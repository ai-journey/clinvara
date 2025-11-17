import streamlit as st
import os

st.set_page_config(
    page_title="Clinvara",
    layout="wide",
)

# Initialize session state
if "current_study" not in st.session_state:
    st.session_state["current_study"] = None

if "study_path" not in st.session_state:
    st.session_state["study_path"] = None

st.sidebar.title("Clinvara Navigation")

st.sidebar.write("Select a page from the left menu.")

st.title("Clinvara: Intelligent CRA Assistant")
st.write("Welcome to the Clinvara MVP!")
st.write("Use the sidebar to navigate through the workflow.")
