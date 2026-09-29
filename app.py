"""
===========================================================
AI-Based Autonomous Academic Decision System

Main Application
===========================================================
"""

import streamlit as st

st.set_page_config(
    page_title="AI Academic Decision System",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI-Based Autonomous Academic Decision System")

st.markdown("""
### Welcome

This system provides:

- 👨‍🎓 Student Portal
- 👨‍🏫 Faculty Portal
- 👨‍💼 Admin Portal
- 🤖 AI-Based Performance Prediction
- 📊 Academic Analytics
- 📄 Reports
""")

st.divider()

st.info("Click the button below to continue.")

if st.button("Go to Login"):
    st.switch_page("pages/login.py")