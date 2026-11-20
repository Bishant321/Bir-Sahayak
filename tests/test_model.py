import json

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from studentbank.model import Predictor, save_vectorizer, load_vectorizer
from studentbank.settings import ROOT, CATEGORIES, read_config
from studentbank.synthetic import generate
from studentbank.training import grouped_split, evaluate_predictions
from studentbank.transactions import load_transactions


def test_synthetic_data_reproducible_and_balanced(tmp_path):
    one = generate(tmp_path / "one.csv")
    two = generate(tmp_path / "two.csv")
    assert one.read_bytes() == two.read_bytes()
    data = load_transactions(one.read_bytes())
    assert len(data) == 400 and set(data.currency) == {"GBP"}
    assert data.category.value_counts().to_dict() == {name: 80 for name in CATEGORIES}


def test_split_is_disjoint_stratified_and_reproducible():
    data = load_transactions((ROOT / "data/sample_transactions.csv").read_bytes())
    partitions = grouped_split(data, read_config()["data"])
    repeated = grouped_split(data, read_config()["data"])
    assert {name: len(idx) for name, idx in partitions.items()} == {"train": 240, "validation": 80, "test": 80}
    groups = {name: set(data.iloc[idx].merchant_group) for name, idx in partitions.items()}
    assert not (groups["train"] & groups["test"] or groups["train"] & groups["validation"] or groups["test"] & groups["validation"])
    for name, idx in partitions.items():
        assert np.array_equal(idx, repeated[name])
        assert set(data.iloc[idx].category) == set(CATEGORIES)


def test_vectorizer_roundtrip_and_no_test_fit(tmp_path):
    vectorizer = TfidfVectorizer().fit(["apple banana", "bus ticket"])
    path = tmp_path / "features.json"
    save_vectorizer(vectorizer, path)
    loaded = load_vectorizer(path)
    np.testing.assert_allclose(loaded.transform(["banana ticket"]).toarray(), vectorizer.transform(["banana ticket"]).toarray())
    assert loaded.transform(["heldoutword"]).nnz == 0


def test_reference_labels_are_not_inference_inputs():
    predictor = Predictor(ROOT / "models")
    frame = load_transactions((ROOT / "data/sample_transactions.csv").read_bytes()).head(5)
    before = predictor.classify(frame)
    frame["category"] = "deliberately_wrong"
    frame["merchant_group"] = "changed"
    after = predictor.classify(frame)
    assert before.predicted_category.tolist() == after.predicted_category.tolist()
    np.testing.assert_array_equal(before.model_score, after.model_score)


def test_saved_model_predicts_and_flags_unknown():
    predictor = Predictor(ROOT / "models")
    results = predictor.predict(["Tesco weekly groceries", "TfL bus ticket", "Odeon cinema tickets", "zzzzzzzzzz"])
    assert [r["predicted_category"] for r in results[:3]] == ["groceries", "transport", "entertainment"]
    assert results[3]["needs_review"]
    assert all(abs(sum(r["scores"].values()) - 1) < 1e-6 for r in results)
    with pytest.raises(ValueError):
        predictor.predict([""])


def test_classified_export_can_be_reloaded():
    predictor = Predictor(ROOT / "models")
    source = load_transactions((ROOT / "data/sample_transactions.csv").read_bytes()).head(4)
    first = predictor.classify(source)
    reloaded = load_transactions(first.to_csv(index=False).encode())
    second = predictor.classify(reloaded)
    assert second.columns.is_unique
    assert first.predicted_category.tolist() == second.predicted_category.tolist()


def test_metrics_include_all_classes_and_known_majority_baseline():
    truth = np.repeat(np.arange(5), 16)
    metrics = evaluate_predictions(truth, np.zeros(80, dtype=int))
    assert metrics["accuracy"] == pytest.approx(0.2)
    assert metrics["f1_macro"] == pytest.approx(1 / 15)
    assert len(metrics["confusion_matrix"]) == 5


def test_saved_metrics_match_heldout_predictions():
    import pandas as pd
    predictor = Predictor(ROOT / "models")
    run = ROOT / "experiments/runs" / predictor.metadata["run_id"]
    heldout = pd.read_csv(run / "test_predictions.csv")
    calculated = evaluate_predictions([CATEGORIES.index(c) for c in heldout.category],
                                       [CATEGORIES.index(c) for c in heldout.predicted_category])
    saved = json.loads((ROOT / "models/metrics.json").read_text())["test_results"]["pytorch_mlp"]
    assert calculated == saved
    reproduced = predictor.predict(heldout.description)
    assert [p["predicted_category"] for p in reproduced] == heldout.predicted_category.tolist()
