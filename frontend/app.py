import streamlit as st
import requests

API_URL = "http://localhost:8000"

MODELS = {
    "Llama 3.1 8B (Fast)": "meta/llama-3.1-8b-instruct",
    "Llama 3.1 70B (Accurate)": "meta/llama-3.1-70b-instruct",
    "Nemotron Nano 8B (NVIDIA)": "nvidia/llama-3.1-nemotron-nano-8b-v1",
    "Nemotron Ultra 550B (Powerful)": "nvidia/nemotron-3-ultra-550b-a55b",
}

st.set_page_config(page_title="Supply Chain CLAW", layout="wide")
st.title("Supply Chain CLAW")
st.caption("Autonomous supply chain monitoring powered by NVIDIA NemoClaw")

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")

    api_key = st.text_input(
        "NVIDIA API Key",
        type="password",
        placeholder="nvapi-...",
        help="Get your free key at build.nvidia.com"
    )

    selected_model_label = st.selectbox(
        "Select Model",
        options=list(MODELS.keys()),
        index=0
    )
    selected_model = MODELS[selected_model_label]

    st.caption(f"Model ID: `{selected_model}`")
    st.divider()

    health = requests.get(f"{API_URL}/health").json()
    st.metric("Hermes Skills Stored", health.get("memory_count", 0))
    st.caption("Skills grow every time the agent runs")

# --- Upload Section ---
st.header("1. Upload Supply Chain Data")
uploaded_file = st.file_uploader("Drop your CSV or Excel file here", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("Uploading file..."):
        response = requests.post(
            f"{API_URL}/upload",
            files={"file": (uploaded_file.name, uploaded_file.getvalue())}
        )
    if response.status_code == 200:
        st.success(f"Uploaded: {uploaded_file.name}")
    else:
        st.error("Upload failed")

# --- Run Agent ---
st.header("2. Run Agent")

if not api_key:
    st.warning("Enter your NVIDIA API Key in the sidebar to run the agent.")

if st.button("Analyze Now", type="primary", disabled=not api_key):
    with st.spinner(f"Nemotron ({selected_model_label}) is analyzing your supply chain..."):
        result = requests.post(
            f"{API_URL}/run",
            json={"api_key": api_key, "model": selected_model}
        )
        data = result.json()

    st.info(f"Model used: `{data.get('model_used', selected_model)}`")

    anomalies = data.get("anomalies", "None")
    reasoning = data.get("reasoning", "None")
    action = data.get("action", "None")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Anomalies Found")
        st.warning(anomalies)
    with col2:
        st.subheader("Reasoning")
        st.info(reasoning)

    st.subheader("Action Taken")
    st.success(action)

    # --- Verification Section ---
    st.header("3. Verification — Agent vs Data")
    st.caption("Cross-checking agent claims against actual data using Python")

    with st.spinner("Verifying..."):
        verify_result = requests.post(
            f"{API_URL}/verify",
            json={"anomalies": anomalies}
        ).json()

    if "error" in verify_result:
        st.error(verify_result["error"])
    else:
        score = verify_result.pop("accuracy_score", "")
        percent = verify_result.pop("accuracy_percent", 0)

        col1, col2 = st.columns(2)
        col1.metric("Accuracy Score", score)
        col2.metric("Accuracy %", f"{percent}%")

        st.divider()

        for check_name, result in verify_result.items():
            if not isinstance(result, dict):
                continue
            claimed = result.get("agent_claimed", False)
            confirmed = result.get("data_confirms", False)
            count = result.get("count", result.get("columns", ""))

            if claimed and confirmed:
                icon, status = "✅", "Agent correct — data confirms"
            elif claimed and not confirmed:
                icon, status = "❌", "Agent wrong — not found in data"
            elif not claimed and confirmed:
                icon, status = "⚠️", "Agent missed this — exists in data"
            else:
                icon, status = "➖", "Not claimed, not found"

            st.markdown(f"{icon} **{check_name.replace('_', ' ').title()}** — {status} | Count: `{count}`")

# --- Past Decisions ---
st.header("4. Hermes Skills — Past Decisions")
decisions = requests.get(f"{API_URL}/decisions").json()

if not decisions:
    st.write("No decisions yet. Upload data and run the agent.")
else:
    for d in decisions:
        with st.expander(f"{d['timestamp']} — {d['action'][:80]}"):
            st.markdown(f"**Anomaly:** {d['anomaly']}")
            st.markdown(f"**Reasoning:** {d['reasoning']}")
            st.markdown(f"**Action:** {d['action']}")
