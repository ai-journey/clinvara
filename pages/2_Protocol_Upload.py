import streamlit as st
import os
import pdfplumber

st.title("Step 1: Upload Protocol")

if not st.session_state.get("current_study"):
    st.error("No study selected. Return to Study Selector.")
    st.stop()

study_path = st.session_state.study_path
protocol_dir = os.path.join(study_path, "protocol")
os.makedirs(protocol_dir, exist_ok=True)

uploaded = st.file_uploader("Upload Protocol PDF", type=["pdf"])

if uploaded:
    file_path = os.path.join(protocol_dir, "protocol.pdf")
    with open(file_path, "wb") as f:
        f.write(uploaded.read())
    st.session_state["protocol_path"] = file_path
    st.success("Protocol uploaded successfully.")

if st.button("Extract Text"):
    file_path = st.session_state.get("protocol_path") or os.path.join(protocol_dir, "protocol.pdf")
    if not file_path or not os.path.exists(file_path):
        st.error("No protocol PDF found. Please upload first.")
    else:
        try:
            text_pages = []
            with pdfplumber.open(file_path) as pdf:
                for p in pdf.pages:
                    page_text = p.extract_text() or ""
                    text_pages.append(page_text)

            full_text = "\n\n".join(text_pages)
            txt_path = os.path.join(protocol_dir, "protocol.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            st.success(f"Text extracted and saved to {txt_path}")
            st.session_state["protocol_text_path"] = txt_path
        except Exception as e:
            st.error(f"Failed to extract text: {e}")

if st.button("Continue → Criteria Extraction"):
    st.switch_page("pages/3_Criteria_Extraction.py")
