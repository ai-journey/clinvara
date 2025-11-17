import streamlit as st
import pandas as pd
import os

st.title("Step 6: Export Results")

study_path = st.session_state.study_path
match_path = os.path.join(study_path, "matches", "match_results.csv")

df = pd.read_csv(match_path)

st.download_button(
    label="Download Match Results (CSV)",
    data=df.to_csv(index=False),
    file_name="match_results.csv",
    mime="text/csv"
)
