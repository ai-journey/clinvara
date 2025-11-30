import streamlit as st
import json
import os
from utils import criteria_utils

st.title("Step 2: Extract Eligibility Criteria")

if not st.session_state.get("current_study"):
    st.error("No study selected. Return to Study Selector.")
    st.stop()

study_path = st.session_state.study_path
criteria_dir = os.path.join(study_path, "criteria")
os.makedirs(criteria_dir, exist_ok=True)

# If user previously set key in session, ensure process env has it so utils can read it
if st.session_state.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = st.session_state.get("OPENAI_API_KEY")

# Small UI to allow pasting an OpenAI API key at runtime (keeps it in session only)
with st.expander("OpenAI API Key (optional)"):
    api_key_input = st.text_input("Paste OpenAI API key (sk-...)", type="password", value=st.session_state.get("OPENAI_API_KEY", ""))
    if st.button("Set API Key", key="set_openai_key"):
        if api_key_input:
            st.session_state["OPENAI_API_KEY"] = api_key_input
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.success("OpenAI API key set for this session.")
        else:
            st.error("Please enter a non-empty key.")

# Extraction options
use_llm = st.checkbox("Use LLM-based extraction (requires OPENAI_API_KEY)", value=False)

if st.button("Extract Criteria"):
    st.info("Running criteria extraction…")
    txt_path = st.session_state.get("protocol_text_path") or os.path.join(study_path, "protocol", "protocol.txt")
    if not os.path.exists(txt_path):
        st.error("Protocol text not found. Run 'Extract Text' on the Protocol Upload step first.")
    else:
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()

            inclusion, exclusion = criteria_utils.extract_criteria(text, use_llm=use_llm)

            json.dump(inclusion, open(os.path.join(criteria_dir, "inclusion.json"), "w"), indent=2)
            json.dump(exclusion, open(os.path.join(criteria_dir, "exclusion.json"), "w"), indent=2)

            st.success("Criteria extracted and saved to study folder.")
        except Exception as e:
            st.error(f"Failed to extract criteria: {e}")

# Table editors
inc_path = os.path.join(criteria_dir, "inclusion.json")
exc_path = os.path.join(criteria_dir, "exclusion.json")

if os.path.exists(inc_path):
    inclusion = json.load(open(inc_path))
    st.subheader("Inclusion Criteria")
    edited = st.data_editor(inclusion)
    json.dump(edited, open(inc_path, "w"), indent=2)

if os.path.exists(exc_path):
    exclusion = json.load(open(exc_path))
    st.subheader("Exclusion Criteria")
    edited = st.data_editor(exclusion)
    json.dump(edited, open(exc_path, "w"), indent=2)

if st.button("Lock Criteria"):
    st.session_state["criteria_locked"] = True
    st.success("Criteria locked.")

if st.button("Continue → Patient Data"):
    st.switch_page("pages/4_Patient_Data.py")
