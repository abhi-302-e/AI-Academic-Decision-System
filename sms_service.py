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

try:
    import streamlit as st
except ImportError:
    st = None

def get_sms_secret(key, default=""):
    """Fetch secret from Streamlit secrets or OS environment."""
    try:
        if st is not None and hasattr(st, "secrets") and st.secrets is not None:
            if key in st.secrets:
                val = st.secrets[key]
                if val is not None:
                    return str(val).strip()
    except Exception:
        pass
    env_val = os.getenv(key, default)
    if env_val is None:
        return ""
    return str(env_val).strip()


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
    account_sid = get_sms_secret("TWILIO_ACCOUNT_SID")
    auth_token = get_sms_secret("TWILIO_AUTH_TOKEN")
    from_number = get_sms_secret("TWILIO_FROM_NUMBER") or get_sms_secret("TWILIO_MESSAGING_SERVICE_SID")
    return bool(account_sid and auth_token and from_number)


def is_whatsapp_enabled():
    """Check if Twilio WhatsApp channel is enabled."""
    return bool(get_sms_secret("TWILIO_WHATSAPP_NUMBER") or get_sms_secret("TWILIO_ENABLE_WHATSAPP"))


def send_academic_update_sms(phone_number, message_body, recipient_name="Student", send_whatsapp=False):
    """
    Send an SMS or WhatsApp message to a mobile number.
    If Twilio is configured, sends via Twilio API.
    Otherwise, logs to database with simulated queueing.
    """
    try:
        norm_phone = normalize_phone_number(phone_number)
    except Exception as e:
        return {"success": False, "status": "invalid_number", "message": f"Invalid phone format: {e}"}

    account_sid = get_sms_secret("TWILIO_ACCOUNT_SID")
    auth_token = get_sms_secret("TWILIO_AUTH_TOKEN")
    messaging_service_sid = get_sms_secret("TWILIO_MESSAGING_SERVICE_SID")
    from_number = get_sms_secret("TWILIO_FROM_NUMBER")
    whatsapp_number = get_sms_secret("TWILIO_WHATSAPP_NUMBER")

    channel_name = "WhatsApp" if send_whatsapp else "SMS"

    if not (account_sid and auth_token and (messaging_service_sid or from_number or whatsapp_number)):
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel=channel_name,
            sender_email="forestnation08@gmail.com",
            subject=f"Academic {channel_name} Alert",
            message=message_body,
            status="Config Required",
            error_message="Twilio credentials not configured in environment or Streamlit secrets.",
        )
        return {
            "success": False,
            "status": "config_required",
            "phone": norm_phone,
            "channel": channel_name,
            "message": (
                f"{channel_name} queued for mobile {norm_phone}. "
                "To deliver live cellular alerts, add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in Streamlit secrets or .env."
            ),
        }

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        if send_whatsapp and whatsapp_number:
            from_wa = whatsapp_number if whatsapp_number.startswith("whatsapp:") else f"whatsapp:{whatsapp_number}"
            to_wa = f"whatsapp:{norm_phone}"
            message = client.messages.create(
                from_=from_wa,
                to=to_wa,
                body=message_body,
            )
        else:
            message_options = {"to": norm_phone, "body": message_body}
            if messaging_service_sid:
                message_options["messaging_service_sid"] = messaging_service_sid
            elif from_number:
                message_options["from_"] = from_number
            else:
                raise ValueError("No Twilio sender phone number or Messaging Service SID provided.")
            message = client.messages.create(**message_options)

        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel=channel_name,
            sender_email="forestnation08@gmail.com",
            subject=f"Academic {channel_name} Alert",
            message=message_body,
            status="Delivered",
            error_message=None,
        )
        return {
            "success": True,
            "status": "delivered",
            "sid": message.sid,
            "phone": norm_phone,
            "channel": channel_name,
            "message": f"Live {channel_name} successfully delivered to {norm_phone}!",
        }

    except Exception as error:
        err_msg = str(error)
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel=channel_name,
            sender_email="forestnation08@gmail.com",
            subject=f"Academic {channel_name} Alert",
            message=message_body,
            status="Failed",
            error_message=err_msg,
        )
        return {
            "success": False,
            "status": "failed",
            "phone": norm_phone,
            "channel": channel_name,
            "message": f"Twilio {channel_name} delivery failed: {err_msg}",
        }


def send_academic_recommendation_sms(phone_number, full_name, roll_no, risk_level, predicted_perf, top_action=""):
    """Dispatch concise SMS and WhatsApp advisory to student and parent mobile numbers."""
    action_text = f" Advisory: {top_action[:60]}." if top_action else ""
    sms_body = (
        f"[AI Academic System] Dear {full_name} ({roll_no}): "
        f"Your AI Forecast is {predicted_perf} ({risk_level} Risk).{action_text} "
        "Log in to the Student ERP portal for your complete intervention plan."
    )
    # Attempt SMS
    res = send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=False)
    # If WhatsApp is enabled, also transmit via WhatsApp
    if is_whatsapp_enabled():
        send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=True)
    return res


def send_attendance_shortage_sms(phone_number, full_name, attendance_pct, parent_phone=None):
    """Send statutory attendance shortage warning via SMS and WhatsApp."""
    sms_body = (
        f"[AI Academic System] Dear {full_name}: Your attendance is {attendance_pct:.1f}% "
        "(below UGC 75% minimum). You are at risk of exam condonation. "
        "Attend upcoming classes and remedial tutorials immediately."
    )
    res = send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=False)
    if is_whatsapp_enabled():
        send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=True)

    if parent_phone:
        p_body = (
            f"[AI Academic System] Attendance for your ward {full_name} is {attendance_pct:.1f}% "
            "(below UGC 75% limit). Remedial tutorial attendance is mandatory."
        )
        send_academic_update_sms(parent_phone, p_body, recipient_name=f"Parent of {full_name}", send_whatsapp=False)
        if is_whatsapp_enabled():
            send_academic_update_sms(parent_phone, p_body, recipient_name=f"Parent of {full_name}", send_whatsapp=True)

    return res


def send_session_attendance_sms(phone_number, full_name, roll_no, course_code, session_date, is_present, attendance_pct, parent_phone=None):
    """Dispatch SMS and WhatsApp notification when faculty submits attendance for a session."""
    status_str = "PRESENT" if is_present else "ABSENT"
    sms_body = (
        f"[AI Academic System] Dear {full_name} ({roll_no}): Attendance for {course_code} on {session_date} "
        f"is recorded: {status_str}. Current attendance: {attendance_pct:.1f}%."
    )
    res = send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=False)
    if is_whatsapp_enabled():
        send_academic_update_sms(phone_number, sms_body, recipient_name=full_name, send_whatsapp=True)

    if not is_present and parent_phone:
        p_body = (
            f"[AI Academic System] Alert for Parent of {full_name}: Your ward was marked ABSENT for "
            f"{course_code} on {session_date}. Current attendance: {attendance_pct:.1f}%."
        )
        send_academic_update_sms(parent_phone, p_body, recipient_name=f"Parent of {full_name}", send_whatsapp=False)
        if is_whatsapp_enabled():
            send_academic_update_sms(parent_phone, p_body, recipient_name=f"Parent of {full_name}", send_whatsapp=True)

    return res


def send_password_reset_sms(phone_number, code):
    """Send verification OTP for password reset."""
    return send_academic_update_sms(
        phone_number,
        f"Your Academic Decision System password reset code is {code}. "
        "It expires in 10 minutes. Do not share this code.",
        recipient_name="User",
    )