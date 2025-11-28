import streamlit as st
import json
import os
import shutil

st.title("Step 2: Extract Eligibility Criteria")

study_path = st.session_state.study_path
criteria_dir = os.path.join(study_path, "criteria")
protocol_dir = os.path.join(study_path, "protocol")

# Ensure criteria directory exists
os.makedirs(criteria_dir, exist_ok=True)

# If criteria files are not yet in criteria_dir but exist in protocol_dir,
# copy them over so this page can present them for review and editing.
proto_inclusion = os.path.join(protocol_dir, "inclusion.json")
proto_exclusion = os.path.join(protocol_dir, "exclusion.json")
crit_inclusion = os.path.join(criteria_dir, "inclusion.json")
crit_exclusion = os.path.join(criteria_dir, "exclusion.json")

if (not os.path.exists(crit_inclusion)) and os.path.exists(proto_inclusion):
    shutil.copy(proto_inclusion, crit_inclusion)

if (not os.path.exists(crit_exclusion)) and os.path.exists(proto_exclusion):
    shutil.copy(proto_exclusion, crit_exclusion)

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

if (
    not os.path.exists(os.path.join(criteria_dir, "inclusion.json"))
    and not os.path.exists(os.path.join(criteria_dir, "exclusion.json"))
):
    st.info(
        "No criteria files were found. Go back to Step 1 to upload the protocol and run automatic extraction, or add criteria files manually."
    )

if st.button("Lock Criteria"):
    st.session_state["criteria_locked"] = True
    st.success("Criteria locked.")

if st.button("Continue → Patient Data"):
    st.switch_page("pages/4_Patient_Data.py")
