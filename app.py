"""StudentBank dashboard and offline voice preview; no API key needed."""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from studentbank.model import Predictor
from studentbank.speech import announcement, speech_engine, synthesise
from studentbank.transactions import load_transactions, pounds, summarise

st.set_page_config(page_title="StudentBank AI · Spending companion", page_icon="💷", layout="wide")


@st.cache_resource
def get_predictor(model_directory, checkpoint_timestamp):
    return Predictor(model_directory)


@st.cache_data(max_entries=4)
def classify_csv(raw, model_version, checkpoint_timestamp):
    frame = load_transactions(raw)
    predictor = get_predictor(str(ROOT / "models"), checkpoint_timestamp)
    return predictor.classify(frame)


with st.sidebar:
    st.title("StudentBank AI")
    st.caption("YOUR SPENDING, MADE CLEARER")
    st.info("Local AI model + voice preview\n\nSimulated GBP spending only. No bank connection.")
    upload = st.file_uploader("Load fictional transactions", type=["csv"])
    use_sample = st.button("Use 400 sample transactions", width="stretch")
    sample_bytes = (ROOT / "data/sample_transactions.csv").read_bytes()
    st.download_button("Download sample CSV", sample_bytes, "sample_transactions.csv", "text/csv", width="stretch")
    st.divider()
    st.markdown("**CSV format**")
    st.caption("transaction_id, date, description, amount_gbp, currency. Use YYYY-MM-DD dates, positive outgoing amounts and GBP. Up to 5 MB / 10,000 rows.")
    st.caption("Income, refunds and incoming payment announcements belong to a later stage. This prototype handles outgoing spending only.")
    st.caption("Predictions and files stay on the computer running this app. No cloud model or API key is used.")

if "studentbank_source" not in st.session_state:
    st.session_state.studentbank_source = (sample_bytes, "Sample · 400 fictional transactions")
if use_sample:
    st.session_state.studentbank_source = (sample_bytes, "Sample · 400 fictional transactions")
    if upload is not None:
        st.session_state.last_studentbank_upload = hashlib.sha256(upload.getvalue()).hexdigest()
elif upload is not None:
    signature = hashlib.sha256(upload.getvalue()).hexdigest()
    if signature != st.session_state.get("last_studentbank_upload"):
        st.session_state.studentbank_source = (upload.getvalue(), upload.name)
        st.session_state.last_studentbank_upload = signature

st.caption("FGCT6020 · ARTIFICIAL INTELLIGENCE AND CREATIVITY")
st.title("Make sense of your spending.")
st.write("A trained AI model suggests spending categories. Python turns the transactions into clear GBP totals and visual insights.")

model_path = ROOT / "models/model.pt"
if not model_path.exists():
    st.warning("Train the StudentBank model first, then refresh this page.")
    st.code("python src/train.py", language="bash")
    st.stop()
checkpoint_timestamp = model_path.stat().st_mtime_ns
try:
    predictor = get_predictor(str(ROOT / "models"), checkpoint_timestamp)
    raw, source_name = st.session_state.studentbank_source
    frame = classify_csv(raw, predictor.metadata["run_id"], checkpoint_timestamp)
except (ValueError, OSError, RuntimeError) as exc:
    st.error(f"Could not load the data or model: {exc}")
    st.stop()
summary = summarise(frame)
st.caption(f"{source_name} · {summary['start_date']} to {summary['end_date']}")

columns = st.columns(4)
for column, label, value in zip(columns, ["Total outgoing", "Transactions", "Categories", "Need review"],
                                 [pounds(summary["total_pence"]), str(len(frame)), "5", str(summary["needs_review"])]):
    column.metric(label, value)

