from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = ["groceries", "transport", "shopping", "bills", "entertainment"]


def read_config(path=None):
    with Path(path or ROOT / "config.yaml").open() as handle:
        config = yaml.safe_load(handle)
    training = config["training"]
    if training["epochs"] < 1 or training["batch_size"] < 1 or training["patience"] < 1:
        raise ValueError("Epochs, batch size and patience must be positive.")
    if not 0 < config["inference"]["review_threshold"] <= 1:
        raise ValueError("Review threshold must be between zero and one.")
    return config
