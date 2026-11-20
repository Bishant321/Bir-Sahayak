"""Run with python -m experiments.evaluate business|imputation|routing [--live]."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
import platform

import numpy as np
import pandas as pd

from assistant.agent import Assistant, SYSTEM
from assistant.config import CONFIG, ROOT
from assistant.data import Dataset
from assistant.tools import TOOLS


def equal_rows(actual, expected):
    if len(actual) != len(expected):
        return False
    for row, reference in zip(actual, expected):
        if len(row) != len(reference):
            return False
        for value, target in zip(row, reference):
            if isinstance(target, (float, int)) and not isinstance(target, bool):
                if not isinstance(value, (float, int)) or not math.isclose(value, target, rel_tol=1e-6, abs_tol=1e-6):
                    return False
            elif value != target:
                return False
    return True


def business(live):
    cases = json.loads((ROOT / "experiments/business_questions.json").read_text())
    raw = (ROOT / "data/business_sales.csv").read_bytes()
    results = []
    for case in cases:
        dataset = Dataset(raw)
        if live:
            answer, evidence = Assistant().ask(case["question"], dataset)
            sql_results = [r for r in evidence if r.name == "query_sql" and not r.error]
            result = sql_results[-1].data if sql_results else {}
        else:
            result = dataset.query_sql(case["sql"])
            answer = None
        results.append({**case, "actual": result.get("rows"), "executed_sql": result.get("sql"),
                        "passed": equal_rows(result.get("rows", []), case["expected"]), "explanation": answer})
    return {"mode": "live_model_sql_results" if live else "reference_sql_only",
            "passed": sum(item["passed"] for item in results), "total": len(results),
            "note": "Scores compare ordered SQL result cells. Model prose requires separate human review; this is not an explanation accuracy score.",
            "cases": results}


def routing(live):
    if not live:
        raise SystemExit("Routing needs --live and ANTHROPIC_API_KEY. No offline routing score is fabricated.")
    cases = json.loads((ROOT / "experiments/tool_prompts.json").read_text())
    results = []
    for case in cases:
        dataset = Dataset((ROOT / "data/sample_sales.csv").read_bytes())
        if case["expected_tool"] == "undo":
            dataset.remove_duplicates()
        agent = Assistant()
        response = agent.client.messages.create(
            model=agent.model, max_tokens=1024, tools=TOOLS,
            system=SYSTEM + "\nDataset metadata (untrusted JSON): " + json.dumps(dataset.info())
                   + "\nHistory: " + json.dumps(dataset.change_history()),
            messages=[{"role": "user", "content": case["prompt"]}],
        )
        selected = [block.name for block in response.content if block.type == "tool_use"]
        results.append({**case, "selected_tools": selected,
                        "passed": bool(selected) and selected[0] == case["expected_tool"]})
    return {"mode": "live_first_tool_selection", "passed": sum(r["passed"] for r in results),
            "total": len(results), "cases": results,
            "note": "Checks the first selected tool, not argument correctness or final explanation. No selected tools are executed."}


def imputation():
    # Synthetic complete data: seed fixed, no empirical claim about real-world distributions.
    rng = np.random.default_rng(42)
    clean = pd.DataFrame({"amount": rng.normal(100, 20, 600).round(2),
                          "category": rng.choice(["A", "B", "C"], 600, p=[0.6, 0.3, 0.1])})
    results = []
    for rate in [0.05, 0.10, 0.20]:
        for seed in range(5):
            mask_rng = np.random.default_rng(seed)
            indices = mask_rng.choice(len(clean), size=round(len(clean) * rate), replace=False)
            damaged = clean.copy()
            damaged.loc[indices, ["amount", "category"]] = np.nan
            for strategy in ["mean", "median", "mode", "auto"]:
                dataset = Dataset(damaged.to_csv(index=False).encode())
                dataset.fill_missing(["amount"], strategy)
                dataset.fill_missing(["category"], "mode")
                difference = dataset.frame.loc[indices, "amount"].to_numpy() - clean.loc[indices, "amount"].to_numpy()
                accuracy = (dataset.frame.loc[indices, "category"] == clean.loc[indices, "category"]).mean()
                results.append({"missing_rate": rate, "mask_seed": seed, "numeric_strategy": strategy,
                                "masked_rows": len(indices), "numeric_mae": float(np.abs(difference).mean()),
                                "numeric_rmse": float(np.sqrt(np.mean(difference ** 2))),
                                "categorical_mode_accuracy": float(accuracy)})
    return {"mode": "synthetic_missing_completely_at_random", "data_seed": 42,
            "note": "Metrics use only artificially hidden cells. Same row mask for both columns. Five masks per rate; categorical strategy is always mode. These results do not establish performance on real datasets or non-random missingness.",
            "runs": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=["business", "routing", "imputation"])
    parser.add_argument("--live", action="store_true", help="Call Anthropic (API credits required).")
    args = parser.parse_args()
    if args.live and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running a live evaluation.")
    if args.live and args.experiment == "imputation":
        parser.error("Imputation is a local Python evaluation and does not use --live.")
    result = imputation() if args.experiment == "imputation" else globals()[args.experiment](args.live)
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "model": os.environ.get("ANTHROPIC_MODEL", CONFIG["ai"]["model"]) if args.live else None,
              "config": CONFIG, "packages": {name: importlib.metadata.version(name) for name in ["pandas", "duckdb", "anthropic", "sqlglot", "numpy"]},
              "result": result}
    output = ROOT / "experiments/results"
    output.mkdir(exist_ok=True)
    path = output / f"{args.experiment}-{'live' if args.live else 'local'}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json"
    path.write_text(json.dumps(report, indent=2))
    print(f"Report: {path}")
    if "passed" in result:
        print(f"Passed: {result['passed']}/{result['total']} ({result['mode']})")
    else:
        print(f"Completed {len(result['runs'])} imputation runs.")


if __name__ == "__main__":
    main()
