# StudentBank experiment log

## 18 November 2026 — Stage 1 baseline

**Question:** How does a small PyTorch network compare with a majority baseline and logistic regression on synthetic spending descriptions from held-out merchant groups?

**Run:** `20261118T232717430400Z-seed42`.

**Data:** 400 fictional GBP outgoing transactions, 80 per class, 50 merchant groups. Group-disjoint partitions contain 240 training, 80 validation and 80 test rows. Character TF-IDF vocabulary and inverse-document frequencies were fitted only on training descriptions. Reference categories and grouping identifiers are not model features.

**Configuration:** seed 42, character n-grams 3–5, up to 2,000 features, hidden size 64, dropout 0.15, Adam learning rate 0.003, batch size 32, maximum 40 epochs, patience 8. CPU. The best validation checkpoint was epoch 40. Training/assessment duration recorded by the runner was 2.918 seconds, excluding module import time. Full configuration and package versions are saved with the run.

| Model | Test accuracy | Macro precision | Macro recall | Macro F1 |
| --- | --- | --- | --- | --- |
| Majority class | 0.200 | 0.040 | 0.200 | 0.0667 |
| Logistic regression | 1.000 | 1.000 | 1.000 | 1.000 |
| PyTorch MLP | 1.000 | 1.000 | 1.000 | 1.000 |

**Interpretation:** both learned models correctly classified the 80 synthetic held-out rows. There is no measured accuracy advantage for the neural network over logistic regression. Merchant identities are held out, but category-specific description templates are shared across splits. This is an easy, balanced teaching fixture; the result does not establish real-world banking performance or calibrated confidence. The small sample also limits conclusions about error rates.

**Review threshold:** at 0.60, all 80 held-out rows were unflagged. That is coverage on this fixture, not evidence that unsupported transactions can be detected reliably. Scores are uncalibrated softmax outputs.

**Decision:** retain the trained network as the requested Stage 1 prototype and retain logistic regression as the stronger baseline comparison. Do not claim superiority. Next, evaluate independently authored abbreviated/ambiguous descriptions and unsupported transaction types without tuning against the final test set. Consider a new held-out dataset before additional model selection.

**Stored evidence:** `runs/20261118T232717430400Z-seed42/` contains the checkpoint, feature vocabulary/IDF, metrics, per-class reports, confusion matrices, split manifest, held-out predictions, loss history and provenance. `../experiment_log.csv` has the machine-readable summary. `../models/` contains the selected run used by the app.

**Git limitation:** Git reported that a local packfile was too short and HEAD could not be read during provenance capture. The runner recorded unavailable Git fields rather than inventing a revision. Source-file and dataset SHA-256 hashes were saved and checked successfully. This work did not repair, commit or push the repository; Git metadata needs attention before using it as submission evidence.

## Software verification

- `python -m pytest -q`: **30 passed in 9.59 seconds**. These are the new StudentBank tests, not the archived assistant's tests.
- Covered exact integer-pence sums, invalid amounts/currencies/dates, duplicate IDs, reproducible synthetic generation, group-disjoint stratified splits, feature round-trip, label exclusion from inference, checkpoint predictions, unknown-text review, export/re-import, stored metric consistency and Streamlit interaction.
- `python src/predict.py "Tesco weekly groceries"`: predicted **groceries**, model score approximately **99.8%**. This is a smoke test, not an independent evaluation example.
- Batch prediction of the sample processed 400 rows and calculated **£22,082.25** total outgoing spending. Category totals sum to that same value. This artificial aggregate does not describe a typical student's spending.
- Saved source hashes matched the source files after training.

The model training was actually executed. No live bank connection, Raspberry Pi, speaker playback or participant testing was performed. Those claims remain outside Stage 1.

## Exploratory descriptions after training

Seven hand-authored probes are saved in `exploratory_predictions.json`. These were run after the baseline, with no subsequent parameter tuning; they are exploratory observations, not a new representative benchmark.

- `TESCO EXPRESS 0831` was incorrectly suggested as **transport** with a score of approximately **97.8%**, without a review flag. This is a concrete example of a confidently wrong result on a more abbreviated description despite perfect performance on the templated held-out fixture.
- `TFL TRAVEL CH`, `Monthly broadband direct debit`, `Online cinema booking` and `Clothes and stationery` received their expected supported categories.
- `CASHPOINT WITHDRAWAL` and `Student loan received` were flagged for review. These are unsupported transaction types, so their forced five-class suggestions are not valid categories to accept. Two flagged examples do not validate general unknown-type detection.

**Decision:** do not hide this failure by adding a merchant-specific rule or tuning against these probes. Improve the dataset and evaluate on a new frozen set of independently authored descriptions. Treat the 0.60 threshold as a heuristic and preserve user review in the interface. This finding limits claims about deployment and should appear in the critical reflection.

## 20 November 2026 — computer voice prototype

Added deterministic speech text from verified integer-pence summary fields, explicit pounds/pence and month names, offline macOS synthesis, a Linux eSpeak adapter, browser playback without autoplay, WAV download and transcript. Changed summaries discard earlier audio. The system handles missing engines, timeouts and empty/invalid WAV files.

`python -m pytest -q`: **41 passed in 25.73 seconds**, including speech formatting, review information, missing engines, timeout handling, temporary-file cleanup, audio generation UI and stale-audio removal. UI tests mock synthesis; the independent macOS engine smoke test generated a real PCM WAV with 58,226 frames at 22,050 Hz (120,548 bytes).

The first synthesis attempt inside the execution sandbox returned an empty WAV; validation rejected it. Running with access to the macOS speech service succeeded. No audio was automatically played. File validation is not a listening test: pronunciation, audible speaker delivery, Linux/Raspberry Pi integration and user comprehension remain unmeasured. Stage 1 model weights and benchmark results were not changed.

The full 400-transaction summary also generated successfully: 504,312 PCM frames at 22,050 Hz, approximately 22.87 seconds, stating £22,082.25 outgoing and £7,370.85 in the largest predicted category (bills). See `voice_verification.json` for the transcript and measured audio properties, and `../dist/studentbank_summary.wav` for the local preview.

## 20 November 2026 — full pipeline rerun

At the user's request, reran training with unchanged configuration: `20261120T170006911961Z-seed42`, using 240/80/80 training/validation/test rows. Majority accuracy remained 0.20; logistic regression and PyTorch accuracy and macro F1 remained 1.00 on the synthetic benchmark. This is a reproducibility check, not new independent evaluation evidence.

After retraining, all **41 tests passed in 5.25 seconds**. The single-description CLI predicted groceries for “Tesco weekly groceries” (99.8% uncalibrated score). The batch CLI processed 400 transactions and exported `dist/studentbank_classified.csv`, with exact total £22,082.25. The local dashboard's page and health endpoint both returned HTTP 200 on port 8502, and the dashboard was opened in the default browser.

Offline speech generation also completed: the updated `dist/studentbank_summary.wav` contains 504,430 frames at 22,050 Hz (22.88 seconds). `voice_verification.json` now identifies the new model run. No audible delivery or Raspberry Pi test was claimed. The starter ZIP was refreshed with the new run and current source.
