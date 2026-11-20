# Experiment log

## 2026-11-18 — Initial local implementation and baseline

Environment: macOS ARM64, Python 3.14.3. Dependency versions are pinned in `requirements.txt`; generated evaluation reports also capture the relevant package versions and configuration. Synthetic fixtures only. No participant data or live Anthropic requests were used.

### Automated verification

- `python -m pytest -q`: **56 passed** (final run, 4.83 seconds).
- `python -m pip check`: no broken requirements found.
- Local Streamlit server launch: homepage and `/_stcore/health` both returned HTTP 200.
- Coverage includes CSV validation, all fill strategies, atomic failure, duplicates, original preservation, undo, export round-trip, chart aggregation/sampling, SQL restrictions and limits, malformed SQL, mocked model tool calls, API failure after mutation, and the Streamlit sample/inspect/clean/undo/SQL workflow.
- `python -m experiments.evaluate business`: **30/30** reference SQL answers matched fixed expected results. This verifies the SQL pipeline and fixtures, not natural-language understanding.
- `python -m experiments.evaluate imputation`: **60 runs** completed: three missingness rates × five masks × four numeric strategies. Data seed 42; mask seeds 0–4.

### Imputation baseline

Means across the five masks, rounded to four decimal places. Numeric units are those of the synthetic `amount` variable (generated with mean 100 and standard deviation 20). Category accuracy uses mode throughout.

| Missing rate | Numeric strategy | MAE | RMSE | Category accuracy |
| --- | --- | --- | --- | --- |
| 5% | Mean | 14.8349 | 18.6946 | 0.5533 |
| 5% | Median / Auto | 14.9093 | 18.7381 | 0.5533 |
| 5% | Mode | 19.4957 | 23.8580 | 0.5533 |
| 10% | Mean | 16.4755 | 20.3082 | 0.6233 |
| 10% | Median / Auto | 16.5256 | 20.3656 | 0.6233 |
| 10% | Mode | 20.6593 | 25.3835 | 0.6233 |
| 20% | Mean | 15.5784 | 19.8225 | 0.6200 |
| 20% | Median / Auto | 15.6361 | 19.8071 | 0.6200 |
| 20% | Mode | 21.1831 | 25.7815 | 0.6200 |

Auto and median are identical for numeric columns by design. These aggregate results are a synthetic baseline, not a statistical comparison across real datasets. The random masks differ by rate and the small variation in error is not evidence that more missingness improves performance. Inspect per-mask results before drawing conclusions. Follow-up experiments should include multiple real, non-sensitive datasets and non-random missingness.

Reports generated at approximately 22:56 UTC are in `experiments/results/` (ignored by Git to avoid committing routine generated output).

### Outstanding evaluation

- Run the 40-prompt routing evaluation with a funded Anthropic key; inspect argument correctness separately from first-tool accuracy.
- Run the 30-question live business evaluation and manually score explanation faithfulness against tool evidence.
- Exercise the manual adversarial cases, including malicious text in actual CSV headers/cells. Passing SQL rejection tests does not establish model resistance to prompt injection.
- Conduct the 10–15 participant study after consent and any required course approval. No usability or trust scores are claimed yet.

For each subsequent run record date, Git revision, dataset identifier, prompt/system-prompt changes, model, parameters, seeds, metrics and limitations. Keep failed experiments in the log rather than retaining only successful results.
