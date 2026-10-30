"""
===========================================================
AI-Based Autonomous Academic Decision System
WhatsApp Notification Service (Twilio Gateway)
Handles live WhatsApp alerts for students and parents.
Replaces cellular SMS with direct WhatsApp messaging.
===========================================================
"""

import os
import re
import json
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

get_whatsapp_secret = get_sms_secret


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


def is_whatsapp_service_configured():
    """Check if Twilio WhatsApp credentials are fully supplied."""
    account_sid = get_sms_secret("TWILIO_ACCOUNT_SID")
    auth_token = get_sms_secret("TWILIO_AUTH_TOKEN")
    whatsapp_number = (
        get_sms_secret("TWILIO_WHATSAPP_NUMBER")
        or get_sms_secret("TWILIO_FROM_NUMBER")
        or get_sms_secret("TWILIO_MESSAGING_SERVICE_SID")
    )
    return bool(account_sid and auth_token and whatsapp_number)

is_sms_service_configured = is_whatsapp_service_configured


def is_whatsapp_enabled():
    """Twilio WhatsApp channel is permanently enabled for all outbound messaging."""
    return True


def send_academic_update_whatsapp(
    phone_number,
    message_body,
    recipient_name="Student",
    send_whatsapp=True,
):
    """
    Send an official WhatsApp notification to a student or parent mobile number via Twilio.
    If Twilio is configured, sends via Twilio WhatsApp API.
    Otherwise, logs to database with simulated queueing.
    """
    try:
        norm_phone = normalize_phone_number(phone_number)
    except Exception as e:
        return {"success": False, "status": "invalid_number", "message": f"Invalid phone format: {e}"}

    account_sid = get_sms_secret("TWILIO_ACCOUNT_SID")
    auth_token = get_sms_secret("TWILIO_AUTH_TOKEN")
    whatsapp_number = (
        get_sms_secret("TWILIO_WHATSAPP_NUMBER")
        or get_sms_secret("TWILIO_FROM_NUMBER")
        or "+17372508034"
    )
    content_sid = get_sms_secret("TWILIO_CONTENT_SID") or get_sms_secret("TWILIO_WHATSAPP_CONTENT_SID")

    channel_name = "WhatsApp"

    if not (account_sid and auth_token and whatsapp_number):
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=norm_phone,
            channel=channel_name,
            sender_email="forestnation08@gmail.com",
            subject=f"Academic {channel_name} Alert",
            message=message_body,
            status="Config Required",
            error_message="Twilio WhatsApp credentials not configured in environment or Streamlit secrets.",
        )
        return {
            "success": False,
            "status": "config_required",
            "phone": norm_phone,
            "channel": channel_name,
            "message": (
                f"WhatsApp message queued for mobile {norm_phone}. "
                "To deliver live alerts, add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER in Streamlit secrets or .env."
            ),
        }

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Ensure whatsapp: prefix for both sender and recipient
        clean_from = whatsapp_number.replace("whatsapp:", "").strip()
        from_wa = f"whatsapp:{clean_from}"

        clean_to = norm_phone.replace("whatsapp:", "").strip()
        to_wa = f"whatsapp:{clean_to}"

        msg_options = {
            "from_": from_wa,
            "to": to_wa,
        }

        if content_sid:
            msg_options["content_sid"] = content_sid
            msg_options["content_variables"] = json.dumps({"1": recipient_name, "2": message_body[:120]})
        else:
            msg_options["body"] = message_body

        try:
            message = client.messages.create(**msg_options)
        except Exception as api_err:
            err_str = str(api_err)
            if "ContentSid Required" in err_str:
                # 24-hour session expired or uninitiated in Sandbox
                guide_msg = (
                    f"Twilio WhatsApp session expired for {norm_phone}. "
                    f"Send a WhatsApp message (e.g. 'Hi' or 'join twilio-trial') to {clean_from} to activate the 24-hr session."
                )
                log_communication(
                    recipient_type="Student",
                    recipient_name=recipient_name,
                    recipient_contact=norm_phone,
                    channel=channel_name,
                    sender_email="forestnation08@gmail.com",
                    subject=f"Academic {channel_name} Alert (Session Required)",
                    message=message_body,
                    status="Session Window Closed",
                    error_message=guide_msg,
                )
                return {
                    "success": False,
                    "status": "session_expired",
                    "phone": norm_phone,
                    "channel": channel_name,
                    "message": guide_msg,
                }
            raise api_err

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
            "message": f"Live WhatsApp message successfully delivered to {norm_phone}!",
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
            "message": f"Twilio WhatsApp delivery failed: {err_msg}",
        }

