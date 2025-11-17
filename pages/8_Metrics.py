import streamlit as st
import pandas as pd
import numpy as np
import os
import json

st.title("Model Metrics & Explainability Dashboard")

# ---- Guard Clause: Check study selection ----
if "current_study" not in st.session_state or st.session_state.current_study is None:
    st.error("No study selected. Please return to the Study Selector.")
    st.stop()

study_path = st.session_state.study_path
match_results_path = os.path.join(study_path, "matches", "match_results.csv")

# ---- Guard Clause: Require matching ----
if not os.path.exists(match_results_path):
    st.error("No matching results found. Run Matching first.")
    st.stop()

# ---- Load match data ----
df = pd.read_csv(match_results_path)

st.subheader("📊 Performance Metrics")

# If no ground truth exists, we simulate "true labels" for demo purposes
# In actual use, you would provide ground truth labels or CRA-reviewed overrides
if "true_eligible" not in df.columns:
    st.info("No ground truth labels detected. Generating synthetic true labels for demo purposes.")
    df["true_eligible"] = df["eligible"]  # Treat model output as ground truth for MVP demo

# ---- Calculate metrics ----
tp = ((df["eligible"] == 1) & (df["true_eligible"] == 1)).sum()
fp = ((df["eligible"] == 1) & (df["true_eligible"] == 0)).sum()
tn = ((df["eligible"] == 0) & (df["true_eligible"] == 0)).sum()
fn = ((df["eligible"] == 0) & (df["true_eligible"] == 1)).sum()

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
accuracy = (tp + tn) / len(df) if len(df) > 0 else 0

# ---- Display in metrics cards ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Precision", f"{precision:.2f}")
col2.metric("Recall", f"{recall:.2f}")
col3.metric("F1 Score", f"{f1:.2f}")
col4.metric("Accuracy", f"{accuracy:.2f}")

# ---- Latency ----
st.subheader("⏱️ Runtime Metrics")

latency = st.session_state.get("matching_latency", None)
if latency:
    st.metric("Matching Runtime (sec)", f"{latency:.2f}")
else:
    st.info("No latency recorded in session_state.")

# ---- Criteria Failure Distribution ----
st.subheader("📉 Criteria Failure Breakdown")

failure_counts = {}

# For MVP, we simply approximate based on diagnosis_codes and labs
# In later versions, use actual rule evaluation logs
for idx, row in df.iterrows():
    if "diagnosis_codes" in row and isinstance(row["diagnosis_codes"], str):
        if "E11" not in row["diagnosis_codes"]:   # example logic for demo
            failure_counts["Missing diabetes diagnosis"] = failure_counts.get("Missing diabetes diagnosis", 0) + 1

    if "bmi" in row and row["bmi"] and row["bmi"] > 35:
        failure_counts["BMI > 35"] = failure_counts.get("BMI > 35", 0) + 1

    if "lab_hba1c_latest" in row and not pd.isna(row["lab_hba1c_latest"]) and row["lab_hba1c_latest"] > 8:
        failure_counts["HbA1c > 8"] = failure_counts.get("HbA1c > 8", 0) + 1

if failure_counts:
    st.bar_chart(pd.DataFrame.from_dict(failure_counts, orient="index", columns=["Failures"]))
else:
    st.write("No criteria failure data available.")

# ---- Bias Analysis ----
st.subheader("⚖️ Bias & Fairness Analysis")

if "gender" in df.columns:
    bias_df = df.groupby("gender")["eligible"].mean().reset_index()
    bias_df.columns = ["Gender", "Eligibility Rate"]
    st.dataframe(bias_df)
else:
    st.info("No gender column found for bias analysis.")

if "race" in df.columns:
    bias_df = df.groupby("race")["eligible"].mean().reset_index()
    bias_df.columns = ["Race", "Eligibility Rate"]
    st.dataframe(bias_df)
else:
    st.info("No race column found for bias analysis.")

# ---- Traceability Section ----
st.subheader("🔒 Traceability Metadata")

trace = {
    "Model Version": "1.0-MVP",
    "Criteria Version": "extracted_" + st.session_state.current_study,
    "Patient Dataset": "patients_flat.csv",
    "Match Run ID": "run_" + st.session_state.current_study,
}

st.json(trace)

# ---- Export Metrics ----
st.subheader("⬇️ Export Metrics as JSON")

export_data = {
    "precision": precision,
    "recall": recall,
    "f1_score": f1,
    "accuracy": accuracy,
    "latency": latency,
    "traceability": trace,
}

st.download_button(
    label="Download Metrics JSON",
    data=json.dumps(export_data, indent=2),
    file_name="clinvara_metrics.json",
    mime="application/json"
)
