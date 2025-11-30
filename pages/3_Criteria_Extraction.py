import streamlit as st
import json
import os
from utils.criteria_consensus import extract_all_criteria

st.title("Step 2: Extract Eligibility Criteria")

# Ensure a study is selected
if not st.session_state.get("current_study"):
    st.error("No study selected. Return to Study Selector.")
    st.stop()

study_path = st.session_state.study_path
criteria_dir = os.path.join(study_path, "criteria")
os.makedirs(criteria_dir, exist_ok=True)

# -------------------------------------------------------
# Load protocol and extract criteria using the new pipeline
# -------------------------------------------------------

protocol_path = os.path.join(study_path, "protocol.pdf")

if not os.path.exists(protocol_path):
    st.error("Protocol file not found in this study directory.")
    st.stop()

# Load raw protocol text as best as possible
try:
    with open(protocol_path, "rb") as f:
        raw_bytes = f.read()
    try:
        raw_text = raw_bytes.decode("utf-8", errors="ignore")
    except Exception:
        raw_text = raw_bytes.decode("latin-1", errors="ignore")
except Exception as e:
    st.error(f"Could not read protocol file: {e}")
    st.stop()

# Run full consensus extractor
st.subheader("Extracting criteria. This may take a moment...")
inclusion, exclusion = extract_all_criteria(raw_text, protocol_path)

# Save results
inc_path = os.path.join(criteria_dir, "inclusion.json")
exc_path = os.path.join(criteria_dir, "exclusion.json")

json.dump(inclusion, open(inc_path, "w"), indent=2)
json.dump(exclusion, open(exc_path, "w"), indent=2)

st.success("Eligibility criteria extracted successfully.")

# -------------------------------------------------------
# Display and allow editing of extracted criteria
# -------------------------------------------------------

st.subheader("Inclusion Criteria")
if os.path.exists(inc_path):
    inclusion_loaded = json.load(open(inc_path))
    edited = st.data_editor(inclusion_loaded, key="inc_editor")
    json.dump(edited, open(inc_path, "w"), indent=2)

st.subheader("Exclusion Criteria")
if os.path.exists(exc_path):
    exclusion_loaded = json.load(open(exc_path))
    edited = st.data_editor(exclusion_loaded, key="exc_editor")
    json.dump(edited, open(exc_path, "w"), indent=2)

# -------------------------------------------------------
# User actions
# -------------------------------------------------------

if st.button("Lock Criteria"):
    st.session_state["criteria_locked"] = True
    st.success("Criteria locked.")

if st.button("Continue → Patient Data"):
    st.switch_page("pages/4_Patient_Data.py")