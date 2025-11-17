import streamlit as st
import json
import os

st.title("Step 2: Extract Eligibility Criteria")

study_path = st.session_state.study_path
criteria_dir = os.path.join(study_path, "criteria")

if st.button("Extract Criteria"):
    st.info("Running AI criteria extraction…")
    # TODO: actual LLM/NLP extraction
    inclusion = [{"id": "INC1", "text": "Age ≥ 18", "type": "numeric"}]
    exclusion = [{"id": "EXC1", "text": "Pregnant", "type": "dx"}]

    json.dump(inclusion, open(os.path.join(criteria_dir, "inclusion.json"), "w"))
    json.dump(exclusion, open(os.path.join(criteria_dir, "exclusion.json"), "w"))

    st.success("Criteria extracted!")

# Table editors
if os.path.exists(os.path.join(criteria_dir, "inclusion.json")):
    inclusion = json.load(open(os.path.join(criteria_dir, "inclusion.json")))
    st.subheader("Inclusion Criteria")
    edited = st.data_editor(inclusion)
    json.dump(edited, open(os.path.join(criteria_dir, "inclusion.json"), "w"))

if os.path.exists(os.path.join(criteria_dir, "exclusion.json")):
    exclusion = json.load(open(os.path.join(criteria_dir, "exclusion.json")))
    st.subheader("Exclusion Criteria")
    edited = st.data_editor(exclusion)
    json.dump(edited, open(os.path.join(criteria_dir, "exclusion.json"), "w"))

if st.button("Lock Criteria"):
    st.session_state["criteria_locked"] = True
    st.success("Criteria locked.")

if st.button("Continue → Patient Data"):
    st.switch_page("pages/4_Patient_Data.py")
