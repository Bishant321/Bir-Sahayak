# Bir Sahayak · AI Data Engineering Assistant

FGCT6020 – Artificial Intelligence and Creativity

A Streamlit application for inspecting, cleaning and querying CSV datasets. Claude selects declared tools; pandas and DuckDB calculate the results. The interface exposes the actual tool results, SQL and change history alongside the model's explanation.

## Run locally

Use Python 3.14 (the development environment). From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`. Select **Try the sample dataset**, or upload a UTF-8, comma-separated CSV with a header. Use **Data tools** for local operations without any API key.

For natural-language chat, enter an Anthropic API key in the sidebar or set `ANTHROPIC_API_KEY` in the shell before launching. The model is configured in `config.toml`; `ANTHROPIC_MODEL` or the sidebar can override it. A key must have API credits and access to the selected model. The app does not read `.env` files automatically. Never commit credentials.

## Included features

- CSV inspection, column types, missing counts and duplicate detection.
- Duplicate removal across all or selected columns, keeping the first occurrence.
- Mean, median, mode, constant and automatic missing-value imputation. Auto uses numeric median and categorical mode. All-empty columns require a constant. A failed multi-column fill changes nothing.
- Bar, line, scatter and histogram charts, including count, sum and mean aggregation.
- Read-only SQL against `dataset`, with executed SQL and numerical results displayed.
- Ten undo snapshots, an append-only session change history and JSON history download.
- Downloads of the working CSV and the exact original upload.
- Bounded multi-step Claude tool use, validated tool arguments and visible tool errors.

Example prompts: “Find all missing values”, “Remove duplicate rows”, “Fill missing units with the median”, “Plot total revenue by region”, “What is total revenue for Business customers?” and “Undo the last change”.

## Architecture

```text
Streamlit UI → Claude Messages API → declared tool call
                                      ↓
                          JSON Schema argument validation
                                      ↓
                          pandas / DuckDB / Plotly
                                      ↓
                       bounded result → Claude explanation
                                      ↓
                         visible evidence + session history
```

`assistant/data.py` owns dataset operations and undo. `assistant/sql.py` validates and runs SQL. `assistant/tools.py` declares and dispatches the permitted tools. `assistant/agent.py` implements the model/tool loop. `app.py` manages the session and interface. `config.toml` records model and resource limits.

The model receives metadata, user prompts and bounded tool results, not the uploaded CSV file. SQL results can still contain raw cell values; ask aggregate questions when possible. Chart payloads stay local. Credentials are not included in model context. Dataset headers and cell contents are treated as untrusted data in the system instructions. These instructions reduce prompt-injection risk but do not prove model immunity; SQL and tool constraints are enforced independently in Python.

## Boundaries and interpretation

This is a local coursework prototype, without authentication or durable storage. Browser refreshes/reconnects can discard session state; download work before leaving. A fresh upload clears the old chat and history. The app retains the original CSV in memory, not on disk.

- Uploads: 10 MB, 100,000 rows, 100 columns. Column names must be nonempty and unique ignoring case. CSV types and standard missing markers are inferred by pandas; identifiers with leading zeroes can be interpreted as numbers. Keep the original download if exact formatting matters.
- SQL: one SELECT, including nonrecursive SELECT CTEs. Only `dataset` and query-local CTEs are accessible. A conservative function allowlist excludes file/network functions and unsupported SQL. External access and automatic extension installation/loading are disabled. Each connection uses two threads and a 256 MB DuckDB memory budget, with a five-second interruption timer. These are prototype limits, not an operating-system security sandbox; do not expose this application as an unrestricted public SQL service.
- SQL returns at most 50 rows, with truncation disclosed. Aggregates operate over all rows. SQL NULL semantics apply.
- Charts exclude rows missing their required fields. Raw charts above 5,000 complete rows use a reproducible random sample. Grouped charts use all complete rows and reject more than 100 groups. Read chart sampling and exclusion counts before interpreting it.
- Imputation does not recover known truth. Mode ties use the first mode returned by pandas. No-op operations do not consume an undo step; undo itself is recorded. Changing a CSV may alter inferred types and output formatting.
- The model may still explain a result incorrectly. The displayed tool outputs are the evidence. If an API request fails after a tool changes data, that change remains visible and can be undone. Tool errors do not cause automatic retries of mutations.
- Conversation context retains eight completed turns. API calls have timeouts and tool budgets. Direct local actions reset model conversation context, while visible historical results remain labelled with their recorded dataset version.

## Tests and experiments

```bash
python -m pytest -q
python -m experiments.evaluate business
python -m experiments.evaluate imputation
```

The business command checks 30 fixed reference SQL queries against known answers on `data/business_sales.csv`. Expected answers were calculated independently using Python's standard library; they are stored as literals in `experiments/business_questions.json`. This local test does **not** measure the model's ability to answer natural-language questions.

The imputation command creates 600 complete synthetic rows with seed 42, masks 5%, 10% and 20% of values using five random seeds, and compares mean, median, mode and auto. It reports numeric MAE/RMSE and categorical mode accuracy on hidden cells only. This is missing-completely-at-random evaluation, not evidence about other missingness patterns.

Live experiments consume Anthropic API credits and require `ANTHROPIC_API_KEY`:

```bash
python -m experiments.evaluate routing --live
python -m experiments.evaluate business --live
```

Routing scores the first selected tool across 40 prompts and does not execute those tool calls. Business evaluation runs the assistant and compares its final successful SQL result cells with the reference answers; column labels are ignored, order and numeric tolerance matter. Review stored explanations separately. Reports contain timestamps, configuration, model and package versions, and are written to the ignored `experiments/results/` directory. Reports are not participant data.

`experiments/adversarial_prompts.json` supplies manual robustness cases. `experiments/user_study.md` supplies a 10–15 participant protocol. Live-model accuracy and user-study outcomes must be measured; they are not asserted by local unit tests. Record runs and limitations in `experiments/LOG.md`.

## Development and sources

The existing Git repository is ready for local version control. No remote repository has been created or pushed. `.gitignore` excludes credentials, the virtual environment and generated experiment reports. `requirements.txt` pins the tested dependencies.

Implementation references: [Anthropic tool-call protocol](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls), [Claude model IDs](https://platform.claude.com/docs/en/models/overview), [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state), and [DuckDB security guidance](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview).
