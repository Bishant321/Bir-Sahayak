# StudentBank AI Smart Financial Assistant

FGCT6020 — Artificial Intelligence and Creativity

**Stage 1: a trained spending classifier and local visual dashboard.** This separate coursework project takes fictional UK banking transactions in GBP, predicts spending categories with PyTorch, and calculates exact spending summaries with Python. It does not connect to or modify the StudentBank mobile application.

**Stage 2 now has a computer voice prototype.** The dashboard generates offline WAV speech and provides a player and download. Raspberry Pi integration, incoming payment alerts, OLED display and conversational assistance remain future work.

## Run

Developed on Python 3.14.3 / macOS ARM64. Use a platform/Python version supported by the pinned packages; Raspberry Pi installation has not been tested.

`requirements.txt` pins the direct dependencies. `requirements-lock.txt` records their full installed dependency closure for the development environment; use `pip install -r requirements-lock.txt` to reproduce those transitive versions on a compatible platform.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/train.py
python src/predict.py "Tesco weekly groceries"
streamlit run app.py
```

On Windows activate with `.venv\Scripts\activate`. A trained CPU checkpoint is included in `models/`, so you can launch the app or run predictions without retraining. No API key or cloud service is needed. Run `python src/predict.py` without an argument for an interactive description prompt.

```bash
python src/predict.py --csv data/sample_transactions.csv --output /tmp/studentbank_classified.csv
python -m pytest -q
```

## Data contract

`data/sample_transactions.csv` contains **400 fictional outgoing transactions**, 80 per category: groceries, transport, shopping, bills and entertainment. The 50 merchant groups have eight records each. Brand names identify illustrative merchants; the transactions, dates and amounts are generated and have no connection to real accounts or those businesses. This is not a representative student's budget or a validated financial simulator.

| Column | Meaning |
| --- | --- |
| `transaction_id` | Unique text identifier; leading zeroes are preserved. |
| `date` | A valid date in `YYYY-MM-DD` format. |
| `description` | 1–200 characters; the only classifier input. |
| `amount_gbp` | Positive outgoing spending, at most two decimal places and no currency symbol. |
| `currency` | Must be `GBP`. |
| `category` | Reference training label; optional for prediction. Never used as an input feature. |
| `merchant_group` | Training partition group; optional for prediction. Never used as an input feature. |

Uploads are limited to 5 MB and 10,000 rows. Negative amounts, zero amounts, mixed currencies and duplicate transaction IDs are rejected. Income, transfers and refunds need a separately defined data contract in a later stage. Use the provided fictional fixtures for the coursework prototype.

Regenerate the exact sample with `python src/generate_data.py` (seed 42). The sample's descriptions contain category-specific templates and are intentionally easy to interpret. In the overview they include training rows: dashboard sample predictions are not held-out evaluation evidence.

## Actual AI pipeline

1. Validate transactions and map reference labels to the five classes.
2. Assign merchant groups within each class to training, validation and test sets, using a recorded seed. With the default dataset this is **240 / 80 / 80 rows**. Each merchant group stays in one partition. Exact repeated descriptions crossing partitions are rejected.
3. Fit character TF-IDF (3–5 character n-grams, up to 2,000 features) on **training descriptions only**. Category labels, group IDs, amounts, dates and transaction IDs never become features.
4. Train a PyTorch feed-forward network: TF-IDF → 64-unit linear layer → ReLU → dropout → five output logits. Use Adam and cross-entropy loss. CPU execution and random seeds are fixed for reproducibility within the recorded environment.
5. Choose the checkpoint with the best validation macro F1, breaking ties using lower validation loss. Apply early stopping after the configured patience. Test performance is evaluated after selection; test data does not select epochs or vocabulary.
6. Compare the selected network with a majority-class baseline and logistic regression on the same training features and held-out test rows.
7. Save the model state, vocabulary/IDF, parameters, split membership, learning curve, test predictions, per-class metrics and confusion matrices.

`config.yaml` controls splits, feature extraction, training and the review threshold. `python src/train.py --config path/to/config.yaml` supports a separate experiment configuration; relative paths inside it resolve against the project root.

The model's softmax score is **uncalibrated**, not a guarantee of correctness. Scores below 0.60 and descriptions with no recognised features are marked “needs review”. This is a heuristic, not proven unknown-merchant detection. A model can still be confidently wrong. Report accuracy over the entire test set alongside review coverage, rather than hiding errors by dropping flagged records.

## Verified totals and generated insights

Amounts are parsed with `Decimal` and stored as integer pence. Totals and category sums are calculated using these integers; formatted GBP values are not calculated through floating-point arithmetic. Plotting converts pence to GBP for presentation only.

Summary sentences are deterministic templates filled with verified dates, counts and sums. They do not use an LLM and do not provide personalised budgeting, lending or investment recommendations. Category totals remain estimates because their labels come from the classifier. Flagged records remain in the overall total and appear in a separate “needs review” group.

The Streamlit interface provides a spending overview, daily/category charts, single-description predictions, CSV export, baseline comparison, confusion matrix, learning curves and run metadata.

## Computer voice preview

In **Spending overview**, select **Generate spoken summary**, then press play. Pause/seek using the player, and adjust or mute your device volume. Audio never autoplays. Download the WAV or read/download its transcript. Changing the summary clears the old recording.

Speech uses the built-in macOS `say` engine and the selected system voice. On Linux, the adapter supports `espeak-ng` or `espeak` if installed; Linux and Raspberry Pi execution still need testing. Windows has no bundled speech adapter. Missing voices, empty audio and timeouts produce an error while the visual dashboard remains available. No extra Python packages or cloud speech APIs are used. Synthesis runs on the computer hosting Streamlit; playback runs in your browser.

Speech is generated from the same verified integer-pence totals as the dashboard. Amounts are expanded to pounds/pence and dates to month names; category estimates and review counts remain explicit. Transaction descriptions are never passed to the speech engine. Generating a valid audio file does not establish audible delivery or pronunciation quality: those require listening and physical-speaker tests.

## Evidence and limitations

Each training run appends a real row to `experiment_log.csv` and creates `experiments/runs/<run_id>/`. These are included as coursework evidence. `models/` contains the selected run used by the app. Reports record resolved configuration, seeds, dataset checksum, source checksums, package versions, local Git revision/dirty status, split membership and actual outputs. Preserve failed experiments and decisions in `experiments/LOG.md` as development continues.

Held-out merchant groups prevent a merchant from appearing on both sides of the split, but **phrase templates are shared** across partitions. Therefore high scores on these 400 examples do not establish real-bank performance. All five classes are balanced, unlike many real datasets. Stronger follow-up evaluation should include independently authored, less explicit descriptions, ambiguous/multicategory merchants, different class frequencies, per-class failures and score calibration. The simple model's category vocabulary is closed; it cannot reliably identify every unsupported type of transaction.

Training from a fixed seed is intended to be reproducible in the recorded environment, not bit-for-bit identical across different operating systems or package versions. Repeated use of the same test set for tuning turns it into development data; preserve a fresh evaluation set for final claims.

## Project structure

```text
app.py                         Streamlit dashboard
src/train.py                   Training CLI
src/predict.py                 Single-description and CSV prediction CLI
src/generate_data.py           Reproduce the synthetic dataset
src/studentbank/               Validation, model, inference and training modules
data/sample_transactions.csv   400 fictional GBP transactions
config.yaml                    Training and inference settings
models/                        Trained checkpoint and selected-run evidence
experiment_log.csv             Measured run summaries
experiments/runs/               Complete run artifacts
docs/                          Proposal, AI-use disclosure and Stage 2 plan
tests/                         Data, inference, split, metric and interface tests
archive/csv_data_assistant/     Historical CSV assistant; not the active application
```

The old app and its evaluation records are preserved in the workspace archive, which is excluded from the StudentBank starter ZIP. Its test counts and measurements do not describe this StudentBank model. Only `tests/` is collected by the new pytest configuration. The provided documents and one-sentence definition are used as project guidance; hardware is a proposed extension, not a requirement inferred from the workshop PDFs.

The report, original contribution, future usability study and final marking requirements still need the student's own attention. See `docs/AI_USE_DISCLOSURE.md`; no participant or hardware results are fabricated. This implementation does not automatically commit or push files to GitHub.

## Implementation references

- [PyTorch cross-entropy loss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html) for learning from class labels and logits.
- [PyTorch model serialisation](https://docs.pytorch.org/docs/stable/notes/serialization) for state-dictionary checkpoints; prediction loads the local weights with `weights_only=True`.
- [scikit-learn data leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) for fitting preprocessing only on training data.
- [scikit-learn grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation) for the rationale behind keeping related groups apart. The project implements its own per-class group assignment.
