"""Faculty self-registration for administrator approval."""

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import get_active_courses, register_faculty


DEPARTMENTS = [
    "Computer Science and Engineering",
    "Artificial Intelligence and Machine Learning",
    "AI and Data Science",
    "Information Technology",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
]

st.title("Faculty Registration")
st.write("Submit your profile and the courses you are qualified to teach.")
st.info("Your account will be available after an administrator approves your registration and assigns your section.")

active_courses = get_active_courses()
course_options = {
    f"{course['course_code']} · {course['course_name']}": course
    for course in active_courses
}
department_options = sorted({course["department"] for course in active_courses}) or DEPARTMENTS

with st.form("faculty_registration_form"):
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full name *")
        employee_id = st.text_input("Employee ID *")
        department = st.selectbox("Department *", department_options)
        email = st.text_input("Work email *")
        phone = st.text_input("Phone number *")
    with col2:
        qualification = st.text_input("Highest qualification *", placeholder="e.g. M.Sc. Computer Science")
        experience = st.number_input("Teaching experience (years) *", min_value=0, max_value=60, value=0)
        designation = st.selectbox(
            "Designation *",
            ["Lecturer", "Assistant Professor", "Associate Professor", "Professor"],
        )
        password = st.text_input("Create password *", type="password")
        confirm_password = st.text_input("Confirm password *", type="password")

    if course_options:
        selected_course_labels = st.multiselect(
            "Courses you are qualified to teach *",
            options=list(course_options),
        )
        requested_course_text = ""
    else:
        selected_course_labels = []
        requested_course_text = st.text_area(
            "Courses you are qualified to teach *",
            placeholder="Enter one course name or code per line",
            help="The course catalog is empty. You can enter your requested courses here until the catalog is populated.",
        )

    submitted = st.form_submit_button("Submit faculty registration", type="primary", use_container_width=True)

if submitted:
    errors = []
    if not full_name.strip():
        errors.append("Enter your full name.")
    if not employee_id.strip():
        errors.append("Enter your employee ID.")
    if not email.strip() or "@" not in email:
        errors.append("Enter a valid email address.")
    if not phone.strip():
        errors.append("Enter your phone number.")
    if not qualification.strip():
        errors.append("Enter your highest qualification.")
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters.")
    if password != confirm_password:
        errors.append("Passwords do not match.")

    if course_options:
        requested_courses = [
            {
                "course_code": course_options[label]["course_code"],
                "course_name": course_options[label]["course_name"],
            }
            for label in selected_course_labels
        ]
    else:
        requested_courses = [
            {"course_code": None, "course_name": line.strip()}
            for line in requested_course_text.splitlines()
            if line.strip()
        ]

    if not requested_courses:
        errors.append("Select or enter at least one course.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        faculty_id = register_faculty(
            employee_id=employee_id,
            full_name=full_name,
            department=department,
            email=email,
            phone=phone,
            password=password,
            qualification=qualification,
            experience=int(experience),
            designation=designation,
            courses=requested_courses,
        )
        if faculty_id is None:
            st.error("That employee ID or email is already registered.")
        else:
            st.success("Registration submitted. An administrator must approve your account and assign your section before you can sign in.")
            st.info(f"Employee ID: {employee_id.strip()}")

st.divider()
if st.button("Back to sign in"):
    st.switch_page("dashboard/login.py")