overview, classify, evaluation, project = st.tabs(["Spending overview", "Classify a transaction", "Model evaluation", "Project & next steps"])
with overview:
    st.subheader("Your spending snapshot")
    st.write(summary["announcement_text"])
    st.caption("Category totals use predicted labels. Low-score or unrecognised descriptions stay in ‘needs review’; every transaction remains included in the overall total.")
    left, right = st.columns([1, 1.25])
    categories = pd.DataFrame([{"Category": name.title(), "GBP": value / 100}
                               for name, value in summary["by_category_pence"].items()])
    colours = ["#147D73", "#4F72B8", "#DAA140", "#9873B9", "#D47768", "#8C939B"]
    with left:
        figure = px.pie(categories, names="Category", values="GBP", hole=0.58,
                        color_discrete_sequence=colours, title="Predicted spending categories")
        figure.update_traces(hovertemplate="%{label}: £%{value:,.2f}<extra></extra>")
        figure.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(figure, width="stretch")
    with right:
        daily = frame.groupby("date", as_index=False)["amount_pence"].sum().sort_values("date")
        daily["GBP"] = daily.amount_pence / 100
        figure = px.bar(daily, x="date", y="GBP", title="Daily outgoing spending", color_discrete_sequence=["#147D73"])
        figure.update_layout(xaxis_title=None, yaxis_title="GBP", margin=dict(l=10, r=10, t=50, b=10))
        figure.update_traces(hovertemplate="%{x}: £%{y:,.2f}<extra></extra>")
        st.plotly_chart(figure, width="stretch")
    st.subheader("Transactions and model suggestions")
    show_review = st.checkbox("Show only transactions needing review")
    visible = frame[frame.needs_review] if show_review else frame
    display = visible[["date", "description", "amount_pence", "predicted_category", "model_score", "needs_review"]].copy()
    display["amount_pence"] = display.amount_pence.map(pounds)
    display["model_score"] = display.model_score.map(lambda value: f"{value:.1%}")
    display.columns = ["Date", "Description", "Amount", "Suggested category", "Model score", "Needs review"]
    st.dataframe(display, hide_index=True, width="stretch")
    st.caption("Model scores are uncalibrated softmax outputs, not guaranteed probabilities of correctness. Review unfamiliar merchants and ambiguous descriptions.")
    st.download_button("Download classified transactions", frame.to_csv(index=False).encode(), "studentbank_classified.csv", "text/csv")
    st.subheader("Listen to your spending summary")
    speech_text = announcement(summary)
    # A changed summary must never retain an earlier recording in the player.
    if st.session_state.get("speech_text") != speech_text:
        st.session_state.speech_text = speech_text
        st.session_state.pop("speech_audio", None)
    engine = speech_engine()
    st.caption("Generate audio on this computer, then press play. Use the player's pause and seek controls; adjust or mute your device volume. Audio never starts automatically.")
    if engine is None:
        st.info("Voice generation needs a macOS system voice or eSpeak installed on the computer running the app. You can still download the summary text.")
    if st.button("Generate spoken summary", disabled=engine is None):
        try:
            with st.spinner("Creating offline speech…"):
                st.session_state.speech_audio = synthesise(speech_text)
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))
    if "speech_audio" in st.session_state:
        st.audio(st.session_state.speech_audio, format="audio/wav", autoplay=False,
                 alt="Spoken summary of fictional outgoing spending and estimated categories")
        st.download_button("Download spoken summary", st.session_state.speech_audio, "studentbank_summary.wav", "audio/wav")
    with st.expander("Read the spoken summary"):
        st.write(speech_text)
        st.download_button("Download announcement text", speech_text, "studentbank_summary.txt", "text/plain")
    st.caption("Computer voice prototype. Raspberry Pi integration and listening tests on the physical speaker remain to be completed.")