# Backwards compatible alias so any existing caller automatically routes to WhatsApp
send_academic_update_sms = send_academic_update_whatsapp


def send_academic_recommendation_whatsapp(
    phone_number, full_name, roll_no, risk_level, predicted_perf, top_action=""
):
    """Dispatch concise WhatsApp advisory to student mobile number."""
    action_text = f"\n💡 *Key Advisory:* {top_action[:80]}" if top_action else ""
    wa_body = (
        f"🎓 *[IFHE AI Academic Decision System]*\n"
        f"Dear *{full_name}* (`{roll_no}`):\n\n"
        f"📊 *Forecast:* {predicted_perf}\n"
        f"🚨 *Risk Tier:* {risk_level} Risk{action_text}\n\n"
        "👉 Log in to the Student ERP portal for your complete in-semester Continuous Internal Evaluation (CIE) intervention roadmap."
    )
    return send_academic_update_whatsapp(phone_number, wa_body, recipient_name=full_name)

send_academic_recommendation_sms = send_academic_recommendation_whatsapp


def send_attendance_shortage_whatsapp(phone_number, full_name, attendance_pct, parent_phone=None):
    """Send statutory attendance shortage warning via WhatsApp to student and parent."""
    wa_body = (
        f"🚨 *[IFHE Statutory Attendance Warning]*\n"
        f"Dear *{full_name}*:\n"
        f"Your attendance regularity is *{attendance_pct:.1f}%* (below UGC 75% minimum requirement).\n"
        "You are at immediate risk of exam debarment. Attend all upcoming lectures and remedial tutorials without fail."
    )
    res = send_academic_update_whatsapp(phone_number, wa_body, recipient_name=full_name)

    if parent_phone:
        p_body = (
            f"📢 *[IFHE Department Notice to Parent]*\n"
            f"Attendance for your ward *{full_name}* is *{attendance_pct:.1f}%* (below the statutory 75% limit).\n"
            "Please advise your ward to attend all scheduled classes and departmental remedial coaching."
        )
        send_academic_update_whatsapp(parent_phone, p_body, recipient_name=f"Parent of {full_name}")

    return res

send_attendance_shortage_sms = send_attendance_shortage_whatsapp


def send_session_attendance_whatsapp(
    phone_number, full_name, roll_no, course_code, session_date, is_present, attendance_pct, parent_phone=None
):
    """Dispatch WhatsApp notification when faculty records classroom attendance."""
    status_icon = "✅" if is_present else "❌"
    status_str = "PRESENT" if is_present else "ABSENT"
    wa_body = (
        f"📋 *[IFHE Classroom Attendance Update]*\n"
        f"Student: *{full_name}* (`{roll_no}`)\n"
        f"Course: *{course_code}* | Date: *{session_date}*\n"
        f"Status: {status_icon} *{status_str}*\n"
        f"Current Cumulative Attendance: *{attendance_pct:.1f}%*"
    )
    res = send_academic_update_whatsapp(phone_number, wa_body, recipient_name=full_name)

    if not is_present and parent_phone:
        p_body = (
            f"⚠️ *[IFHE Absence Alert to Parent]*\n"
            f"Your ward *{full_name}* was marked *ABSENT* for *{course_code}* on *{session_date}*.\n"
            f"Current Cumulative Attendance: *{attendance_pct:.1f}%*."
        )
        send_academic_update_whatsapp(parent_phone, p_body, recipient_name=f"Parent of {full_name}")

    return res

send_session_attendance_sms = send_session_attendance_whatsapp


def send_password_reset_whatsapp(phone_number, code):
    """Send verification OTP for password reset directly to WhatsApp."""
    return send_academic_update_whatsapp(
        phone_number,
        (
            f"🔐 *[IFHE AI Academic System]*\n"
            f"Your password reset verification code is: *{code}*\n\n"
            "This OTP expires in 10 minutes. For your security, never share this code with anyone."
        ),
        recipient_name="User",
    )

send_password_reset_sms = send_password_reset_whatsapp