import streamlit as st
import pandas as pd
import os

st.title("Step 3: Upload Patient Data")

study_path = st.session_state.study_path
patient_dir = os.path.join(study_path, "patients")

uploaded = st.file_uploader("Upload patients_flat.csv", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df.to_csv(os.path.join(patient_dir, "processed.csv"), index=False)
    st.session_state["patient_data_ready"] = True
    st.dataframe(df.head())
    st.success("Patient data saved.")

if st.button("Continue → Matching"):
    st.switch_page("pages/5_Matching.py")
