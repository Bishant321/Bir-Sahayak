import csv
from datetime import datetime, timezone
from io import BytesIO, StringIO
import json
import math

import pandas as pd
import plotly.express as px
from pandas.api.types import is_numeric_dtype, is_bool_dtype

from assistant.config import CONFIG
from assistant.sql import run_sql


class Dataset:
    def __init__(self, raw: bytes, name: str = "dataset.csv"):
        limits = CONFIG["data"]
        if len(raw) > limits["max_upload_bytes"]:
            raise ValueError("CSV files must be 10 MB or smaller.")
        try:
            decoded = raw.decode("utf-8-sig")
            header = next(csv.reader(StringIO(decoded)))
            if not header or any(not c.strip() for c in header):
                raise ValueError("Every CSV column must have a name.")
            if len({c.casefold() for c in header}) != len(header):
                raise ValueError("Column names must be unique, ignoring letter case.")
            if len(header) > limits["max_columns"] or any(len(c) > 200 for c in header):
                raise ValueError("Use at most 100 columns, with names up to 200 characters.")
            # Check row widths: pandas can otherwise silently infer an index.
            reader = csv.reader(StringIO(decoded), strict=True)
            next(reader)
            count = 0
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    raise ValueError("Each CSV row must have the same number of fields as the header.")
                count += 1
                if count > limits["max_rows"]:
                    raise ValueError("Use a dataset with at most 100,000 rows.")
            frame = pd.read_csv(BytesIO(raw), encoding="utf-8-sig")
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError,
                StopIteration, csv.Error) as exc:
            raise ValueError("Upload a valid comma-separated UTF-8 CSV with a header row.") from exc
        if frame.empty:
            raise ValueError("The CSV must contain at least one data row.")
        self.name = name
        self.original_bytes = bytes(raw)
        self._original = frame.copy(deep=True)
        self.frame = frame
        self.history = []
        self._undo = []
        self.version = 0

    @property
    def original(self):
        return self._original.copy(deep=True)

    @property
    def can_undo(self):
        return bool(self._undo)

    def _columns(self, columns):
        if not columns or len(set(columns)) != len(columns):
            raise ValueError("Choose one or more distinct columns.")
        unknown = [column for column in columns if column not in self.frame.columns]
        if unknown:
            raise ValueError(f"Unknown columns: {unknown}. Use the exact names in Dataset preview.")

    def info(self):
        return {"rows": len(self.frame), "columns": len(self.frame.columns),
                "version": self.version, "missing_cells": int(self.frame.isna().sum().sum()),
                "duplicate_rows": int(self.frame.duplicated().sum()),
                "schema": [{"name": c, "dtype": str(self.frame[c].dtype)} for c in self.frame.columns]}

    def find_nulls(self):
        return {"rows": len(self.frame), "total_missing": int(self.frame.isna().sum().sum()),
                "columns": [{"column": c, "missing": int(self.frame[c].isna().sum()),
                             "percent": round(float(self.frame[c].isna().mean() * 100), 2)}
                            for c in self.frame.columns]}

    def find_duplicates(self, columns=None):
        if columns is not None:
            self._columns(columns)
        return {"duplicate_rows": int(self.frame.duplicated(subset=columns).sum()),
                "rows": len(self.frame), "compared_columns": columns or list(self.frame.columns),
                "definition": "Repeated rows after the first occurrence."}

    def _commit(self, new_frame, operation, details):
        before = self.frame
        self._undo.append((before.copy(deep=True), operation))
        self._undo = self._undo[-CONFIG["data"]["undo_steps"]:]
        self.frame = new_frame
        self.version += 1
        self.history.append({"version": self.version, "time": datetime.now(timezone.utc).isoformat(),
                             "operation": operation, "rows_before": len(before),
                             "rows_after": len(new_frame), "details": details})

    def remove_duplicates(self, columns=None):
        summary = self.find_duplicates(columns)
        removed = summary["duplicate_rows"]
        if removed:
            self._commit(self.frame.drop_duplicates(subset=columns).reset_index(drop=True),
                         "remove_duplicates", {"removed_rows": removed, "columns": summary["compared_columns"]})
        return {"removed_rows": removed, "remaining_rows": len(self.frame), "changed": bool(removed)}

    def fill_missing(self, columns, strategy="auto", value=None):
        self._columns(columns)
        if strategy not in {"auto", "mean", "median", "mode", "constant"}:
            raise ValueError("Choose auto, mean, median, mode or constant.")
        updated = self.frame.copy(deep=True)
        details = []
        for column in columns:
            series = updated[column]
            missing = int(series.isna().sum())
            if not missing:
                continue
            numeric = is_numeric_dtype(series) and not is_bool_dtype(series)
            selected = ("median" if numeric else "mode") if strategy == "auto" else strategy
            if selected in {"mean", "median"}:
                if not numeric:
                    raise ValueError(f"{selected} requires a numeric column: {column}.")
                replacement = float(getattr(series, selected)())
                # Fractional means and medians must not be truncated by nullable integer dtypes.
                updated[column] = series = series.astype(float)
            elif selected == "mode":
                modes = series.mode(dropna=True)
                if modes.empty:
                    raise ValueError(f"{column} has no observed values. Choose a constant.")
                replacement = modes.iloc[0]
            else:
                if value is None or isinstance(value, (dict, list)):
                    raise ValueError("Provide a non-null scalar constant.")
                replacement = value
                if numeric:
                    try:
                        replacement = float(value)
                        updated[column] = series = series.astype(float)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"{column} requires a numeric constant.") from exc
                elif is_bool_dtype(series):
                    if not isinstance(value, bool):
                        raise ValueError(f"{column} requires a boolean constant.")
                else:
                    replacement = str(value)
            if pd.isna(replacement) or (isinstance(replacement, float) and not math.isfinite(replacement)):
                raise ValueError(f"Cannot infer a finite value for {column}. Choose a constant.")
            updated[column] = series.fillna(replacement)
            # No cell values are returned to the model for imputation.
            details.append({"column": column, "strategy": selected, "filled_cells": missing})
        if details:
            self._commit(updated, "fill_missing", details)
        return {"filled_cells": sum(d["filled_cells"] for d in details), "columns": details,
                "changed": bool(details)}

    def undo(self):
        if not self._undo:
            raise ValueError("There is no saved change to undo.")
        previous, operation = self._undo.pop()
        rows_before = len(self.frame)
        self.frame = previous
        self.version += 1
        self.history.append({"version": self.version, "time": datetime.now(timezone.utc).isoformat(),
                             "operation": "undo", "rows_before": rows_before,
                             "rows_after": len(previous), "details": {"reversed": operation}})
        return {"reversed": operation, "rows": len(previous), "version": self.version}

    def change_history(self):
        return {"changes": self.history[-20:], "total_changes": len(self.history),
                "undo_steps_available": len(self._undo)}

    def query_sql(self, query):
        return run_sql(self.frame, query)

    def create_chart(self, kind, x, y=None, aggregation="none"):
        self._columns([x] if y is None or x == y else [x, y])
        if kind not in {"bar", "line", "scatter", "histogram"}:
            raise ValueError("Choose bar, line, scatter or histogram.")
        if aggregation not in {"none", "count", "sum", "mean"}:
            raise ValueError("Choose none, count, sum or mean aggregation.")
        if kind == "histogram" and aggregation != "none":
            raise ValueError("Histograms use raw values, without an aggregation.")
        if kind == "histogram":
            y = None
        if aggregation in {"sum", "mean"} and (not y or not is_numeric_dtype(self.frame[y])):
            raise ValueError("Sum and mean charts need a numeric y column.")
        if aggregation == "none" and kind != "histogram" and not y:
            raise ValueError("Choose a y column, or use count aggregation for a bar chart.")
        # A count or histogram depends only on x, even if an unused y was supplied.
        selected = list(dict.fromkeys([x] + ([y] if y and kind != "histogram" and aggregation != "count" else [])))
        frame = self.frame[selected].dropna().copy()
        dropped = len(self.frame) - len(frame)
        if aggregation != "none":
            if frame[x].nunique() > 100:
                raise ValueError("Choose a grouping column with at most 100 unique values.")
            if aggregation == "count":
                output = "row_count"
                while output in frame.columns:
                    output = "_" + output
                frame = frame.groupby(x).size().reset_index(name=output)
                y = output
            else:
                if x == y:
                    raise ValueError("Choose different grouping and measure columns.")
                frame = frame.groupby(x)[y].agg(aggregation).reset_index()
        limit = CONFIG["data"]["chart_rows"]
        sampled = len(frame) > limit
        if sampled:
            frame = frame.sample(limit, random_state=42)
        if frame.empty:
            raise ValueError("No complete values are available for this chart.")
        if kind == "line":
            frame = frame.sort_values(x)
        title = f"{aggregation.title() + ' of ' if aggregation != 'none' else ''}{y + ' by ' if y and kind != 'histogram' else ''}{x}"
        kwargs = {"data_frame": frame, "x": x, "title": title,
                  "color_discrete_sequence": ["#147D73", "#E3A63B"]}
        if kind != "histogram":
            kwargs["y"] = y
        figure = getattr(px, kind)(**kwargs)
        figure.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=60, b=20))
        summary = {"kind": kind, "x": x, "y": y, "aggregation": aggregation,
                   "plotted_rows": len(frame), "sampled": sampled, "excluded_missing_rows": dropped,
                   "note": "Chart rendered locally. No plotted cell values are sent to Claude."}
        return summary, figure

    def export_csv(self):
        return self.frame.to_csv(index=False).encode("utf-8")

    def export_history(self):
        return json.dumps(self.history, indent=2).encode("utf-8")
