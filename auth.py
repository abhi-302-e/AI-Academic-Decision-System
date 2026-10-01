"""
===========================================================
AI-Based Autonomous Academic Decision System

Authentication Module
===========================================================
"""

import streamlit as st

from database import (
    admin_login,
    faculty_login,
    student_login,
    change_admin_password,
    change_faculty_password,
    change_student_password
)


# ==========================================================
# SESSION MANAGEMENT
# ==========================================================

def initialize_session():
    """
    Initialize Streamlit session state.
    """

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user_role" not in st.session_state:
        st.session_state.user_role = None

    if "user_data" not in st.session_state:
        st.session_state.user_data = None


# ==========================================================
# LOGIN
# ==========================================================
def login(role, username, password):

    if role == "Admin":
        user = admin_login(username, password)

    elif role == "Faculty":
        user = faculty_login(username, password)

    elif role == "Student":
        user = student_login(username, password)

    else:
        return None

    return user


# ==========================================================
# LOGOUT
# ==========================================================

def logout():

    st.session_state.logged_in = False

    st.session_state.user_role = None

    st.session_state.user_data = None


# ==========================================================
# LOGIN STATUS
# ==========================================================

def is_logged_in():

    initialize_session()

    return st.session_state.logged_in


def get_current_user():

    initialize_session()

    return st.session_state.user_data


def get_current_role():

    initialize_session()

    return st.session_state.user_role

# ==========================================================
# PASSWORD MANAGEMENT
# ==========================================================

def change_password(user_id, role, new_password):
    """
    Change password based on user role.
    """

    try:

        if role == "Admin":

            change_admin_password(
                user_id,
                new_password
            )

        elif role == "Faculty":

            change_faculty_password(
                user_id,
                new_password
            )

        elif role == "Student":

            change_student_password(
                user_id,
                new_password
            )

        else:

            return False

        return True

    except Exception as error:

        st.error(f"Password Change Failed: {error}")

        return False


# ==========================================================
# ROLE CHECK FUNCTIONS
# ==========================================================

def is_admin():
    """
    Check if logged-in user is an admin.
    """

    initialize_session()

    return (
        st.session_state.logged_in and
        st.session_state.user_role == "Admin"
    )


def is_faculty():
    """
    Check if logged-in user is faculty.
    """

    initialize_session()

    return (
        st.session_state.logged_in and
        st.session_state.user_role == "Faculty"
    )


def is_student():
    """
    Check if logged-in user is a student.
    """

    initialize_session()

    return (
        st.session_state.logged_in and
        st.session_state.user_role == "Student"
    )


# ==========================================================
# ACCESS CONTROL
# ==========================================================

def require_login():
    """
    Stop execution if user is not logged in.
    """

    if not is_logged_in():

        st.warning("Please login to continue.")

        st.stop()
        raise SystemExit(0)


def require_admin():
    """
    Allow only admin users.
    """

    require_login()

    if not is_admin():

        st.error("Access Denied! Admin Only.")

        st.stop()
        raise SystemExit(0)


def require_faculty():
    """
    Allow only faculty users.
    """

    require_login()

    if not is_faculty():

        st.error("Access Denied! Faculty Only.")

        st.stop()
        raise SystemExit(0)


def require_student():
    """
    Allow only student users.
    """

    require_login()

    if not is_student():

        st.error("Access Denied! Students Only.")

        st.stop()
        raise SystemExit(0)


# ==========================================================
# CURRENT USER INFORMATION
# ==========================================================

def get_current_user_name():
    """
    Return logged-in user's name.
    """

    user = get_current_user()

    if user:

        return user["full_name"]

    return ""


def get_current_user_id():
    """
    Return logged-in user's primary key.
    """

    user = get_current_user()

    role = get_current_role()

    if user is None:

        return None

    if role == "Admin":

        return user["admin_id"]

    elif role == "Faculty":

        return user["faculty_id"]

    elif role == "Student":

        return user["student_id"]

    return None

