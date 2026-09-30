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
    get_pending_student_applications,
    approve_student,
    reject_student,
    get_pending_faculty_registrations,
    approve_faculty_registration,
    reject_faculty_registration,
    get_default_section_names,
    get_pending_faculty_teaching_requests,
    approve_faculty_teaching_request,
    reject_faculty_teaching_request,
    change_student_password,
    change_faculty_password,
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

admin = dict(st.session_state.user_data)



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
        "Student Approvals",
        "Faculty Registration Approvals",
        "Faculty Teaching Requests",
        "Students",
        "Faculty",
        "Add Student",
        "Add Faculty",
        "Reset Account Password",
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

elif menu == "Student Approvals":

    st.subheader("Pending Student Registrations")
    pending_students = get_pending_student_applications()
    st.metric("Pending applications", len(pending_students))

    if not pending_students:
        st.success("There are no student registrations awaiting approval.")
    else:
        confirm_bulk = st.checkbox(
            f"I reviewed all {len(pending_students)} applications and want to approve them all",
            key="confirm_bulk_student_approval"
        )
        if st.button(
            "Approve all pending registrations",
            disabled=not confirm_bulk,
            type="primary"
        ):
            admin_name = admin.get("username", admin.get("email", "Admin"))
            approved_count = sum(
                approve_student(row["student_id"], admin_name)
                for row in pending_students
            )
            st.success(f"Approved {approved_count} student registration(s).")
            st.rerun()

        for pending_student in pending_students:
            student_id = pending_student["student_id"]
            with st.expander(
                f"{pending_student['enrollment_no']} · {pending_student['full_name']}"
            ):
                st.write(f"**Department:** {pending_student['department']}")
                st.write(f"**Admission session:** {pending_student['admission_session']}")
                st.write(f"**Email:** {pending_student['email']}")
                reason = st.text_input(
                    "Rejection reason",
                    key=f"admin_rejection_reason_{student_id}"
                )
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button(
                        "Approve registration",
                        key=f"admin_approve_{student_id}",
                        use_container_width=True
                    ):
                        admin_name = admin.get("username", admin.get("email", "Admin"))
                        if approve_student(student_id, admin_name):
                            st.success("Registration approved.")
                            st.rerun()
                        st.error("This registration could not be approved.")
                with reject_col:
                    if st.button(
                        "Reject registration",
                        key=f"admin_reject_{student_id}",
                        use_container_width=True
                    ):
                        if not reason.strip():
                            st.warning("Enter a reason before rejecting.")
                        elif reject_student(
                            student_id,
                            reason.strip(),
                            admin.get("username", admin.get("email", "Admin"))
                        ):
                            st.success("Registration rejected.")
                            st.rerun()
                        else:
                            st.error("This registration could not be rejected.")

elif menu == "Faculty Registration Approvals":

    st.subheader("Pending Faculty Registrations")
    pending_faculty = get_pending_faculty_registrations()
    st.metric("Pending faculty registrations", len(pending_faculty))

    if not pending_faculty:
        st.success("There are no faculty registrations awaiting approval.")
    else:
        for pending in pending_faculty:
            faculty_id = pending["faculty_id"]
            with st.expander(
                f"{pending['employee_id']} · {pending['full_name']}"
            ):
                st.write(f"**Department:** {pending['department']}")
                st.write(f"**Email:** {pending['email']}")
                st.write(f"**Qualification:** {pending['qualification']}")
                st.write(f"**Experience:** {pending['experience']} years")
                st.write(f"**Designation:** {pending['designation']}")
                st.write("**Requested courses:**")
                for course in pending["requested_courses"]:
                    code = f"{course['course_code']} · " if course["course_code"] else ""
                    st.write(f"- {code}{course['course_name']}")

                year_col, semester_col, section_col = st.columns(3)
                with year_col:
                    assigned_year = st.selectbox(
                        "Assign year",
                        [1, 2, 3, 4],
                        key=f"faculty_year_{faculty_id}"
                    )
                with semester_col:
                    assigned_semester = st.selectbox(
                        "Assign semester",
                        list(range(1, 9)),
                        key=f"faculty_semester_{faculty_id}"
                    )
                section_options = get_default_section_names(
                    pending["department"],
                    assigned_year,
                    assigned_semester
                ) or ["A", "B", "C"]
                with section_col:
                    assigned_section = st.selectbox(
                        "Assign section",
                        section_options,
                        key=f"faculty_section_{faculty_id}"
                    )

                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button(
                        "Approve and assign",
                        key=f"approve_faculty_{faculty_id}",
                        use_container_width=True
                    ):
                        if approve_faculty_registration(
                            faculty_id,
                            assigned_section,
                            assigned_year,
                            assigned_semester
                        ):
                            st.success("Faculty account approved and assigned.")
                            st.rerun()
                        st.error("Faculty approval could not be completed.")
                with reject_col:
                    if st.button(
                        "Reject registration",
                        key=f"reject_faculty_{faculty_id}",
                        use_container_width=True
                    ):
                        if reject_faculty_registration(faculty_id):
                            st.success("Faculty registration rejected.")
                            st.rerun()
                        st.error("Faculty registration could not be rejected.")

