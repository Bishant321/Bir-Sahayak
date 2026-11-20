import argparse
from pathlib import Path

from studentbank.training import train


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate the StudentBank PyTorch spending classifier.")
    parser.add_argument("--config", type=Path, help="YAML configuration; paths inside are relative to the project root.")
    args = parser.parse_args()
    result = train(args.config)
    print(f"Run: {result['run_id']}")
    print(f"Partitions: {result['metadata']['partition_sizes']}")
    for name, metrics in result["test_results"].items():
        print(f"{name}: accuracy={metrics['accuracy']:.3f}, precision={metrics['precision_macro']:.3f}, recall={metrics['recall_macro']:.3f}, macro F1={metrics['f1_macro']:.3f}")
    print(f"Evidence saved to: {result['run_directory']}")
    print("Synthetic data only. These scores do not establish accuracy on real banking transactions.")


if __name__ == "__main__":
    main()
