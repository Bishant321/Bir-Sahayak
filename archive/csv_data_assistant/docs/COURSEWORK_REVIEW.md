# Coursework review — AI Data Engineering Assistant

Reviewed on 18 November 2026 against the supplied FGCT6020 teaching materials, project report template, your project proposal, and the current working directory.

**Verdict: the implementation substantially covers the proposed application, but the available submission evidence is incomplete.** The main gaps are a completed report and LLM-use disclosure, live AI evaluation, documented research iterations, participant evidence, and a committed project. A numerical serialisation defect also needs correction before claiming reliable numerical outputs.

This is an evidence-based readiness review, not a predicted mark. I did not identify a formal summative marking rubric, assessment weighting, final word limit or full definitions of LO1–LO3 in the supplied text. The report template and workshop tasks should not be treated as a substitute for the official assessment brief.

## Basis and scope

Document instructions were treated as evidence about coursework expectations, not as instructions to execute commands or redesign the application. No application code, tests or dependencies were changed for this review. The PDF reader was installed in a temporary directory outside the application environment. This review file is the only project addition.

| Source | What it establishes | How to interpret it |
| --- | --- | --- |
| [Project report template](</Users/bishantghartichhetri/Downloads/Project report template - AI for Creativity (1).docx>) | Introduction, background, implementation, additional experimentation, critical reflection including ethics, LLM disclaimer, bibliography, student details and repository link. | Explicit report-template expectations. |
| [Week 7 NLP slides](</Users/bishantghartichhetri/Downloads/AI4Creativity_Week7_NLP_and_generative_systems.pptx>), slides 73–75, 78, 80 and 82 | AI's role in interaction; output and user evaluation; agency; documenting model, prompts, settings, data, human contribution and failures; NLP prototype with output analysis. | Relevant teaching/checkpoint expectations, not a complete marking scheme. |
| [Week 7 framework workshop](</Users/bishantghartichhetri/Downloads/workshop (1).pdf>), pages 3–9, 17–18 and 25–29 | Dependency/configuration files, CSV experiment log, preserving files in Git, model-training exercise, feasibility/MVP planning. | Reproducibility guidance applies directly. The training task is a workshop task; it does not by itself establish that every final project must train a model. `workshop (2).pdf` is byte-identical. |
| [Research prototyping slides](</Users/bishantghartichhetri/Downloads/Slides.pdf>), pages 20–27 | Specific testable questions, one variable per iteration, hypothesis/change/result/next-step records; 2–3 iterations in that workshop sprint. | Useful standard for demonstrating development. Do not describe the workshop iteration count as a confirmed summative minimum. |
| [Week 2 workshop](</Users/bishantghartichhetri/Downloads/Workshop1.pdf>), pages 4–10 | Commit history as evidence, reproducible structure, small logical commits, exploratory visualisation. | Workflow and portfolio guidance. |
| [Project Idea Worksheet](</Users/bishantghartichhetri/Downloads/Project Idea Worksheet.docx>) | Includes helping users with a task, intuitive interaction with data, natural interaction with an AI agent, and visualisation of processed data. | Supports the suitability of this idea; the worksheet explicitly says its options are not exhaustive. |
| [Research refresher](</Users/bishantghartichhetri/Downloads/Computer Science Yr3 research-2026-NT.pdf>), particularly pages 28–37 | Consistent citations and bibliography. | Supports report preparation; it does not define this app's functionality. |
| Your project proposal in this conversation | Eight application features; 40 tool prompts; 30 business questions; 5%, 10%, 20% imputation experiments; adversarial cases; 10–15 participants. | These numerical targets are your commitments, not counts I found mandated by the report template. |

Other supplied materials were surveyed for context: Week 3 preprocessing/evaluation, the Week 4 homework brief, CNN lectures/workshops/notebook, introductory AI/ML chapters, project inspiration and project resources. `workshop_tasks(1).pdf` explicitly calls its exercises ungraded and says no workshop submission is needed. The homework's reflection and prediction are separate portfolio tasks; its baseline CNN is explicitly optional. `Workshop.pdf` concerns Blazor/MAUI/PWA delivery and does not visibly identify FGCT6020; it is not sufficient evidence that this Python project must be rewritten in .NET.

