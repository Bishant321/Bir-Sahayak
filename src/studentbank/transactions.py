"""CSV validation and exact monetary calculations; no model or network access."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
import re

import pandas as pd

REQUIRED = {"transaction_id", "date", "description", "amount_gbp", "currency"}


def parse_pence(value):
    text = str(value).strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", text):
        raise ValueError("Amounts must be positive GBP spending with at most two decimal places.")
    try:
        amount = Decimal(text)
        if not amount.is_finite() or not Decimal("0") < amount <= Decimal("1000000"):
            raise ValueError("Amounts must be greater than £0 and at most £1,000,000.")
        return int(amount * 100)
    except InvalidOperation as exc:
        raise ValueError("Invalid GBP amount.") from exc


def pounds(pence):
    return f"£{int(pence) // 100:,}.{int(pence) % 100:02d}"


def load_transactions(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("Use a CSV of at most 5 MB.")
    try:
        reader = csv.DictReader(StringIO(raw.decode("utf-8-sig")), strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not REQUIRED.issubset(headers):
            raise ValueError("Use unique column names including: " + ", ".join(sorted(REQUIRED)))
        rows = []
        identifiers = set()
        for number, row in enumerate(reader, start=2):
            if len(rows) >= 10000:
                raise ValueError("Use at most 10,000 transactions.")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {number} has the wrong number of fields.")
            identifier = row["transaction_id"].strip()
            description = row["description"].strip()
            if not identifier or identifier in identifiers or len(identifier) > 100:
                raise ValueError(f"Row {number}: transaction_id must be nonempty, unique and at most 100 characters.")
            if not description or len(description) > 200:
                raise ValueError(f"Row {number}: description must contain 1–200 characters.")
            if row["currency"].strip() != "GBP":
                raise ValueError(f"Row {number}: only GBP is supported.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"].strip()):
                raise ValueError(f"Row {number}: use YYYY-MM-DD dates.")
            try:
                date.fromisoformat(row["date"].strip())
            except ValueError as exc:
                raise ValueError(f"Row {number}: invalid calendar date.") from exc
            identifiers.add(identifier)
            rows.append({**row, "transaction_id": identifier, "description": description,
                         "date": row["date"].strip(), "currency": "GBP",
                         "amount_pence": parse_pence(row["amount_gbp"])})
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("Upload a valid UTF-8, comma-separated CSV with a header.") from exc
    if not rows:
        raise ValueError("The CSV must contain at least one transaction.")
    return pd.DataFrame(rows)


def summarise(classified):
    total = sum(int(value) for value in classified["amount_pence"])
    by_category = {str(key): int(value) for key, value in
                   classified.groupby("display_category")["amount_pence"].sum().items()}
    review_count = int(classified["needs_review"].sum())
    start, end = classified["date"].min(), classified["date"].max()
    summary = (f"Your fictional transaction file contains {len(classified)} outgoing payments "
               f"from {start} to {end}, totalling {pounds(total)}.")
    known = {key: value for key, value in by_category.items() if key != "needs review"}
    if known:
        largest = max(known, key=known.get)
        summary += f" The largest predicted spending category is {largest}, at {pounds(known[largest])}."
    if review_count:
        summary += f" {review_count} transactions need a category review."
    summary += " Categories are model estimates; totals are calculated from the CSV."
    return {"total_pence": total, "transaction_count": len(classified), "by_category_pence": by_category,
            "needs_review": review_count, "start_date": start, "end_date": end,
            "announcement_text": summary}
