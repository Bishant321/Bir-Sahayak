import argparse
import json
from pathlib import Path

from studentbank.model import Predictor
from studentbank.settings import ROOT
from studentbank.transactions import load_transactions, summarise


def main():
    parser = argparse.ArgumentParser(description="Classify fictional StudentBank transactions locally.")
    parser.add_argument("description", nargs="?")
    parser.add_argument("--csv", type=Path, help="Classify a fictional transaction CSV.")
    parser.add_argument("--output", type=Path, help="Save the classified CSV.")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    try:
        predictor = Predictor(args.model_dir)
        if args.csv:
            frame = predictor.classify(load_transactions(args.csv.read_bytes()))
            print(json.dumps(summarise(frame), indent=2))
            if args.output:
                if args.output.resolve() == args.csv.resolve():
                    parser.error("Choose an output path different from the input CSV.")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                frame.to_csv(args.output, index=False)
        else:
            description = args.description or input("Transaction description: ")
            result = predictor.predict([description])[0]
            print(f"Suggested category: {result['predicted_category']}")
            print(f"Model score: {result['model_score']:.1%} (uncalibrated; not a guarantee)")
            print("Status: " + ("Needs review — " + result["review_reason"] if result["needs_review"] else "Model suggestion"))
    except FileNotFoundError:
        parser.exit(1, "Model or CSV not found. Train first with: python src/train.py\n")
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
