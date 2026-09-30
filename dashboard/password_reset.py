"""Reset student or faculty passwords using registered-phone SMS OTP."""

import sys
import secrets
import time
from pathlib import Path

import bcrypt
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import (
    change_faculty_password,
    change_student_password,
    create_student_notification,
    get_password_reset_account,
)
from email_service import send_email
from sms_service import send_password_reset_sms


st.title("Reset Password")
st.write("A one-time code will be sent to the email and mobile number registered to your active account.")

if "password_reset_target" not in st.session_state:
    st.session_state.password_reset_target = None

target = st.session_state.password_reset_target

if target is None:
    with st.form("request_password_reset_code"):
        role = st.selectbox("Account type", ["Student", "Faculty"])
        identifier = st.text_input(
            "Enrollment number" if role == "Student" else "Employee ID"
        )
        phone = st.text_input("Registered mobile number", placeholder="10-digit number")
        request_code = st.form_submit_button("Send verification code", type="primary")

    if request_code:
        account = get_password_reset_account(role, identifier, phone)
        if account is None:
            st.error("If the account details and registered mobile number match, a verification code can be sent.")
        else:
            code = f"{secrets.randbelow(1_000_000):06d}"
            sms_sent = False
            email_sent = False
            try:
                sms_sent = send_password_reset_sms(account["phone"], code)
            except Exception:
                pass
            try:
                if account["email"]:
                    send_email(
                        account["email"],
                        "Academic Decision System password reset code",
                        (
                            f"Your password reset code is {code}. It expires in 10 minutes.\n\n"
                            "Do not share this code with anyone. If you did not request a reset, ignore this message."
                        )
                    )
                    email_sent = True
            except Exception:
                pass

            if sms_sent or email_sent:
                delivery_channels = []
                if email_sent:
                    delivery_channels.append("email")
                if sms_sent:
                    delivery_channels.append("SMS")
                channel_text = " and ".join(delivery_channels)
                st.session_state.password_reset_target = {
                    "role": role,
                    "account_id": account["account_id"],
                    "phone": account["phone"],
                    "otp_hash": bcrypt.hashpw(code.encode(), bcrypt.gensalt()),
                    "expires_at": time.time() + 600,
                    "attempts": 0,
                }
                if role == "Student":
                    create_student_notification(
                        account["account_id"],
                        "Password reset requested",
                        f"A reset code was sent through {channel_text}. The code is intentionally not shown in dashboard notifications."
                    )
                st.success(f"Verification code sent through {channel_text}.")
                if not (email_sent and sms_sent):
                    st.warning("One delivery channel is unavailable. Configure both SMS and email for dual-channel verification.")
                st.rerun()
            else:
                st.error("The verification code could not be sent. Check the Twilio and Gmail provider configuration.")
else:
    if time.time() >= target["expires_at"]:
        st.session_state.password_reset_target = None
        st.warning("The verification code expired. Start again to request a new one.")
    elif target["attempts"] >= 5:
        st.session_state.password_reset_target = None
        st.warning("Too many incorrect attempts. Start again to request a new code.")
    else:
        st.info("Enter the code sent to your registered email and mobile number. It expires in 10 minutes.")
        with st.form("complete_password_reset"):
            code = st.text_input("Verification code", max_chars=6)
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            reset_password = st.form_submit_button("Verify and reset password", type="primary")

        if reset_password:
            if len(new_password) < 8:
                st.error("Use at least 8 characters for your new password.")
            elif new_password != confirm_password:
                st.error("The new passwords do not match.")
            elif not code.isdigit() or len(code) != 6:
                st.error("Enter the six-digit verification code.")
            elif not bcrypt.checkpw(code.encode(), target["otp_hash"]):
                target["attempts"] += 1
                st.error("The code is invalid or expired.")
            else:
                if target["role"] == "Student":
                    updated = change_student_password(target["account_id"], new_password)
                else:
                    updated = change_faculty_password(target["account_id"], new_password)
                st.session_state.password_reset_target = None
                if updated:
                    st.success("Password reset successfully. Sign in with your new password.")
                else:
                    st.error("The account could not be updated. Contact the administrator.")

st.divider()
if st.button("Back to sign in"):
    st.session_state.password_reset_target = None
    st.switch_page("dashboard/login.py")