elif menu == "Faculty Teaching Requests":

    st.subheader("Pending Teaching Schedule Requests")
    teaching_requests = get_pending_faculty_teaching_requests()
    st.metric("Pending requests", len(teaching_requests))
    if not teaching_requests:
        st.info("No teaching schedule requests are waiting for review.")
    else:
        for request in teaching_requests:
            with st.expander(
                f"{request['course_code']} · {request['course_name']} · "
                f"Section {request['section']} · {request['day']} {request['slot']}"
            ):
                st.write(f"**Faculty:** {request['faculty_name']} ({request['employee_id']})")
                st.write(f"**Department:** {request['department']}")
                st.write(f"**Year/Semester:** {request['year']} / {request['semester']}")
                st.write(f"**Academic batch:** {request['academic_batch']}")
                st.write(f"**Period:** {request['start_time']}–{request['end_time']}")
                st.write(f"**Room:** {request['room_number'] or 'Not specified'}")
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button(
                        "Approve timetable slot",
                        key=f"approve_teaching_{request['request_id']}",
                        use_container_width=True
                    ):
                        if approve_faculty_teaching_request(
                            request["request_id"],
                            admin.get("username", admin.get("email", "Admin"))
                        ):
                            st.success("Teaching slot approved and added to the timetable.")
                            st.rerun()
                        st.error("Slot conflicts with an existing section or faculty timetable entry.")
                with reject_col:
                    if st.button(
                        "Reject request",
                        key=f"reject_teaching_{request['request_id']}",
                        use_container_width=True
                    ):
                        reject_faculty_teaching_request(
                            request["request_id"],
                            admin.get("username", admin.get("email", "Admin"))
                        )
                        st.success("Teaching request rejected.")
                        st.rerun()


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

elif menu == "Reset Account Password":

    st.subheader("Reset Student or Faculty Password")
    st.info("Passwords are stored as secure hashes and cannot be viewed. Set a new password here instead.")

    account_type = st.radio(
        "Account type",
        ["Student", "Faculty"],
        horizontal=True
    )
    if account_type == "Student":
        accounts = get_all_students().to_dict("records")
        account_options = {
            f"{account['roll_number']} · {account['full_name']}": account["student_id"]
            for account in accounts
        }
    else:
        accounts = get_all_faculty()
        account_options = {
            f"{account['employee_id']} · {account['full_name']}": account["faculty_id"]
            for account in accounts
        }

    if account_options:
        selected_account = st.selectbox("Choose account", list(account_options))
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")

        if st.button("Reset password", type="primary"):
            if len(new_password) < 8:
                st.error("Use at least 8 characters for the new password.")
            elif new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                account_id = account_options[selected_account]
                if account_type == "Student":
                    updated = change_student_password(account_id, new_password)
                else:
                    updated = change_faculty_password(account_id, new_password)
                if updated:
                    st.success("Password reset successfully.")
                else:
                    st.error("The account could not be updated.")
    else:
        st.info(f"No {account_type.lower()} accounts are available.")

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

st.divider()

st.subheader("🎓 Student Management")

if st.button(
    "👨‍🎓 Student Registration Approvals",
    use_container_width=True
):
    st.switch_page("dashboard/student_approvals.py")

    
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

    st.rerun()


