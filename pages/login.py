"""
===========================================================
AI-Based Autonomous Academic Decision System

Streamlit Login Page
===========================================================
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
from auth import login


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(

    page_title="Academic Decision System",

    page_icon="🎓",

    layout="wide"

)


# ==========================================================
# TITLE
# ==========================================================

st.title("🎓 AI-Based Autonomous Academic Decision System")

st.subheader("User Login")


# ==========================================================
# USER ROLE
# ==========================================================

role = st.selectbox(

    "Login As",

    [

        "Student",

        "Faculty",

        "Admin"

    ]

)

st.divider()

st.write("New Student?")

if st.button("Register Here"):
    st.switch_page("pages/register.py")

# ==========================================================
# LOGIN FORM
# ==========================================================

with st.form("login_form"):

    username = st.text_input(
    "Enrollment Number"
    if role == "Student"
    else "College Email"
)

    password = st.text_input(

        "Password",

        type="password"

    )

    login_button = st.form_submit_button(

        "Login"

    )
# ==========================================================
# LOGIN AUTHENTICATION
# ==========================================================

if login_button:

    if username.strip() == "" or password.strip() == "":

        st.error("Please enter both username and password.")

    else:

        user = login(
                role,
                username,
                password
            )

        if user:

            # Store logged-in user in session
            st.session_state["user"] = user
            st.session_state["role"] = role

            st.success(f"Welcome {user['full_name']}!")

            # Redirect according to role
            if role == "Student":

                st.switch_page("pages/student_dashboard.py")

            elif role == "Faculty":

                st.switch_page("pages/faculty_dashboard.py")

            elif role == "Admin":

                st.switch_page("pages/admin_dashboard.py")


# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    "© 2026 AI-Based Autonomous Academic Decision System"
)