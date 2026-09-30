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
from database import (
    get_published_semester_structures,
    get_courses_for_semester_structure,
    get_student_registration_for_structure,
    get_section_capacity,
    register_student_for_semester,
    get_student_registered_courses,
    get_student_notifications,
    mark_student_notifications_read,
)

# ==========================================================
# LOGIN CHECK
# ==========================================================

require_student()
student = dict(st.session_state.user_data)


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

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

    semester_value = student.get("semester")
    st.write(
        "**Semester:**",
        semester_value if semester_value else "Not registered"
    )
    st.write("**Section:**", student.get("section") or "Not assigned")

with col2:

    st.write("**Email:**", student["email"])

    st.write("**CGPA:**", student["cgpa"])

    st.write("**Attendance:**", f"{student['attendance_percentage']}%")
# ==========================================================
# SEMESTER REGISTRATION AND COURSES
# ==========================================================

st.subheader("📚 Semester Registration")
published_structures = get_published_semester_structures(
    student["department"],
    int(student.get("current_year") or 1)
)

if not published_structures:
    st.info("No published course structure is available for your department and year yet. Contact the academic office.")
else:
    structure_options = {
        (
            f"Year {structure['year']} · Semester {structure['semester']} · "
            f"{structure['academic_batch']}"
        ): structure
        for structure in published_structures
    }
    selected_label = st.selectbox("Available semester", list(structure_options))
    selected_structure = structure_options[selected_label]
    structure_courses = get_courses_for_semester_structure(
        selected_structure["structure_id"]
    )

    if not structure_courses:
        st.warning("This published semester does not contain active courses yet. Contact the academic office.")
    else:
        course_data = [
            {
                "Course Code": course["course_code"],
                "Course Name": course["course_name"],
                "Credits": course["credits"],
                "Course Type": course["course_type"],
            }
            for course in structure_courses
        ]
        st.dataframe(pd.DataFrame(course_data), use_container_width=True, hide_index=True)
        st.caption(f"Total credits: {sum(course['credits'] or 0 for course in structure_courses)}")

        registration = get_student_registration_for_structure(
            student["student_id"],
            selected_structure["structure_id"]
        )
        if registration:
            st.success(f"You are registered for this semester in Section {registration['section']}.")
        else:
            section_capacity = get_section_capacity(
                selected_structure["structure_id"]
            )
            available_sections = [
                item for item in section_capacity if item["available"] > 0
            ]
            if not available_sections:
                st.error("All sections are full. Contact the academic office.")
            else:
                section_options = {
                    f"Section {item['section']} · {item['available']} seats available": item["section"]
                    for item in available_sections
                }
                selected_section_label = st.selectbox(
                    "Choose a section",
                    list(section_options),
                    key=f"section_choice_{selected_structure['structure_id']}"
                )
                st.info("Payment details are simulated for this project. No real payment information or charge is collected.")
                payment_acknowledged = st.checkbox(
                    "I understand this is a simulated payment step",
                    key=f"demo_payment_ack_{selected_structure['structure_id']}"
                )
                if st.button(
                    "Register for this semester",
                    type="primary",
                    disabled=not payment_acknowledged
                ):
                    selected_section = section_options[selected_section_label]
                    registration_id = register_student_for_semester(
                        student["student_id"],
                        selected_structure["structure_id"],
                        selected_structure["academic_batch"],
                        selected_structure["semester"],
                        [course["course_id"] for course in structure_courses],
                        selected_section
                    )
                    if registration_id:
                        student["semester"] = selected_structure["semester"]
                        student["section"] = selected_section
                        st.session_state.user_data = student
                        st.session_state.user = student
                        st.success("Semester registration completed.")
                        st.rerun()
                    else:
                        st.error("Registration could not be completed. Refresh and try again, or contact the academic office.")

st.subheader("My Registered Courses")
registered_courses = get_student_registered_courses(student["student_id"])
if registered_courses:
    st.dataframe(
        pd.DataFrame([
            {
                "Academic Year": course["academic_year"],
                "Semester": course["semester"],
                "Course Code": course["course_code"],
                "Course Name": course["course_name"],
                "Credits": course["credits"],
                "Course Type": course["course_type"],
            }
            for course in registered_courses
        ]),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("You have not registered for any semester courses yet.")
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
# STUDENT NOTIFICATIONS
# ==========================================================

st.divider()
st.subheader("Notifications")
notifications = get_student_notifications(student["student_id"])
unread_count = sum(not notification["is_read"] for notification in notifications)

if notifications:
    st.caption(f"{unread_count} unread")
    for notification in notifications:
        with st.container(border=True):
            st.markdown(f"**{notification['title']}**")
            st.caption(notification["created_at"])
            st.write(notification["message"])

    if unread_count and st.button("Mark all as read"):
        mark_student_notifications_read(student["student_id"])
        st.rerun()
else:
    st.info("No academic updates yet. Faculty updates and AI recommendations will appear here.")


# ==========================================================
# LOGOUT
# ==========================================================

st.divider()

if st.button("Logout"):

    st.session_state.clear()
    st.rerun()

