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

    average_cgpa = students["cgpa"].mean()
    average_attendance = students["attendance_percentage"].mean()
    st.metric(
        "Average CGPA",
        round(average_cgpa, 2) if pd.notna(average_cgpa) else "Not recorded"
    )

    st.metric(
        "Average Attendance",
        round(average_attendance, 2) if pd.notna(average_attendance) else "Not recorded"
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