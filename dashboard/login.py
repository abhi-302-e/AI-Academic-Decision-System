"""
===========================================================
AI-Based Autonomous Academic Decision System

Streamlit Login Page
===========================================================
"""
import streamlit as st
import streamlit.components.v1 as components
from auth import login

brand, sign_in = st.columns([1, 1], gap="large", vertical_alignment="center")

with brand:
    st.markdown("### Academic Decision System")
    st.title("Your academic workspace")
    st.write("Student progress, faculty support, and institutional decisions in one place.")
    st.markdown("**STUDENT · FACULTY · ADMINISTRATION**")

with sign_in:
    st.subheader("Sign in")

    role = st.radio(
        "Choose your portal",
        ["Student", "Faculty", "Admin"],
        horizontal=True,
        key="login_role"
    )

    if role == "Student":
        username_label = "Enrollment Number / Roll Number"
        username_placeholder = "e.g. 26STU0001, 1, or student"
    elif role == "Faculty":
        username_label = "Employee ID"
        username_placeholder = "e.g. SCHED0001"
    else:
        username_label = "Admin Username"
        username_placeholder = "e.g. admin"

    with st.form("login_form"):
        username = st.text_input(username_label, placeholder=username_placeholder)
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Continue", use_container_width=True)

    if login_button:
        if not username.strip() or not password:
            st.error("Enter your account name and password.")
        else:
            user = login(role, username.strip(), password)
            if user:
                st.session_state.update({
                    "logged_in": True,
                    "user_role": role,
                    "user_data": user,
                    "user": user,
                    "role": role,
                    "just_logged_in": True,
                })
                st.rerun()
            else:
                st.error("The account details are incorrect or the account is not active.")

    st.markdown("---")
    if role == "Student":
        if st.button("Forgot student password?", use_container_width=True):
            st.switch_page("dashboard/password_reset.py")
        st.write("New student?")
        if st.button("Create a student account", use_container_width=True):
            st.switch_page("dashboard/register.py")
    elif role == "Faculty":
        if st.button("Forgot faculty password?", use_container_width=True):
            st.switch_page("dashboard/password_reset.py")
        st.write("New faculty member?")
        if st.button("Register as faculty", use_container_width=True):
            st.switch_page("dashboard/faculty_register.py")