with classify:
    st.subheader("Try a transaction description")
    st.write("Try ‘Tesco weekly groceries’, ‘TfL bus ticket’ or ‘Odeon cinema tickets’.")
    with st.form("predict_transaction"):
        description = st.text_input("Description", value="Tesco weekly groceries", max_chars=200)
        submitted = st.form_submit_button("Predict category", type="primary")
    if submitted:
        try:
            st.session_state.studentbank_prediction = (description, predictor.predict([description])[0])
        except ValueError as exc:
            st.error(str(exc))
    if "studentbank_prediction" in st.session_state:
        description, prediction = st.session_state.studentbank_prediction
        st.caption(description)
        st.metric("Suggested category", prediction["predicted_category"].title(), delta=None)
        if prediction["needs_review"]:
            st.warning("Needs review: " + prediction["review_reason"])
        scores = pd.DataFrame({"Category": [name.title() for name in prediction["scores"]],
                               "Score": list(prediction["scores"].values())})
        fig = px.bar(scores, x="Score", y="Category", orientation="h", color_discrete_sequence=["#147D73"])
        fig.update_layout(xaxis=dict(range=[0, 1], tickformat=".0%"), height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    st.info("This small model was trained on synthetic, category-specific phrases. It can be confidently wrong on real-world descriptions. No transaction is changed by this prediction.")

with evaluation:
    st.subheader("Measured performance, with a held-out test set")
    metrics = json.loads((ROOT / "models/metrics.json").read_text())
    metadata = predictor.metadata
    sizes = metadata["partition_sizes"]
    st.caption(f"{sizes['train']} training · {sizes['validation']} validation · {sizes['test']} test rows. Merchant groups do not overlap. Checkpoint chosen using validation data only.")
    comparison = pd.DataFrame([{"Model": name.replace("_", " ").title(),
                               "Accuracy": result["accuracy"], "Precision (macro)": result["precision_macro"],
                               "Recall (macro)": result["recall_macro"], "F1 (macro)": result["f1_macro"]}
                              for name, result in metrics["test_results"].items()])
    st.dataframe(comparison.style.format({name: "{:.3f}" for name in comparison.columns if name != "Model"}), hide_index=True, width="stretch")
    st.warning("Synthetic benchmark only: the merchants are held out, but the phrase templates are shared across partitions. These scores do not establish real-bank accuracy. The overview sample includes training rows and is not a separate evaluation.")
    matrix, losses = st.columns(2)
    with matrix:
        result = metrics["test_results"]["pytorch_mlp"]
        fig = px.imshow(result["confusion_matrix"], x=result["category_order"], y=result["category_order"],
                        text_auto=True, color_continuous_scale="Teal", title="PyTorch confusion matrix",
                        labels={"x": "Predicted category", "y": "Reference category", "color": "Count"})
        st.plotly_chart(fig, width="stretch")
    with losses:
        curve = pd.read_csv(ROOT / "models/learning_curve.csv")
        fig = px.line(curve, x="epoch", y=["train_loss", "validation_loss"], title="Training and validation loss",
                      color_discrete_sequence=["#147D73", "#DAA140"])
        fig.add_vline(x=metadata["chosen_epoch"], line_dash="dot")
        st.plotly_chart(fig, width="stretch")
    with st.expander("Per-category precision, recall and F1"):
        st.dataframe(pd.DataFrame({name: result["classification_report"][name] for name in metadata["categories"]}).T)
    with st.expander("Run provenance and limitations"):
        st.json(metadata)
        st.json(metrics["review_policy"])
    st.download_button("Download evaluation metrics", json.dumps(metrics, indent=2), "studentbank_metrics.json", "application/json")

with project:
    st.subheader("StudentBank AI Smart Financial Assistant")
    st.write("This project takes simulated UK banking transactions and uses AI to classify spending, producing visual insights and a computer voice preview, with a smart gadget planned so students can understand spending more easily.")
    st.markdown("**Stage 1 — implemented:** fictional CSV data, trained PyTorch classifier, majority and logistic-regression baselines, held-out evaluation, visual summaries and prediction exports.")
    st.markdown("**Stage 2 — computer prototype:** offline WAV generation, a playback control and audio download. Raspberry Pi integration, physical speaker checks and usability testing are still planned. An OLED display, conversational assistant and incoming payment simulation are stretch goals.")
    st.write("This is a separate coursework prototype. It does not connect to or modify the StudentBank mobile application.")
    st.caption("The dataset contains 400 artificial records, not a representative student's banking history. Amounts use integer pence for calculations; reference labels are never passed into the classifier.")
