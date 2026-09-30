import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# DATABASE IMPORTS
# ---------------------------------------------------------
from database import (
    create_new_student_account,
)

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
defaults = {
    "registration_step": 1,
    "pending_enrollment_no": None,
    "student_data": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("🎓 New Student Registration")

st.info(
    "This registration is only for students who are joining the university "
    "for the first time. Existing students should use their permanent "
    "Enrollment Number and Password to login."
)

st.divider()


# =========================================================
# STEP 1 — NEW STUDENT DETAILS
# =========================================================
if st.session_state.registration_step == 1:

    st.subheader("Step 1: Student Admission Details")

    st.markdown(
        "Please enter your personal, contact and admission information."
    )

    with st.form("new_student_registration_form"):

        col1, col2 = st.columns(2)

        with col1:

            full_name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name"
            )

            date_of_birth = st.date_input(
                "Date of Birth *",
                value=None,
                min_value=datetime(1980, 1, 1).date(),
                max_value=datetime.now().date()
            )

            gender = st.selectbox(
                "Gender *",
                [
                    "Male",
                    "Female",
                    "Other"
                ]
            )

            father_name = st.text_input(
                "Father's Name *",
                placeholder="Enter father's name"
            )

            mother_name = st.text_input(
                "Mother's Name *",
                placeholder="Enter mother's name"
            )

            phone = st.text_input(
                "Mobile Number *",
                placeholder="Enter mobile number"
            )

        with col2:

            department = st.selectbox(
                "Department *",
                [
                    "Computer Science and Engineering",
                    "Artificial Intelligence and Machine Learning",
                    "AI and Data Science",
                    "Information Technology",
                    "Electronics and Communication Engineering",
                    "Electrical and Electronics Engineering",
                    "Mechanical Engineering",
                    "Civil Engineering"
                ]
            )

            admission_year = st.selectbox(
                "Admission Year *",
                list(range(datetime.now().year, datetime.now().year - 4, -1))
            )

            admission_session = f"{admission_year}-{str(admission_year + 1)[-2:]}"

            st.text_input(
                "Admission Session",
                value=admission_session,
                disabled=True
            )

            email = st.text_input(
                "Email Address *",
                placeholder="name@example.com"
            )

            address = st.text_area(
                "Permanent Address *",
                placeholder="Enter your complete address"
            )

            password = st.text_input(
                "Create Password *",
                type="password",
                placeholder="Create your password"
            )

            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Re-enter your password"
            )

        st.markdown("---")

        st.caption("* Required fields")

        submitted = st.form_submit_button(
            "Submit Registration",
            use_container_width=True
        )

    # -----------------------------------------------------
    # FORM VALIDATION
    # -----------------------------------------------------
    if submitted:

        errors = []

        if not full_name.strip():
            errors.append("Please enter your full name.")

        if not father_name.strip():
            errors.append("Please enter father's name.")

        if not mother_name.strip():
            errors.append("Please enter mother's name.")

        if not phone.strip():
            errors.append("Please enter your mobile number.")

        if not address.strip():
            errors.append("Please enter your permanent address.")

        if not email.strip():
            errors.append("Please enter your email address.")

        if not password:
            errors.append("Please create a password.")
        elif len(password) < 6:
            errors.append("Password must contain at least 6 characters.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if date_of_birth is None:
            errors.append("Please select your date of birth.")

        # -------------------------------------------------
        # SHOW VALIDATION ERRORS
        # -------------------------------------------------
        if errors:

            for error in errors:
                st.error(error)

        else:

            # -------------------------------------------------
            # CREATE PERMANENT STUDENT ACCOUNT
            # -------------------------------------------------
            student_result = create_new_student_account(
                full_name=full_name.strip(),
                date_of_birth=date_of_birth.isoformat(),
                gender=gender,
                father_name=father_name.strip(),
                mother_name=mother_name.strip(),
                address=address.strip(),
                department=department,
                admission_year=admission_year,
                admission_session=admission_session,
                email=email.strip().lower(),
                phone=phone.strip(),
                password=password,
            )

            # -------------------------------------------------
            # ACCOUNT CREATION FAILED
            # -------------------------------------------------
            if student_result is None:

                st.error(
                    "This email address may already be registered. "
                    "If you are already a student, please use your "
                    "Enrollment Number and Password to login."
                )

            else:

                enrollment_no = student_result["enrollment_no"]
                st.session_state.pending_enrollment_no = enrollment_no
                st.session_state.student_data = {
                    "full_name": full_name.strip(),
                    "department": department,
                    "admission_year": admission_year,
                    "admission_session": admission_session,
                }
                st.session_state.registration_step = 3
                st.rerun()


# =========================================================
# STEP 3 — REGISTRATION COMPLETED
# =========================================================
elif st.session_state.registration_step == 3:

    st.success("🎉 Student Registration Completed Successfully!")

    st.balloons()

    st.subheader("Your Permanent Enrollment Number")

    st.markdown(
        f"""
        <div style="
            padding: 25px;
            border-radius: 12px;
            border: 2px solid #4CAF50;
            text-align: center;
            margin: 20px 0;
        ">
            <h2>Enrollment Number</h2>
            <h1>{st.session_state.pending_enrollment_no}</h1>
            <p>This Enrollment Number is permanent and will remain
            the same throughout your degree.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Your registration is waiting for administrator approval. "
        "You can sign in after it has been approved."
    )

    st.markdown("### Student Information")

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Name:** "
            f"{st.session_state.student_data.get('full_name', '')}"
        )

        st.write(
            f"**Department:** "
            f"{st.session_state.student_data.get('department', '')}"
        )

    with col2:

        st.write(
            f"**Admission Year:** "
            f"{st.session_state.student_data.get('admission_year', '')}"
        )

        st.write(
            f"**Admission Session:** "
            f"{st.session_state.student_data.get('admission_session', '')}"
        )

    st.markdown("---")

    st.write("After approval, log in using:")

    st.markdown(
        f"""
        **Enrollment Number:** `{st.session_state.pending_enrollment_no}`

        **Password:** The password you created during registration.
        """
    )

    st.warning(
        "Do not share your Enrollment Number or Password with anyone."
    )

    if st.button(
        "🔐 Go to Student Login",
        use_container_width=True
    ):

        # Clear registration session data
        st.session_state.registration_step = 1
        st.session_state.pending_enrollment_no = None
        st.session_state.student_data = {}

        st.switch_page("dashboard/login.py")


# =========================================================
# FOOTER / LOGIN LINK
# =========================================================
st.divider()

if st.session_state.registration_step != 3:

    st.caption(
        "Already registered? Use your permanent Enrollment Number "
        "and Password to login."
    )

    if st.button(
        "← Back to Login"
    ):

        st.switch_page("dashboard/login.py")