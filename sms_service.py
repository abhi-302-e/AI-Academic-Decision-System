"""
===========================================================
AI-Based Autonomous Academic Decision System
SMS Notification Service
Handles live cellular SMS alerts for students and parents.
===========================================================
"""

import os
import re
from pathlib import Path
from database import log_communication

# Auto-load .env credentials
try:
    from dotenv import load_dotenv
    _ENV_FILE = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=_ENV_FILE, override=False)
except ImportError:
    pass


def normalize_phone_number(phone_number):
    """Clean and standardize phone numbers into E.164 international format."""
    value = str(phone_number or "").strip()
    digits = re.sub(r"\D", "", value)

    if not digits:
        raise ValueError("Phone number cannot be empty.")

    if value.startswith("+"):
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Enter a valid international phone number.")
        return f"+{digits}"

    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"

    return f"+{digits}"


def is_sms_service_configured():
    """Check if Twilio credentials are fully supplied."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER") or os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    return bool(account_sid and auth_token and from_number)


def send_academic_update_sms(phone_number, message_body, recipient_name="Student"):
    """
    Send an SMS message to a mobile number.
    If Twilio is configured, sends via Twilio API.
    Otherwise, logs to database with Simulated status and actionable setup tips.
    """
    try:
        norm_phone = normalize_phone_number(phone_number)
    except Exception as e:
        return {"success": False, "status": "invalid_number", "message": f"Invalid phone format: {e}"}

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (account_sid and auth_token and (messaging_service_sid or from_number)):
        # Record simulated dispatch in database
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel="SMS",
            sender_email="forestnation08@gmail.com",
            subject="Academic SMS Alert",
            message=message_body,
            status="Config Required",
            error_message="Twilio credentials not configured in environment.",
        )
        return {
            "success": False,
            "status": "config_required",
            "phone": norm_phone,
            "message": (
                f"SMS queued for real phone {norm_phone}. "
                "To deliver live cellular SMS, configure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in environment."
            ),
        }

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message_options = {"to": norm_phone, "body": message_body}
        if messaging_service_sid:
            message_options["messaging_service_sid"] = messaging_service_sid
        else:
            message_options["from_"] = from_number

        message = client.messages.create(**message_options)
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel="SMS",
            sender_email="forestnation08@gmail.com",
            subject="Academic SMS Alert",
            message=message_body,
            status="Delivered",
            error_message=None,
        )
        return {
            "success": True,
            "status": "delivered",
            "sid": message.sid,
            "phone": norm_phone,
            "message": f"Live SMS successfully dispatched to {norm_phone}!",
        }

    except Exception as error:
        err_msg = str(error)
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel="SMS",
            sender_email="forestnation08@gmail.com",
            subject="Academic SMS Alert",
            message=message_body,
            status="Failed",
            error_message=err_msg,
        )
        return {"success": False, "status": "failed", "phone": norm_phone, "message": f"Twilio SMS delivery failed: {err_msg}"}


def send_academic_recommendation_sms(phone_number, full_name, roll_no, risk_level, predicted_perf, top_action=""):
    """Dispatch concise SMS advisory to student and parent mobile numbers."""
    action_text = f" Advisory: {top_action[:60]}." if top_action else ""
    sms_body = (
        f"[IFHE Academic Alert] Dear {full_name} ({roll_no}): "
        f"Your AI Forecast is {predicted_perf} ({risk_level} Risk).{action_text} "
        "Log in to the Student ERP portal for your complete intervention plan."
    )
    return send_academic_update_sms(phone_number, sms_body, recipient_name=full_name)


def send_attendance_shortage_sms(phone_number, full_name, attendance_pct, parent_phone=None):
    """Send statutory attendance shortage warning via SMS."""
    sms_body = (
        f"[IFHE Statutory Alert] Dear {full_name}: Your attendance is {attendance_pct:.1f}% "
        "(below UGC 75% minimum). You are at risk of exam condonation. "
        "Attend upcoming classes and remedial tutorials immediately."
    )
    res = send_academic_update_sms(phone_number, sms_body, recipient_name=full_name)

    if parent_phone:
        p_body = (
            f"[IFHE Parent Alert] Attendance for your ward {full_name} is {attendance_pct:.1f}% "
            "(below UGC 75% limit). Remedial tutorial attendance is mandatory."
        )
        send_academic_update_sms(parent_phone, p_body, recipient_name=f"Parent of {full_name}")

    return res


def send_password_reset_sms(phone_number, code):
    """Send verification OTP for password reset."""
    return send_academic_update_sms(
        phone_number,
        f"Your Academic Decision System password reset code is {code}. "
        "It expires in 10 minutes. Do not share this code.",
        recipient_name="User",
    )