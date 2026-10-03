"""Application entry point and role-aware page navigation."""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from database import (
    initialize_database,
    upgrade_student_registration_system,
    upgrade_student_approval_system,
    ensure_default_admin,
    get_connection,
)

ROOT_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Academic Decision System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

stylesheet = ROOT_DIR / "assets" / "style.css"
if stylesheet.exists():
    st.markdown(
        f"<style>{stylesheet.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )


@st.cache_resource
def initialize_app_database(schema_revision):
    initialize_database()
    upgrade_student_registration_system()
    upgrade_student_approval_system()
    ensure_default_admin()


connection = get_connection()
has_student_table = connection.execute(
    """
    SELECT 1 FROM sqlite_master
    WHERE type = 'table' AND name = 'students'
    """
).fetchone() is not None
connection.close()

if not has_student_table:
    initialize_app_database.clear()

initialize_app_database("credentials-update-v2")

role = st.session_state.get("role")

if role == "Student":
    pages = [
        st.Page("dashboard/student_dashboard.py", title="Student Dashboard", icon="🎓", default=True)
    ]
elif role == "Faculty":
    pages = [
        st.Page("dashboard/faculty_dashboard.py", title="Faculty Dashboard", icon="👨‍🏫", default=True)
    ]
elif role == "Admin":
    pages = {
        "Administration": [
            st.Page("dashboard/admin_dashboard.py", title="Admin Dashboard", icon="🛡️", default=True),
            st.Page("dashboard/student_approvals.py", title="Student Approvals", icon="📋"),
            st.Page("dashboard/analytics.py", title="Analytics", icon="📊"),
            st.Page("dashboard/reports.py", title="Reports", icon="📄"),
            st.Page("dashboard/course_management.py", title="Course Management", icon="📚"),
        ]
    }
else:
    pages = [
        st.Page("dashboard/login.py", title="Sign in", icon="🔐", default=True),
        st.Page("dashboard/register.py", title="Student Registration", icon="📝"),
        st.Page("dashboard/faculty_register.py", title="Faculty Registration", icon="👨‍🏫"),
        st.Page("dashboard/password_reset.py", title="Reset Password", icon="🔑"),
    ]

st.navigation(pages, position="sidebar").run()