import streamlit as st
import os

st.title("Study Selector")

BASE_DIR = "studies"
os.makedirs(BASE_DIR, exist_ok=True)

# Create Study
st.header("Create New Study")
study_name = st.text_input("Study Name")

if st.button("Create Study"):
    path = os.path.join(BASE_DIR, study_name)
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(os.path.join(path, "protocol"))
        os.makedirs(os.path.join(path, "criteria"))
        os.makedirs(os.path.join(path, "patients"))
        os.makedirs(os.path.join(path, "matches"))
        os.makedirs(os.path.join(path, "exports"))
        st.success(f"Study '{study_name}' created!")
    else:
        st.error("Study already exists.")

# List Studies
st.header("Existing Studies")

studies = os.listdir(BASE_DIR)

for s in studies:
    if st.button(f"Open: {s}"):
        st.session_state.current_study = s
        st.session_state.study_path = os.path.join(BASE_DIR, s)
        st.switch_page("pages/2_Protocol_Upload.py")