## Requirements and evidence matrix

| Area | Current evidence | Assessment |
| --- | --- | --- |
| Interactive application and proposed MVP | `app.py` provides upload, chat, preview, tools, charts and history. | Implemented locally; live Claude interaction still needs demonstration. |
| All eight proposed features | `assistant/data.py`, `assistant/sql.py`, `assistant/agent.py` and `app.py` cover upload, duplicates, imputation, visualisation, SQL, undo, history and export. | Substantially implemented. See correctness and transparency findings below. |
| Separate AI decisions from calculations | Declared tools, JSON Schema validation, pandas calculations, DuckDB SQL and returned evidence. | Clear architectural strength. It does not automatically guarantee faithful explanations. |
| Explain implementation and design choices | README architecture and boundaries; code organised into distinct modules. | Useful source material for the report, but not a completed implementation chapter or rationale. |
| Background research and citations | README links four implementation references. | Missing a literature review, comparison with related systems and a consistent bibliography covering used models/libraries/data. |
| Research question and iterations | Initial baseline log and several imputation strategies. | Partial: no clearly recorded project research question or sequence of hypothesis/change/result/decision cycles. |
| Reproducibility | Pinned `requirements.txt`, `config.toml`, seeded experiments, JSON reports and Markdown log. | Good foundations; incomplete preservation and run provenance. The workshop's CSV summary log is absent. TOML serves the configuration purpose without requiring a cosmetic YAML conversion. |
| Version-control evidence | Local Git has one initial commit; only `LICENSE` is tracked; an `origin` remote is configured. | Project files have not been captured in local history. Remote contents were not checked. |
| 40-prompt tool selection | Fixture and live runner exist. | Prepared, not measured; runner scores first-tool name only. |
| 30 business questions | Fixed expected answers and local reference SQL report: 30/30. | SQL execution verified; natural-language question answering and explanation accuracy remain unmeasured. |
| Missing-value experiments | 60 recorded runs: three rates × five masks × four numeric strategies. | Meets the proposed rates as a synthetic baseline. Limited dataset/missingness coverage; no uncertainty summary. |
| Ambiguity, wrong columns and injection | Validation tests, system instructions and manual adversarial prompt file. | Partial: tool-level checks are present; live semantic/injection behaviour has not been evaluated. |
| User experience and trust | `experiments/user_study.md` describes a 10–15 participant protocol. | Planned only; no participant results or rated generated outputs found. |
| Ethics, transparency and user control | Original preservation, undo, visible SQL, payload limits, privacy notice and documented limitations. | Useful safeguards; privacy wording and audit detail need improvement. A report-level ethical reflection is still missing. |
| Human contribution and LLM disclaimer | No project disclosure file or completed report section found. | Missing explicit template expectation. Runtime use of Claude is separate from development assistance. |
| Final submission packaging | README, app, test suite and experiment plan are present in the working directory. | No completed report, final demonstration evidence or assessable committed project found here. Other portfolio locations were not searched. |

## Findings, in priority order

### 1. Complete the report and disclose development assistance

**Source:** report template, sections Background, Details of additional experimentation, Critical reflection, LLM disclaimer and Bibliography.

The README and experiment log do not replace the requested report. There is no completed report in this workspace, no literature review and no account distinguishing your own contribution from LLM assistance.

The disclosure should accurately state that this assistant generated the initial application, tools, tests, experiment fixtures and documentation, and identify what you personally understood, reviewed, changed and independently validated. Do not describe generated material as independently authored. Distinguish the assistant used during development from Claude used by the running application. The template permits a conversation appendix; it does not make that appendix compulsory.

