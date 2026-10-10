"""SMS verification helpers for account password resets."""

import os
import re


def normalize_phone_number(phone_number):
    value = str(phone_number or "").strip()
    digits = re.sub(r"\D", "", value)

    if value.startswith("+"):
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Enter a valid phone number.")
        return f"+{digits}"

    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"

    raise ValueError("Enter a valid phone number with country code.")


def send_academic_update_sms(phone_number, message_body):
    phone_number = normalize_phone_number(phone_number)
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not all((account_sid, auth_token)):
        raise RuntimeError("SMS delivery is not configured.")
    if not messaging_service_sid and not from_number:
        raise RuntimeError(
            "Set TWILIO_MESSAGING_SERVICE_SID or TWILIO_FROM_NUMBER to send SMS."
        )

    try:
        from twilio.rest import Client
    except ImportError as error:
        raise RuntimeError("Install the twilio package to enable SMS delivery.") from error

    client = Client(account_sid, auth_token)
    message_options = {"to": phone_number, "body": message_body}
    if messaging_service_sid:
        message_options["messaging_service_sid"] = messaging_service_sid
    else:
        message_options["from_"] = from_number

    message = client.messages.create(**message_options)
    return bool(message.sid)


def send_password_reset_sms(phone_number, code):
    return send_academic_update_sms(
        phone_number,
        f"Your Academic Decision System password reset code is {code}. "
        "It expires in 10 minutes. Do not share this code."
    )
    
    