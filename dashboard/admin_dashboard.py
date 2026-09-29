"""
===========================================================
AI-Based Autonomous Academic Decision System

Admin Dashboard
===========================================================
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))   # Use insert instead of append

import streamlit as st
import pandas as pd

from auth import require_admin

from database import (
    get_all_students,
    get_all_faculty,
    get_student_by_roll,
    get_faculty_by_employee_id,
    update_faculty,
    add_student,
    add_faculty,
    update_student,
    delete_student,
    delete_faculty,
)
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🎓",
    layout="wide"
)
st.title("🎓 AI-Based Autonomous Academic Decision System")

st.subheader("Administrator Dashboard")
students = get_all_students()

faculty = get_all_faculty()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Students",
        len(students)
    )

with col2:
    st.metric(
        "Total Faculty",
        len(faculty)
    )


# ==========================================================
# LOGIN CHECK
# ==========================================================

require_admin()

admin = st.session_state.user_data



# ==========================================================
# HEADER
# ==========================================================

st.title("🛡️ Admin Dashboard")

st.success(f"Welcome {admin['full_name']}")

st.divider()

# ==========================================================
# MENU
# ==========================================================

menu = st.sidebar.selectbox(
    "Select Option",
    [
        "Dashboard",
        "Students",
        "Faculty",
        "Add Student",
        "Add Faculty",
        "Update Student",
        "Delete Student",
        "Update Faculty",
        "Delete Faculty",
        "Analytics",
        "Reports",
        "Settings"
    ]
)

# ==========================================================
# DASHBOARD
# ==========================================================

if menu == "Dashboard":

    students = get_all_students()
    faculty = get_all_faculty()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Students",
            len(students)
        )

    with col2:
        st.metric(
            "Total Faculty",
            len(faculty)
        )

    with col3:
        st.metric(
            "Departments",
            students["department"].nunique()
        )

    st.divider()

    st.subheader("Students Department-wise")

    department_count = (
        students.groupby("department")
        .size()
        .reset_index(name="Total Students")
    )

    st.dataframe(
        department_count,
        use_container_width=True
    )


# ==========================================================
# STUDENTS
# ==========================================================

elif menu == "Students":

    st.subheader("All Students")

    students = get_all_students()

    st.dataframe(
        students,
        use_container_width=True
    )


# ==========================================================
# FACULTY
# ==========================================================

elif menu == "Faculty":

    st.subheader("All Faculty")

    faculty = get_all_faculty()

    st.dataframe(
        faculty,
        use_container_width=True
    )

# ==========================================================
# ADD STUDENT
# ==========================================================

elif menu == "Add Student":

    st.subheader("Add New Student")

    full_name = st.text_input("Full Name")
    roll_number = st.text_input("Roll Number")
    department = st.text_input("Department")
    semester = st.number_input("Semester", 1, 8)
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    gender = st.selectbox(
    "Gender",
    ["Male", "Female", "Other"]
)
    password = st.text_input("Password", type="password")

    if st.button("Add Student"):

        add_student(
            roll_number,
            full_name,
            gender,
            department,
            semester,
            email,
            phone,
            password
        )

        st.success("Student Added Successfully.")


# ==========================================================
# ADD FACULTY
# ==========================================================

elif menu == "Add Faculty":

    st.subheader("Add New Faculty")

    full_name = st.text_input("Faculty Name")
    employee_id = st.text_input("Employee ID")
    department = st.text_input("Department")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    password = st.text_input("Password", type="password")

    if st.button("Add Faculty"):

        add_faculty(
            employee_id,
            full_name,
            department,
            email,
            phone,
            password
        )

        st.success("Faculty Added Successfully.")

# ==========================================================
# UPDATE FACULTY
# ==========================================================

elif menu == "Update Faculty":

    st.subheader("Update Faculty")

    employee_id = st.text_input("Enter Employee ID")

    if st.button("Search Faculty"):

        faculty = get_faculty_by_employee_id(employee_id)

        if faculty:
            st.session_state.faculty = faculty
        else:
            st.error("Faculty Not Found")

    if "faculty" in st.session_state:

        faculty = st.session_state.faculty

        full_name = st.text_input(
            "Full Name",
            value=faculty["full_name"]
        )

        department = st.text_input(
            "Department",
            value=faculty["department"]
        )

        email = st.text_input(
            "Email",
            value=faculty["email"]
        )

        phone = st.text_input(
            "Phone",
            value=faculty["phone"]
        )

        if st.button("Update Faculty"):

            update_faculty(
                faculty["faculty_id"],
                full_name,
                department,
                email,
                phone
            )

            del st.session_state.faculty

            st.success("Faculty Updated Successfully")



# ==========================================================
# DELETE FACULTY
# ==========================================================

elif menu == "Delete Faculty":

    st.subheader("Delete Faculty")

    employee_id = st.text_input("Enter Employee ID")

    if st.button("Search Faculty"):

        faculty = get_faculty_by_employee_id(employee_id)

        if faculty:
            st.session_state.delete_faculty = faculty
        else:
            st.error("Faculty Not Found")

    if "delete_faculty" in st.session_state:

        faculty = st.session_state.delete_faculty

        st.write("### Faculty Details")

        st.write(f"**Employee ID:** {faculty['employee_id']}")
        st.write(f"**Name:** {faculty['full_name']}")
        st.write(f"**Department:** {faculty['department']}")
        st.write(f"**Email:** {faculty['email']}")

        if st.button("Delete Faculty"):

            delete_faculty(
                faculty["faculty_id"]
            )

            del st.session_state.delete_faculty

            st.success("Faculty Deleted Successfully")


# ==========================================================
# UPDATE STUDENT
# ==========================================================

elif menu == "Update Student":

    st.subheader("Update Student")

    roll_number = st.text_input("Enter Roll Number")

    if st.button("Search Student"):

        student = get_student_by_roll(roll_number)

        if student:

            st.session_state.student = student

        else:

            st.error("Student not found.")

    if "student" in st.session_state:

        student = st.session_state.student

        full_name = st.text_input(
            "Full Name",
            value=student["full_name"]
        )

        gender = st.selectbox(
            "Gender",
            ["Male", "Female", "Other"]
        )

        department = st.text_input(
            "Department",
            value=student["department"]
        )

        semester = st.number_input(
            "Semester",
            1,
            8,
            value=student["semester"]
        )

        email = st.text_input(
            "Email",
            value=student["email"]
        )

        phone = st.text_input(
            "Phone",
            value=student["phone"]
        )

        if st.button("Update"):

            update_student(
                student["student_id"],
                full_name,
                gender,
                department,
                semester,
                email,
                phone
            )

            st.success("Student Updated Successfully.")

# ==========================================================
# DELETE STUDENT
# ==========================================================

elif menu == "Delete Student":

    st.subheader("Delete Student")

    roll_number = st.text_input("Enter Roll Number")

    if st.button("Search"):

        student = get_student_by_roll(roll_number)

        if student:

            st.session_state.delete_student = student

        else:

            st.error("Student Not Found")

    if "delete_student" in st.session_state:

        student = st.session_state.delete_student

        st.write("### Student Details")

        st.write(f"**Roll Number:** {student['roll_number']}")
        st.write(f"**Name:** {student['full_name']}")
        st.write(f"**Department:** {student['department']}")
        st.write(f"**Semester:** {student['semester']}")

        if st.button("Delete Student"):

            delete_student(
                student["student_id"]
            )

            del st.session_state.delete_student

            st.success("Student Deleted Successfully")


# ==========================================================
# LOGOUT
# ==========================================================

st.sidebar.divider()

if st.sidebar.button("Logout"):

    st.session_state.clear()

    st.switch_page("dashboard/login.py")


