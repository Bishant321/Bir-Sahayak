import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import torch
from torch import nn


class SpendingClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, classes, dropout):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(input_size, hidden_size), nn.ReLU(),
                                     nn.Dropout(dropout), nn.Linear(hidden_size, classes))

    def forward(self, features):
        return self.network(features)


def save_vectorizer(vectorizer, path):
    Path(path).write_text(json.dumps({"vocabulary": {k: int(v) for k, v in vectorizer.vocabulary_.items()},
                                    "idf": vectorizer.idf_.tolist(),
                                    "analyzer": vectorizer.analyzer, "ngram_range": list(vectorizer.ngram_range),
                                    "lowercase": vectorizer.lowercase}, indent=2))


def load_vectorizer(path):
    data = json.loads(Path(path).read_text())
    vectorizer = TfidfVectorizer(vocabulary=data["vocabulary"], analyzer=data["analyzer"],
                                ngram_range=tuple(data["ngram_range"]), lowercase=data["lowercase"])
    vectorizer.idf_ = np.asarray(data["idf"])
    return vectorizer


class Predictor:
    def __init__(self, directory):
        directory = Path(directory)
        self.metadata = json.loads((directory / "metadata.json").read_text())
        self.vectorizer = load_vectorizer(directory / "features.json")
        architecture = self.metadata["architecture"]
        self.model = SpendingClassifier(**architecture)
        self.model.load_state_dict(torch.load(directory / "model.pt", map_location="cpu", weights_only=True))
        self.model.eval()
        self.categories = self.metadata["categories"]
        self.threshold = self.metadata["config"]["inference"]["review_threshold"]

    def predict(self, descriptions):
        descriptions = list(descriptions)
        if not descriptions or any(not isinstance(d, str) or not d.strip() or len(d) > 200 for d in descriptions):
            raise ValueError("Provide descriptions containing 1–200 characters.")
        # Bound dense memory even when processing a large uploaded CSV.
        results = []
        for start in range(0, len(descriptions), 128):
            batch = descriptions[start:start + 128]
            sparse = self.vectorizer.transform(batch)
            with torch.inference_mode():
                probabilities = torch.softmax(self.model(torch.tensor(sparse.toarray(), dtype=torch.float32)), dim=1).numpy()
            for i, scores in enumerate(probabilities):
                best = int(scores.argmax())
                confidence = float(scores[best])
                unknown = sparse[i].nnz == 0
                review = unknown or confidence < self.threshold
                results.append({"predicted_category": self.categories[best], "model_score": confidence,
                                "needs_review": review, "display_category": "needs review" if review else self.categories[best],
                                "review_reason": "No recognised text features" if unknown else "Low model score" if review else "",
                                "scores": {label: float(score) for label, score in zip(self.categories, scores)}})
        return results

    def classify(self, transactions):
        import pandas as pd
        # Labels, merchant groups, dates and amounts are never model inputs.
        predictions = pd.DataFrame(self.predict(transactions["description"]))
        # A re-uploaded export must replace old predictions, not create duplicate columns.
        frame = transactions.drop(columns=list(predictions.columns), errors="ignore").reset_index(drop=True).copy()
        return pd.concat([frame, predictions.drop(columns="scores")], axis=1)
