"""
===========================================================
AI-Based Autonomous Academic Decision System

Reports
===========================================================
"""

import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
import pandas as pd
from auth import require_admin
from database import get_all_students

st.set_page_config(
    page_title="Reports",
    page_icon="📄",
    layout="wide"
)

require_admin()

st.title("📄 Reports")

students = get_all_students()

if len(students) == 0:

    st.warning("No records found.")

else:

    csv = students.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Student Report (CSV)",
        data=csv,
        file_name="students_report.csv",
        mime="text/csv"
    )

    st.dataframe(
        students,
        use_container_width=True
    )