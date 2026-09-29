"""
===========================================================
AI-Based Autonomous Academic Decision System

Analytics Dashboard
===========================================================
"""

import streamlit as st
import pandas as pd

from auth import require_admin
from database import get_all_students

st.set_page_config(
    page_title="Analytics",
    page_icon="📊",
    layout="wide"
)

require_admin()

st.title("📊 Academic Analytics")

students = get_all_students()

if len(students) == 0:

    st.warning("No student records found.")

else:

    st.metric(
        "Total Students",
        len(students)
    )

    st.metric(
        "Average CGPA",
        round(students["cgpa"].mean(), 2)
    )

    st.metric(
        "Average Attendance",
        round(
            students["attendance_percentage"].mean(),
            2
        )
    )

    st.subheader("Department Wise Students")

    dept = (
        students.groupby("department")
        .size()
        .reset_index(name="Students")
    )

    st.bar_chart(
        dept.set_index("department")
    )

    st.subheader("Student Data")

    st.dataframe(
        students,
        use_container_width=True
    )