import streamlit as st
import os
import shutil

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


# Delete study (safe, requires explicit name confirmation)
st.header("Delete Study")
if studies:
    del_choice = st.selectbox("Select study to delete", studies, key="delete_choice")
    st.write("Type the study name exactly to confirm deletion:")
    confirm_name = st.text_input("Confirm study name", key="delete_confirm")

    if st.button("Delete Study"):
        if not confirm_name:
            st.error("Please type the study name to confirm deletion.")
        elif confirm_name != del_choice:
            st.error("Confirmation name does not match the selected study.")
        else:
            path = os.path.join(BASE_DIR, del_choice)
            # Safety: ensure path is inside BASE_DIR
            abs_base = os.path.abspath(BASE_DIR)
            abs_path = os.path.abspath(path)
            if not abs_path.startswith(abs_base):
                st.error("Refusing to delete path outside the studies directory.")
            else:
                try:
                    shutil.rmtree(path)
                    st.success(f"Study '{del_choice}' deleted.")
                    # Clear session_state if it referenced the deleted study
                    if st.session_state.get("current_study") == del_choice:
                        st.session_state["current_study"] = None
                        st.session_state["study_path"] = None
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to delete study: {e}")
else:
    st.write("No studies available to delete.")
