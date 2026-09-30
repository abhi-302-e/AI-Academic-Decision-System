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

require_admin()

st.title("📄 Reports")

students = get_all_students()

if len(students) == 0:

    st.warning("No records found.")

else:

    report_data = students.copy()
    for column in ("semester", "cgpa", "attendance_percentage"):
        report_data[column] = report_data[column].map(
            lambda value: "Not recorded" if pd.isna(value) else value
        )

    csv = report_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Student Report (CSV)",
        data=csv,
        file_name="students_report.csv",
        mime="text/csv"
    )

    st.caption("Not recorded means the academic office or faculty has not entered a value yet.")
    st.dataframe(
        report_data,
        use_container_width=True
    )