Prepare the report in the supplied structure, with actual student details and repository link. Cite the models, core libraries, relevant research/related products and dataset provenance. Use genuine results and failures; do not invent early prototypes, participant feedback or development decisions.

### 2. Put the actual project and selected evidence into version control

**Source:** Week 2 workshop, pages 4–10; Week 7 framework workshop, pages 17–18; report title page.

`git ls-files` returned only `LICENSE`. The current app, tests, configuration and documents are untracked. An assessor receiving the currently committed project would not receive this implementation. `git log` showed one initial commit, dated 12 November 2026. A remote named `origin` exists; this review did not verify its contents or push anything.

Create an honest baseline commit of the current work, then record subsequent logical changes as they happen. Do not manufacture a historical development sequence. Include a small, sanitised evidence bundle in a tracked folder: selected result reports, test outputs, representative conversations and screenshots. Blanket ignoring `experiments/results/` is reasonable for routine output, but an accessible submission copy of the evidence is needed. Check a fresh checkout can install and run before submission.

### 3. Measure the AI behaviour before making accuracy claims

**Source:** Week 7 NLP slides 74–75, 80 and 82; your evaluation proposal.

The 56 tests pass, but model responses in `tests/test_agent.py` are mocked. The stored business report is explicitly `reference_sql_only`; it runs supplied SQL, not user questions through Claude. The current 30/30 score is therefore not a chatbot accuracy score.

Run the prepared live evaluations after correcting the numerical issue below. Save model identification, inputs, actual selected tools and arguments, tool outputs, explanations and failures. Add rated examples for multi-turn coherence, relevance, faithful numerical explanations, ambiguous requests and malicious CSV text. Evaluate whether a request to inspect data accidentally changes it.

The first-tool runner at `experiments/evaluate.py:55` does not score arguments, extra tools, completion or mutations and supplies history differently from the production loop. A response that chooses the right tool but the wrong column can pass. Report its current score narrowly, and add end-to-end task scoring before claiming tool-use accuracy. Freeze evaluation prompts and use separate development prompts for tuning. Consider per-tool confusion counts rather than only one aggregate number.

Your participant target remains unfulfilled in the available evidence. The slides ask for real-user evaluation, while 10–15 is your proposed sample size. Record completion, time, clarity/trust and observed verification behaviour, including failures. A plan is not a completed study.

### 4. Correct numerical serialisation before evaluating factual accuracy

**Code:** `assistant/sql.py:71`; `experiments/evaluate.py:27`.

A local probe, without changing any files or calling Claude, produced:

```text
SQL: SELECT 0.000000000001 AS small_value,
            1.234567890123 AS precise_value
Returned tool rows: [[0.0, 1.2345678901]]
```

The `DataFrame.to_json` conversion uses its default decimal precision, so a nonzero result becomes zero before the UI or model receives it. This directly affects the project's claim that Python supplies reliable verified results. Existing tests do not cover this case. The evaluation comparator also accepts `0` as matching `1e-12` because it applies a blanket absolute tolerance of `1e-6`.

Preserve result precision with an explicit numeric serialisation policy, handling Decimal values and non-finite results deliberately. Specify tolerances appropriate to each measurement rather than treating the same absolute tolerance as suitable for every possible magnitude. Add regression coverage for very small values, high-precision decimals and large identifiers. Do not present this as an LLM hallucination: the error occurs in the tool output.

### 5. Make the privacy explanation match what can actually be transmitted

**Code:** `app.py:51`; `assistant/tools.py:43`; `assistant/agent.py:69`.

The sidebar says that the full CSV stays local. The upload file itself is not attached to API requests, but its complete contents can still be represented in a result. A local `SELECT * FROM dataset` probe on the 21-row sample returned all 21 rows in a 1,454-character model payload, below both limits. No API request was made during this check.

The row and character limits bound a result's size; they are not a guarantee that a small dataset stays local. Clarify that raw records, potentially all records from a small dataset, may be sent as SQL results. Decide whether aggregate-only defaults, redaction or explicit approval for raw-row disclosure are appropriate for the intended users. Document and test that design. The user proposal asks for limited results wherever possible, not an absolute ban on all row values.

