import hashlib
import os

import streamlit as st

from assistant.agent import Assistant
from assistant.config import CONFIG, ROOT
from assistant.data import Dataset
from assistant.tools import execute

st.set_page_config(page_title="Bir Sahayak · Data Assistant", page_icon="📊", layout="wide")


def render_result(result):
    if result.error:
        st.error(result.data["error"])
        return
    if result.figure is not None:
        st.plotly_chart(result.figure, width="stretch", key=f"chart-{id(result)}")
    if "sql" in result.data:
        st.code(result.data["sql"], language="sql")
        import pandas as pd
        st.dataframe(pd.DataFrame(result.data["rows"], columns=result.data["columns"]), hide_index=True)
        st.caption(result.data["note"])
        if result.data["truncated"]:
            st.warning("This result is truncated. Narrow your query to see the remaining rows.")
    with st.expander(f"Verified result · {result.name}", expanded=result.figure is None and "sql" not in result.data):
        st.json(result.data)


def record_tool(name, arguments):
    dataset = st.session_state.dataset
    result = execute(dataset, name, arguments)
    st.session_state.messages.append({"role": "assistant", "text": "Local tool result", "results": [result], "version": dataset.version})
    # A direct action changes context independently of previous chat.
    st.session_state.pop("agent", None)


st.session_state.setdefault("messages", [])
with st.sidebar:
    st.markdown("## Bir Sahayak")
    st.caption("AI DATA ENGINEERING ASSISTANT")
    uploaded = st.file_uploader("Upload a CSV", type=["csv"], help="UTF-8, comma-separated; up to 10 MB, 100,000 rows and 100 columns.")
    sample = st.button("Try the sample dataset", width="stretch")
    st.divider()
    st.markdown("**Claude connection**")
    key = st.text_input("Anthropic API key", type="password", help="Or set ANTHROPIC_API_KEY before starting the app.")
    model = st.text_input("Model", value=os.environ.get("ANTHROPIC_MODEL", CONFIG["ai"]["model"]))
    api_key = key or os.environ.get("ANTHROPIC_API_KEY", "")
    st.caption("API key configured" if api_key else "Local tools available · add a key for chat")
    st.caption("Chat sends column names, data types, your messages and bounded tool results to Anthropic. SQL results may include cell values. Charts and the full CSV stay local.")
    st.caption("Your session is held in memory. Download your work before closing or refreshing the page.")

source = None
if sample:
    source = ((ROOT / "data/sample_sales.csv").read_bytes(), "sample_sales.csv", "sample")
elif uploaded is not None:
    raw = uploaded.getvalue()
    upload_id = hashlib.sha256(raw + uploaded.name.encode()).hexdigest()
    if upload_id != st.session_state.get("last_upload"):
        source = (raw, uploaded.name, upload_id)

if source:
    try:
        dataset = Dataset(source[0], source[1])
        st.session_state.dataset = dataset
        st.session_state.messages = []
        st.session_state.pop("agent", None)
        if source[2] != "sample":
            st.session_state.last_upload = source[2]
        elif uploaded is not None:
            st.session_state.last_upload = hashlib.sha256(uploaded.getvalue() + uploaded.name.encode()).hexdigest()
    except ValueError as exc:
        st.error(str(exc))

st.caption("FGCT6020 · ARTIFICIAL INTELLIGENCE AND CREATIVITY")
st.title("A clearer view of your data.")
st.markdown("Explore, clean and understand a CSV through conversation — with Python results you can inspect.")

if "dataset" not in st.session_state:
    st.info("Upload a CSV in the sidebar, or try the sample dataset to begin.")
    a, b, c = st.columns(3)
    a.markdown("### Inspect\nFind missing values, duplicates and column types.")
    b.markdown("### Improve\nFill gaps, remove duplicates and undo changes.")
    c.markdown("### Understand\nBuild charts and answer questions with SQL.")
    st.stop()

dataset = st.session_state.dataset
info = dataset.info()
st.caption(f"{dataset.name} · dataset version {dataset.version}")
metrics = st.columns(4)
for container, label, value in zip(metrics, ["Rows", "Columns", "Missing cells", "Duplicate rows"],
                                  [info["rows"], info["columns"], info["missing_cells"], info["duplicate_rows"]]):
    container.metric(label, f"{value:,}")

