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
