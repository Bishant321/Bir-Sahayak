import copy
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import subprocess
import time

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from studentbank.model import SpendingClassifier, save_vectorizer
from studentbank.settings import CATEGORIES, ROOT, read_config
from studentbank.transactions import load_transactions


def grouped_split(frame, config):
    """Stratify merchant groups within each class; never split an individual group."""
    if not {"category", "merchant_group"}.issubset(frame.columns):
        raise ValueError("Training needs category and merchant_group columns.")
    if set(frame["category"]) != set(CATEGORIES):
        raise ValueError("Training data must include exactly the five configured spending categories.")
    if frame["merchant_group"].str.strip().eq("").any():
        raise ValueError("Every training row needs a merchant_group.")
    if frame.groupby("merchant_group")["category"].nunique().max() != 1:
        raise ValueError("Each merchant group must have one reference category in this teaching dataset.")
    test = float(config["test_fraction"])
    validation = float(config["validation_fraction"])
    if not 0 < test < 1 or not 0 < validation < 1 or test + validation >= 1:
        raise ValueError("Test and validation fractions must be positive and sum to less than one.")
    rng = np.random.default_rng(config["seed"])
    assignments = {}
    for category in CATEGORIES:
        groups = np.array(sorted(frame.loc[frame.category == category, "merchant_group"].unique()))
        if len(groups) < 5:
            raise ValueError("Each category needs at least five distinct merchant groups.")
        rng.shuffle(groups)
        n_test, n_val = max(1, round(len(groups) * test)), max(1, round(len(groups) * validation))
        if n_test + n_val >= len(groups):
            raise ValueError("Not enough merchant groups left for training.")
        for i, group in enumerate(groups):
            assignments[group] = "test" if i < n_test else "validation" if i < n_test + n_val else "train"
    split = frame["merchant_group"].map(assignments)
    description_partitions = pd.DataFrame({"description": frame.description.str.lower().str.strip(), "split": split})
    if description_partitions.groupby("description")["split"].nunique().max() > 1:
        raise ValueError("Identical descriptions occur across partitions; correct the grouping before training.")
    return {name: np.flatnonzero(split.to_numpy() == name) for name in ["train", "validation", "test"]}


def evaluate_predictions(expected, predicted):
    labels = list(range(len(CATEGORIES)))
    report = classification_report(expected, predicted, labels=labels, target_names=CATEGORIES,
                                   output_dict=True, zero_division=0)
    return {"accuracy": float(accuracy_score(expected, predicted)),
            "precision_macro": report["macro avg"]["precision"],
            "recall_macro": report["macro avg"]["recall"],
            "f1_macro": report["macro avg"]["f1-score"],
            "classification_report": report,
            "confusion_matrix": confusion_matrix(expected, predicted, labels=labels).tolist(),
            "category_order": CATEGORIES, "support": len(expected)}


def git_state():
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
        return {"revision": revision, "working_tree_has_uncommitted_files": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "working_tree_has_uncommitted_files": None}