chat, preview, workbench, history = st.tabs(["Assistant", "Dataset preview", "Data tools", "Change history"])
with chat:
    st.caption("Try: ‘Find missing values’ · ‘Remove duplicate rows’ · ‘Chart total revenue by region’")
    quick = st.columns(3)
    for container, label, tool in zip(quick, ["Inspect dataset", "Find missing values", "Find duplicates"],
                                     ["dataset_info", "find_nulls", "find_duplicates"]):
        if container.button(label, width="stretch"):
            record_tool(tool, {})
            st.rerun()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])
            if "version" in message:
                st.caption(f"Recorded at dataset version {message['version']}")
            for result in message.get("results", []):
                render_result(result)
    if not api_key:
        st.info("Add an Anthropic API key in the sidebar to chat. All actions in Data tools work locally without a key.")
    prompt = st.chat_input("Ask about your dataset…", disabled=not api_key)
    if prompt:
        if len(prompt) > 8000:
            st.error("Please keep requests under 8,000 characters.")
        else:
            st.session_state.messages.append({"role": "user", "text": prompt})
            signature = hashlib.sha256((api_key + model).encode()).hexdigest()
            if "agent" not in st.session_state or st.session_state.get("agent_signature") != signature:
                st.session_state.agent = Assistant(api_key=api_key, model=model)
                st.session_state.agent_signature = signature
            with st.spinner("Checking your data…"):
                answer, results = st.session_state.agent.ask(prompt, dataset)
            st.session_state.messages.append({"role": "assistant", "text": answer, "results": results, "version": dataset.version})
            st.rerun()

with preview:
    st.caption("First 200 rows of the working dataset. Downloads include all rows.")
    st.dataframe(dataset.frame.head(200), width="stretch", hide_index=True)
    with st.expander("Column types"):
        st.dataframe(info["schema"], hide_index=True)
    left, right = st.columns(2)
    left.download_button("Download cleaned CSV", dataset.export_csv(), file_name="cleaned_dataset.csv", mime="text/csv", width="stretch")
    right.download_button("Download original CSV", dataset.original_bytes, file_name="original_dataset.csv", mime="text/csv", width="stretch")

with workbench:
    st.caption("These tools run locally. Results appear in the Assistant tab. Changes can be undone.")
    clean, visual = st.columns(2, gap="large")
    with clean:
        st.subheader("Clean your data")
        with st.form("duplicates"):
            subset = st.multiselect("Compare duplicate rows using", list(dataset.frame.columns), help="Leave empty to compare all columns.")
            if st.form_submit_button("Remove duplicates"):
                record_tool("remove_duplicates", {"columns": subset} if subset else {})
                st.rerun()
        with st.form("missing"):
            columns = st.multiselect("Columns to fill", list(dataset.frame.columns))
            strategy = st.selectbox("Fill strategy", ["auto", "mean", "median", "mode", "constant"])
            constant = st.text_input("Constant value (used only for constant strategy)")
            st.caption("Auto uses the median for numbers and the mode for categories. Entirely empty columns need a constant.")
            if st.form_submit_button("Fill missing values"):
                arguments = {"columns": columns, "strategy": strategy}
                if strategy == "constant":
                    arguments["value"] = constant
                record_tool("fill_missing", arguments)
                st.rerun()
    with visual:
        st.subheader("Visualise")
        with st.form("chart"):
            kind = st.selectbox("Chart type", ["bar", "line", "scatter", "histogram"])
            x = st.selectbox("X column", list(dataset.frame.columns))
            y = st.selectbox("Y column", [None] + list(dataset.frame.columns), format_func=lambda c: "None" if c is None else c)
            aggregation = st.selectbox("Aggregation", ["none", "count", "sum", "mean"])
            if st.form_submit_button("Generate chart"):
                arguments = {"kind": kind, "x": x, "aggregation": aggregation}
                if y is not None:
                    arguments["y"] = y
                record_tool("create_chart", arguments)
                st.rerun()
    st.subheader("Ask with SQL")
    with st.form("sql"):
        query = st.text_area("Read-only SQL", 'SELECT COUNT(*) AS row_count FROM dataset')
        st.caption("One SELECT statement over dataset. Results are limited to 50 rows.")
        if st.form_submit_button("Run query"):
            record_tool("query_sql", {"query": query})
            st.rerun()

with history:
    st.caption("The original upload is preserved. Up to 10 changes can be undone; the audit history includes undo actions.")
    if st.button("Undo last change", disabled=not dataset.can_undo):
        record_tool("undo", {})
        st.rerun()
    if dataset.history:
        for entry in reversed(dataset.history):
            with st.expander(f"Version {entry['version']} · {entry['operation']} · {entry['time'][:19]} UTC"):
                st.json(entry)
        st.download_button("Download change history", dataset.export_history(), file_name="change_history.json", mime="application/json")
    else:
        st.info("No changes yet. Inspecting data, generating charts and running SQL do not modify your dataset.")
