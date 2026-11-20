# StudentBank AI Smart Financial Assistant

Module: FGCT6020 — Artificial Intelligence and Creativity

## One-sentence definition

My project takes simulated UK banking transaction data and uses AI to classify spending and generate financial insights, producing visual and spoken feedback through a smart gadget so that students can understand their spending more easily.

This is the proposed whole-project outcome. Visual feedback and model training are Stage 1; spoken feedback and the physical gadget are Stage 2. The structure follows the input → AI function → output → user benefit exercise on page 27 of the supplied Week 7 framework workshop. The hardware is a project choice, not a workshop requirement.

## Purpose and creative question

Build a separate prototype alongside the StudentBank mobile application without changing that application or accessing real accounts. The creative question is how a combination of visible evidence and short spoken summaries can help students interpret spending while retaining control over uncertain AI category suggestions.

## Stage 1 research question

How does a small PyTorch neural classifier compare with a majority-class baseline and logistic regression when categorising fictional GBP transaction descriptions from held-out merchant groups?

The initial experiment holds the dataset, partitions and text features fixed. Compare accuracy, macro precision, recall and F1, plus per-class scores and confusion matrices. The first fixture has shared description templates, so this experiment measures performance in a restricted synthetic setting. Follow-up descriptions must be authored independently to test broader generalisation.

## Implementation and scope

Stage 1 uses 400 reproducibly generated outgoing transactions in five spending categories. Character TF-IDF is fitted on training descriptions. A CPU PyTorch network is selected on validation data and evaluated on the held-out test set. Python separately computes money totals in integer pence. A Streamlit interface displays predictions, charts, deterministic summary text and model evidence. No LLM is required for this stage.

Stage 2 will connect a Raspberry Pi and speaker, choose an offline text-to-speech engine compatible with the actual device, and speak the verified summary. Incoming-payment simulation requires an explicit transaction-direction schema. It must not be inferred from the Stage 1 positive-spending convention.

The first Stage 2 software increment adds offline speech generation on the development computer, a browser audio player, a WAV download and a matching transcript. Physical speaker delivery and listening quality still need verification; this increment does not establish completion of the gadget.

The minimum full-project demonstration is: load a fictional CSV, classify transactions with the trained model, and speak a short verified GBP summary through a connected speaker. Only the first two and text preparation are complete in Stage 1. OLED, conversational interactions and notifications remain stretch goals.

## Evaluation still to perform

Test on independently authored descriptions and inspect ambiguous merchants, abbreviations, unknown vocabulary and subgroup/category errors. Test device playback, availability, pronunciation of GBP amounts, repeated announcements and disconnect/reconnect behaviour before claiming spoken reliability. Conduct consent-based usability testing of comprehension, task completion and clarity. Record genuine observations and limitations rather than treating a written protocol as results.

## Coursework mapping

| Supplied material | Evidence in this project |
| --- | --- |
| Workshop 1 | CSV exploration and charts; structured source code. Student still needs honest Git commits and portfolio evidence. |
| Workshop 2 | Preprocessing fitted only on training data; trained baseline comparisons; accuracy, precision, recall, F1 and confusion matrices. |
| Week 7 framework workshop | PyTorch training, YAML configuration, pinned dependencies and CSV experiment log. |
| Week 7 NLP/interaction material | Clear system role, model/version documentation, transparent scores, human review and future interaction testing. |
| Project report template | Proposal and technical evidence can support the report; completed background research, critical reflection, bibliography and authorship account remain to be written. |

No complete final assessment brief or marking rubric was supplied. Do not invent assessment weights or claim that these workshop mappings alone guarantee compliance.
