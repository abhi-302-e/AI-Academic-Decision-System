"""
===========================================================
AI-Based Autonomous Academic Decision System

Faculty Dashboard
===========================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))   # Use insert instead of append

import streamlit as st
import pandas as pd

from auth import require_faculty
from database import (
    get_all_students,
    get_student_by_roll_number,
    update_student_marks,
    update_student_attendance,
    get_faculty_by_employee_id,
    update_faculty
)

from prediction import predict_student
from recommendation_engine import generate_recommendation


# ==========================================================
# LOGIN CHECK
# ==========================================================

require_faculty()

faculty = st.session_state.user_data


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(

    page_title="Faculty Dashboard",

    page_icon="👨‍🏫",

    layout="wide"

)


# ==========================================================
# HEADER
# ==========================================================

st.title("👨‍🏫 Faculty Dashboard")

st.success(f"Welcome {faculty['full_name']}")


# ==========================================================
# STUDENT SEARCH
# ==========================================================

st.subheader("Search Student")

students = get_all_students()

roll_numbers = students["roll_number"].tolist()

selected_roll = st.selectbox(

    "Select Roll Number",

    roll_numbers

)

student = get_student_by_roll_number(

    selected_roll

)

# ==========================================================
# DISPLAY STUDENT DETAILS
# ==========================================================

if student:

    st.subheader("Student Information")

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Name:**", student["full_name"])
        st.write("**Roll Number:**", student["roll_number"])
        st.write("**Department:**", student["department"])
        st.write("**Semester:**", student["semester"])

    with col2:

        st.write("**Email:**", student["email"])
        st.write("**CGPA:**", student["cgpa"])
        st.write("**Attendance:**", f"{student['attendance_percentage']}%")


    st.divider()


# ==========================================================
# EDIT MARKS
# ==========================================================

    st.subheader("Update Student Marks")

    assignment = st.number_input(
        "Assignment Marks",
        0.0,
        100.0,
        float(student["assignment_marks"])
    )

    quiz = st.number_input(
        "Quiz Marks",
        0.0,
        100.0,
        float(student["quiz_marks"])
    )

    mid = st.number_input(
        "Mid Exam Marks",
        0.0,
        100.0,
        float(student["mid_exam_marks"])
    )

    end = st.number_input(
        "End Semester Marks",
        0.0,
        100.0,
        float(student["end_sem_marks"])
    )

    lab = st.number_input(
        "Lab Marks",
        0.0,
        100.0,
        float(student["lab_marks"])
    )

    attendance = st.number_input(
        "Attendance %",
        0.0,
        100.0,
        float(student["attendance_percentage"])
    )


# ==========================================================
# AI PREDICTION
# ==========================================================

    prediction = predict_student(student)

    st.subheader("AI Prediction")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Performance",
            prediction["performance_prediction"]
        )

    with col2:

        st.metric(
            "Risk Level",
            prediction["risk_level"]
        )


# ==========================================================
# AI RECOMMENDATIONS
# ==========================================================

    st.subheader("Recommendations")

    result = generate_recommendation(student)

    for recommendation in result["recommendations"]:

        st.info(recommendation)


# ==========================================================
# SAVE BUTTON
# ==========================================================

if st.button("Save Changes"):

    update_student_marks(
        student["student_id"],
        assignment,
        quiz,
        mid,
        end,
        lab
    )

    update_student_attendance(
        student["student_id"],
        attendance
    )

    st.success("Student record updated successfully.")


# ==========================================================
# LOGOUT
# ==========================================================

st.divider()

if st.button("Logout"):

    st.session_state.clear()

    st.switch_page("dashboard/login.py")

