"""
===========================================================
AI-Based Autonomous Academic Decision System

Student Dashboard
===========================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd

from auth import require_student
from prediction import predict_student
from recommendation_engine import generate_recommendation
from database import get_student_registered_courses

# ==========================================================
# LOGIN CHECK
# ==========================================================

if "logged_in" not in st.session_state:

    st.error("Please login first.")

    st.stop()


if st.session_state["role"] != "Student":

    st.error("Access Denied.")

    st.stop()


student = st.session_state["user"]


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(

    page_title="Student Dashboard",

    page_icon="🎓",

    layout="wide"

)


# ==========================================================
# HEADER
# ==========================================================

st.title("🎓 Student Dashboard")

st.success(f"Welcome {student['full_name']}")


# ==========================================================
# PROFILE INFORMATION
# ==========================================================

st.subheader("Student Profile")

col1, col2 = st.columns(2)

with col1:

    st.write("**Roll Number:**", student["roll_number"])

    st.write("**Department:**", student["department"])

    st.write("**Semester:**", student["semester"])

with col2:

    st.write("**Email:**", student["email"])

    st.write("**CGPA:**", student["cgpa"])

    st.write("**Attendance:**", f"{student['attendance_percentage']}%")
# ==========================================================
# MY SEMESTER COURSES
# ==========================================================

st.subheader("📚 My Semester Courses")

registered_courses = get_student_registered_courses(
    student["student_id"],
    student["semester"]
)

if registered_courses:

    course_data = []

    for course in registered_courses:

        course_data.append({
            "Course Code": course["course_code"],
            "Course Name": course["course_name"],
            "Credits": course["credits"],
            "Course Type": course["course_type"]
        })

    courses_df = pd.DataFrame(course_data)

    st.dataframe(
        courses_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No semester courses have been registered yet."
    )
# ==========================================================
# ACADEMIC PERFORMANCE
# ==========================================================

st.subheader("Academic Performance")

marks = pd.DataFrame({

    "Assessment": [

        "Assignment",

        "Quiz",

        "Mid Exam",

        "End Semester",

        "Lab"

    ],

    "Marks": [

        student["assignment_marks"],

        student["quiz_marks"],

        student["mid_exam_marks"],

        student["end_sem_marks"],

        student["lab_marks"]

    ]

})

st.dataframe(
    marks,
    use_container_width=True
)


# ==========================================================
# AI PREDICTION
# ==========================================================

st.subheader("AI Prediction")

prediction = predict_student(student)

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

st.subheader("AI Recommendations")

result = generate_recommendation(student)

for recommendation in result["recommendations"]:

    st.success(f"✓ {recommendation}")


# ==========================================================
# LOGOUT
# ==========================================================

st.divider()

if st.button("Logout"):

    st.session_state.clear()

    st.switch_page("dashboard/login.py")

