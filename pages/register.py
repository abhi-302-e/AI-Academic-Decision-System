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
    create_email_verification,
    verify_email_otp,
)

# ---------------------------------------------------------
# EMAIL IMPORTS
# ---------------------------------------------------------
from email_service import (
    generate_otp,
    send_verification_otp,
    send_enrollment_email,
)

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="New Student Registration",
    page_icon="🎓",
    layout="wide"
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
defaults = {
    "registration_step": 1,
    "pending_student_id": None,
    "pending_email": None,
    "pending_enrollment_no": None,
    "registration_completed": False,
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
                "Gmail Address *",
                placeholder="example@gmail.com"
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
            "Create Student Account & Verify Gmail",
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
            errors.append("Please enter your Gmail address.")
        elif not email.lower().endswith("@gmail.com"):
            errors.append("Please enter a valid Gmail address.")

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
                    "This Gmail address may already be registered. "
                    "If you are already a student, please use your "
                    "Enrollment Number and Password to login."
                )

            else:

                student_id = student_result["student_id"]
                enrollment_no = student_result["enrollment_no"]

                # -------------------------------------------------
                # GENERATE OTP
                # -------------------------------------------------
                otp = generate_otp()

                # -------------------------------------------------
                # SAVE OTP
                # -------------------------------------------------
                create_email_verification(
                    student_id=student_id,
                    email=email.strip().lower(),
                    otp=otp
                )

                # -------------------------------------------------
                # SEND REAL GMAIL OTP
                # -------------------------------------------------
                try:

                    send_verification_otp(
                        to_email=email.strip().lower(),
                        otp=otp
                    )

                    # Save temporary information
                    st.session_state.pending_student_id = student_id
                    st.session_state.pending_email = email.strip().lower()
                    st.session_state.pending_enrollment_no = enrollment_no

                    st.session_state.student_data = {
                        "full_name": full_name.strip(),
                        "department": department,
                        "admission_year": admission_year,
                        "admission_session": admission_session,
                    }

                    st.session_state.registration_step = 2

                    st.success(
                        "Student account created successfully!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Student account was created, but the Gmail "
                        "verification email could not be sent."
                    )

                    st.warning(
                        "Please check your Gmail configuration and "
                        "EMAIL_APP_PASSWORD."
                    )

                    st.code(str(e))


# =========================================================
# STEP 2 — EMAIL VERIFICATION
# =========================================================
elif st.session_state.registration_step == 2:

    st.subheader("Step 2: Verify Your Gmail")

    st.write(
        f"A 6-digit verification code has been sent to "
        f"**{st.session_state.pending_email}**."
    )

    st.info(
        "Check your Gmail inbox and spam folder. "
        "The verification code is valid for 10 minutes."
    )

    st.markdown("---")

    otp = st.text_input(
        "Enter 6-Digit Verification Code",
        max_chars=6,
        placeholder="Enter OTP"
    )

    col1, col2 = st.columns(2)

    # ---------------------------------------------------------
    # VERIFY OTP
    # ---------------------------------------------------------
    with col1:

        if st.button(
            "✅ Verify Gmail",
            use_container_width=True
        ):

            if not otp.strip():

                st.error("Please enter the verification code.")

            elif len(otp.strip()) != 6 or not otp.strip().isdigit():

                st.error(
                    "Verification code must contain exactly 6 digits."
                )

            else:

                verified = verify_email_otp(
                    student_id=st.session_state.pending_student_id,
                    email=st.session_state.pending_email,
                    otp=otp.strip()
                )

                if verified:

                    # ---------------------------------------------
                    # SEND ENROLLMENT EMAIL
                    # ---------------------------------------------
                    try:

                        send_enrollment_email(
                            to_email=st.session_state.pending_email,
                            full_name=st.session_state.student_data[
                                "full_name"
                            ],
                            enrollment_no=st.session_state.pending_enrollment_no
                        )

                        email_sent = True

                    except Exception as e:

                        email_sent = False
                        st.warning(
                            "Gmail verified successfully, but the "
                            "Enrollment Number email could not be sent."
                        )

                        st.code(str(e))

                    st.session_state.registration_completed = True
                    st.session_state.registration_step = 3

                    st.success(
                        "Gmail verified successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid or expired verification code."
                    )

    # ---------------------------------------------------------
    # RESEND OTP
    # ---------------------------------------------------------
    with col2:

        if st.button(
            "🔄 Resend OTP",
            use_container_width=True
        ):

            new_otp = generate_otp()

            create_email_verification(
                student_id=st.session_state.pending_student_id,
                email=st.session_state.pending_email,
                otp=new_otp
            )

            try:

                send_verification_otp(
                    to_email=st.session_state.pending_email,
                    otp=new_otp
                )

                st.success(
                    "A new verification code has been sent to your Gmail."
                )

            except Exception as e:

                st.error(
                    "Unable to send the new verification code."
                )

                st.code(str(e))


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
        "Your Enrollment Number has also been sent to your Gmail."
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

    st.write(
        "You can now login using:"
    )

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
        st.session_state.pending_student_id = None
        st.session_state.pending_email = None
        st.session_state.pending_enrollment_no = None
        st.session_state.registration_completed = False
        st.session_state.student_data = {}

        st.switch_page("pages/login.py")


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

        st.switch_page("pages/login.py")