def train(config_path=None):
    started = time.perf_counter()
    config = read_config(config_path)
    seed = config["training"]["seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    raw = (ROOT / config["data"]["path"]).read_bytes()
    frame = load_transactions(raw)
    partitions = grouped_split(frame, config["data"])
    feature_config = dict(config["features"])
    feature_config["ngram_range"] = tuple(feature_config["ngram_range"])
    vectorizer = TfidfVectorizer(**feature_config)
    # Fit vocabulary/IDF ONLY on training rows. Hold-out descriptions never affect it.
    train_features = vectorizer.fit_transform(frame.iloc[partitions["train"]].description)
    arrays = {"train": train_features.toarray().astype(np.float32)}
    for name in ["validation", "test"]:
        arrays[name] = vectorizer.transform(frame.iloc[partitions[name]].description).toarray().astype(np.float32)
    labels = {name: np.array([CATEGORIES.index(c) for c in frame.iloc[indices].category], dtype=np.int64)
              for name, indices in partitions.items()}
    tensors = {name: torch.from_numpy(values) for name, values in arrays.items()}
    targets = {name: torch.from_numpy(values) for name, values in labels.items()}
    settings = config["training"]
    architecture = {"input_size": arrays["train"].shape[1], "hidden_size": settings["hidden_size"],
                    "classes": len(CATEGORIES), "dropout": settings["dropout"]}
    model = SpendingClassifier(**architecture)
    optimizer = torch.optim.Adam(model.parameters(), lr=settings["learning_rate"])
    criterion = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(tensors["train"], targets["train"]),
                        batch_size=settings["batch_size"], shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    best_score, best_loss, stale, best_epoch, best_state = -1, float("inf"), 0, 0, None
    history = []
    for epoch in range(1, settings["epochs"] + 1):
        model.train()
        training_loss = 0.0
        for features, target in loader:
            optimizer.zero_grad()
            loss = criterion(model(features), target)
            loss.backward()
            optimizer.step()
            training_loss += loss.item() * len(features)
        model.eval()
        with torch.inference_mode():
            logits = model(tensors["validation"])
            validation_loss = float(criterion(logits, targets["validation"]).item())
            metrics = evaluate_predictions(labels["validation"], logits.argmax(dim=1).numpy())
        score = metrics["f1_macro"]
        history.append({"epoch": epoch, "train_loss": training_loss / len(labels["train"]),
                        "validation_loss": validation_loss, "validation_f1_macro": score})
        if score > best_score or (abs(score - best_score) < 1e-12 and validation_loss < best_loss):
            best_score, best_loss, best_epoch, stale = score, validation_loss, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            stale += 1
        if stale >= settings["patience"]:
            break
    model.load_state_dict(best_state)
    model.eval()
    # Test labels are used only here, after checkpoint selection on validation.
    with torch.inference_mode():
        test_scores = torch.softmax(model(tensors["test"]), dim=1).numpy()
    neural_predictions = test_scores.argmax(axis=1)
    majority = DummyClassifier(strategy="most_frequent").fit(arrays["train"], labels["train"])
    linear = LogisticRegression(max_iter=1000, random_state=seed).fit(arrays["train"], labels["train"])
    results = {"majority": evaluate_predictions(labels["test"], majority.predict(arrays["test"])),
               "logistic_regression": evaluate_predictions(labels["test"], linear.predict(arrays["test"])),
               "pytorch_mlp": evaluate_predictions(labels["test"], neural_predictions)}
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S%fZ") + f"-seed{seed}"
    directory = ROOT / config["paths"]["model_directory"]
    run_directory = ROOT / config["paths"]["experiment_directory"] / run_id
    directory.mkdir(parents=True, exist_ok=True)
    run_directory.mkdir(parents=True, exist_ok=False)
    threshold = config["inference"]["review_threshold"]
    covered = (test_scores.max(axis=1) >= threshold) & (np.count_nonzero(arrays["test"], axis=1) > 0)
    review = {"threshold": threshold, "coverage": float(covered.mean()),
              "flagged_count": int((~covered).sum()),
              "accuracy_on_unflagged": float((neural_predictions[covered] == labels["test"][covered]).mean()) if covered.any() else None,
              "note": "Softmax scores are uncalibrated. Threshold is a review heuristic, not an out-of-distribution guarantee."}
    metadata = {"run_id": run_id, "timestamp_utc": now.isoformat(), "config": config,
                "categories": CATEGORIES, "architecture": architecture, "chosen_epoch": best_epoch,
                "epochs_completed": len(history), "best_validation_f1_macro": best_score,
                "dataset_sha256": hashlib.sha256(raw).hexdigest(),
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT / "src").rglob("*.py"))},
                "git": git_state(), "python": platform.python_version(), "device": "cpu",
                "packages": {p: importlib.metadata.version(p) for p in ["torch", "scikit-learn", "numpy", "pandas", "PyYAML"]},
                "partition_sizes": {name: len(indices) for name, indices in partitions.items()},
                "split_policy": "Stratified merchant-group holdout; group-disjoint train/validation/test; preprocessing fitted on train only.",
                "feature_policy": "Description-only character TF-IDF; reference category and merchant_group are never features.",
                "limitations": "400 synthetic examples generated from category-specific phrase templates. Merchants are held out, but phrase templates are shared. Scores do not establish real-bank accuracy. No real transactions, live bank integration, speech or physical gadget tested.",
                "duration_seconds": round(time.perf_counter() - started, 3)}
    payload = {"run_id": run_id, "test_results": results, "review_policy": review}
    for target in [directory, run_directory]:
        torch.save(best_state, target / "model.pt")
        save_vectorizer(vectorizer, target / "features.json")
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2))
        (target / "metrics.json").write_text(json.dumps(payload, indent=2))
        pd.DataFrame(history).to_csv(target / "learning_curve.csv", index=False)
    split_records = []
    for name, indices in partitions.items():
        for i in indices:
            row = frame.iloc[i]
            split_records.append({"transaction_id": row.transaction_id, "merchant_group": row.merchant_group,
                                  "reference_category": row.category, "partition": name})
    pd.DataFrame(split_records).to_csv(run_directory / "split_manifest.csv", index=False)
    held_out = frame.iloc[partitions["test"]][["transaction_id", "description", "category"]].copy()
    held_out["predicted_category"] = [CATEGORIES[i] for i in neural_predictions]
    held_out["model_score"] = test_scores.max(axis=1)
    held_out["needs_review"] = ~covered
    held_out.to_csv(run_directory / "test_predictions.csv", index=False)
    log_row = {"run_id": run_id, "timestamp_utc": metadata["timestamp_utc"], "seed": seed,
               "dataset_sha256": metadata["dataset_sha256"], "train_rows": len(partitions["train"]),
               "validation_rows": len(partitions["validation"]), "test_rows": len(partitions["test"]),
               "majority_accuracy": results["majority"]["accuracy"],
               "logistic_accuracy": results["logistic_regression"]["accuracy"],
               **{key: results["pytorch_mlp"][key] for key in ["accuracy", "precision_macro", "recall_macro", "f1_macro"]},
               "chosen_epoch": best_epoch, "duration_seconds": metadata["duration_seconds"],
               "config_json": json.dumps(config, sort_keys=True),
               "notes": "Synthetic baseline; shared phrase templates limit generalisation claims."}
    log_path = ROOT / "experiment_log.csv"
    exists = log_path.exists() and log_path.stat().st_size > 0
    with log_path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(log_row))
        if not exists:
            writer.writeheader()
        writer.writerow(log_row)
    return {"metadata": metadata, **payload, "run_directory": str(run_directory)}
