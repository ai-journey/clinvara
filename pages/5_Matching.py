import streamlit as st
import pandas as pd
import json
import os
import time

st.title("Step 4: Run Eligibility Matching")

study_path = st.session_state.study_path
patient_csv = os.path.join(study_path, "patients", "processed.csv")
inclusion_file = os.path.join(study_path, "criteria", "inclusion.json")
exclusion_file = os.path.join(study_path, "criteria", "exclusion.json")

if st.button("Run Matching"):
    st.info("Running matching engine…")

    start = time.time()
    df = pd.read_csv(patient_csv)
    inc = json.load(open(inclusion_file))
    exc = json.load(open(exclusion_file))

    # TODO: real matching engine
    df["eligible"] = df["age"] >= 18

    latency = time.time() - start
    st.session_state["matching_latency"] = latency

    out_path = os.path.join(study_path, "matches", "match_results.csv")
    df.to_csv(out_path, index=False)

    st.success(f"Matching completed in {latency:.2f} seconds.")
    st.dataframe(df.head())

if st.button("Continue → Review"):
    st.switch_page("pages/6_Review.py")
