"""
===========================================================
AI-Based Autonomous Academic Decision System
WhatsApp Notification Gateway Module
Direct alias to sms_service.py for clean semantic imports.
===========================================================
"""

from sms_service import (
    is_whatsapp_service_configured,
    is_whatsapp_enabled,
    send_academic_update_whatsapp,
    send_academic_recommendation_whatsapp,
    send_attendance_shortage_whatsapp,
    send_session_attendance_whatsapp,
    send_password_reset_whatsapp,
    normalize_phone_number,
    get_sms_secret,
    get_whatsapp_secret,
)

__all__ = [
    "is_whatsapp_service_configured",
    "is_whatsapp_enabled",
    "send_academic_update_whatsapp",
    "send_academic_recommendation_whatsapp",
    "send_attendance_shortage_whatsapp",
    "send_session_attendance_whatsapp",
    "send_password_reset_whatsapp",
    "normalize_phone_number",
    "get_sms_secret",
    "get_whatsapp_secret",
]
#