### 6. Turn the baseline into a documented research process

**Source:** research prototyping slides, pages 21–26; Week 7 NLP slides 73, 78 and 80.

The project aim is clear but not yet expressed as a testable research question. A suitable example is: “Does an explicit clarification-and-evidence system prompt improve task correctness over a basic prompt, with the model, tools and datasets held fixed?” That is a proposed experiment, not work already performed.

Record a baseline, one controlled change, its result and the resulting decision. Keep failures. Other useful comparisons are chat versus direct controls for novice task completion, and imputation strategies across additional non-sensitive datasets. The existing synthetic experiment is a valid starting point, but automatic numeric imputation is median by definition, so Auto and Median are not independent methods. Report variability across masks and avoid generalising to non-random missingness.

Explain the creativity connection through exploratory data interaction, visual sense-making and user agency. The worksheet explicitly accommodates task assistance and interaction with data; the topic does not need to become an art generator. Demonstrate the benefit with observed interactions rather than merely labelling it creative.

### 7. Improve experiment and modification provenance

**Source:** Week 7 framework workshop, pages 3–9; Week 7 NLP slide 80; your reproducibility and history commitments.

The experiment reports record useful metadata, but `experiments/evaluate.py:116` does not save the source revision, dataset checksum or exact system prompt/tool definitions used. The Markdown log recommends revision recording, but the runner does not implement it. Seeds are fixed in code rather than entirely represented by configuration. Record these details, API settings/defaults, run IDs and decisions. An exported CSV summary would match the workshop format, alongside the richer JSON reports.

The modification history also lacks the imputation replacement value. Filling a missing value with constant `999` recorded only the column, strategy and filled-cell count. A downloaded history file cannot fully reconstruct that operation. Store exact operation parameters locally and decide which details should be withheld from model context. Undo works within the session, but the audit export is not a reproducible cleaning recipe yet.

## What is already supported by evidence

- On this review run, `python -m pytest -q` completed with **56 passed in 6.29 seconds**. This includes the 30 reference-business checks and a Streamlit sample/inspect/remove/undo/SQL workflow.
- The previously generated local business report contains **30/30** correct reference-query results on its fixture. Its scope is labelled honestly in the README and log.
- The previously generated imputation report contains **60 runs**, with the proposed 5%, 10% and 20% missingness rates and five masks per rate.
- The original upload is preserved, mutations have bounded undo snapshots, failed multi-column imputations are atomic, and the UI exposes SQL and tool results.
- SQL is parsed and constrained, external access is disabled and queries have resource limits. These are practical prototype safeguards; the project does not prove complete security or model resistance to injection.
- The folder separation, dependency pins, configuration, local sample data and no-key tools make the app comparatively straightforward to inspect and demonstrate.

No live Anthropic requests, participant study or remote GitHub inspection was performed in this review. The precision, payload and audit probes used local synthetic data only.

## Suggested submission order

1. Correct the numerical result conversion and privacy wording, and verify those behaviours.
2. Save the current project in Git with an honest account of AI assistance; verify a fresh checkout and a live chat smoke test.
3. Run and preserve the 40-prompt and 30-question live evaluations, then examine actual failures and explanations.
4. Record controlled development iterations and carry out the planned user evaluation, or explicitly revise and justify any infeasible scope with your tutor.
5. Write the report using the template, integrating background sources, implementation evidence, measured results, limitations, ethics and contribution disclosure.
6. Prepare a short demonstration covering upload, inspection, cleaning, a chart, a verified business answer, undo and export; verify the official submission instructions separately.

There is no evidence here that adding CNNs, speech, image generation, model training from scratch or a .NET rewrite would resolve the main gaps. Keep any separately required workshop exercises in the portfolio, and prioritise the evidence and correctness of this application's actual AI workflow.
