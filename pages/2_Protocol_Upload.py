import streamlit as st
import os

st.title("Step 1: Upload Protocol")

if not st.session_state.current_study:
    st.error("No study selected. Return to Study Selector.")
    st.stop()

study_path = st.session_state.study_path
protocol_dir = os.path.join(study_path, "protocol")

uploaded = st.file_uploader("Upload Protocol PDF", type=["pdf"])

if uploaded:
    with open(os.path.join(protocol_dir, "protocol.pdf"), "wb") as f:
        f.write(uploaded.read())
    st.success("Protocol uploaded successfully.")

if st.button("Extract Text"):
    st.info("Running text extraction (placeholder)…")
    # TODO: call your PDF → text function
    st.write("✓ Text extracted and saved.")

if st.button("Continue → Criteria Extraction"):
    st.switch_page("pages/3_Criteria_Extraction.py")
