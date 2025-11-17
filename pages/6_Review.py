import streamlit as st
import pandas as pd
import os

st.title("Step 5: Review & Validate Matches")

study_path = st.session_state.study_path
match_path = os.path.join(study_path, "matches", "match_results.csv")

df = pd.read_csv(match_path)

st.dataframe(df)

if st.button("Continue → Export"):
    st.switch_page("pages/7_Export.py")
