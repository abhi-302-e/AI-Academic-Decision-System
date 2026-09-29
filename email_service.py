import os
import random
import smtplib
from email.message import EmailMessage


# =========================================================
# GMAIL CONFIGURATION
# =========================================================

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


# =========================================================
# GENERATE OTP
# =========================================================

def generate_otp():
    """
    Generate a 6-digit email verification OTP.
    """
    return str(random.randint(100000, 999999))


# =========================================================
# SEND GENERAL EMAIL
# =========================================================

def send_email(to_email, subject, body):

    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise ValueError(
            "EMAIL_ADDRESS or EMAIL_APP_PASSWORD is not configured."
        )

    message = EmailMessage()

    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD
        )

        smtp.send_message(message)

    return True


# =========================================================
# SEND VERIFICATION OTP
# =========================================================

def send_verification_otp(to_email, otp):

    subject = "Student Registration - Gmail Verification"

    body = f"""
Dear Student,

Welcome to the AI Academic Decision System.

Your Gmail verification OTP is:

{otp}

This OTP is valid for 10 minutes.

Please do not share this OTP with anyone.

Regards,
University Academic Administration
AI Academic Decision System
"""

    return send_email(
        to_email,
        subject,
        body
    )


# =========================================================
# SEND ENROLLMENT NUMBER
# =========================================================

def send_enrollment_email(
    to_email,
    full_name,
    enrollment_no
):

    subject = "Student Registration Successful - Enrollment Number"

    body = f"""
Dear {full_name},

Your student registration has been successfully completed.

Your permanent Enrollment Number is:

{enrollment_no}

This Enrollment Number will remain the same throughout your degree.

You can use your:

Enrollment Number + Password

to login to the Student Portal.

Please keep your Enrollment Number safe.

Regards,
University Academic Administration
AI Academic Decision System
"""

    return send_email(
        to_email,
        subject,
        body
    )