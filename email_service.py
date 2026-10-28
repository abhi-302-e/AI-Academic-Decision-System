"""
===========================================================
AI-Based Autonomous Academic Decision System
Email Communication Service
Sender (Permanent): forestnation08@gmail.com
===========================================================
"""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from database import log_communication
import streamlit as st


ADMIN_EMAIL_ADDRESS = "forestnation08@gmail.com"

def get_secret(key, default=""):
    """Read Streamlit Cloud secrets first, then environment variables."""
    try:
        value = st.secrets.get(key, "")
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(key, default).strip()


EMAIL_ADDRESS = (
    get_secret("SMTP_EMAIL")
    or get_secret("EMAIL_ADDRESS")
    or ADMIN_EMAIL_ADDRESS
)

EMAIL_APP_PASSWORD = (
    get_secret("SMTP_APP_PASSWORD")
    or get_secret("EMAIL_APP_PASSWORD")
)


def get_configured_admin_email():
    return EMAIL_ADDRESS


def is_email_service_active():
    return bool(EMAIL_APP_PASSWORD)


def send_email(to_email, subject, body, html_body=None, recipient_name="Student"):
    """
    Send an email from forestnation08@gmail.com.
    If EMAIL_APP_PASSWORD is set, sends a live email via Gmail SMTP.
    Otherwise, logs the dispatch to database and provides actionable instructions.
    """
    from_email = get_configured_admin_email()
    app_password = (
    get_secret("SMTP_APP_PASSWORD")
    or get_secret("EMAIL_APP_PASSWORD")
)
    message = EmailMessage()
    message["From"] = f"IFHE Academic Administration <{from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    if not app_password:
        # Log simulated dispatch
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=to_email,
            channel="Email",
            sender_email=from_email,
            subject=subject,
            message=body[:500],
            status="Config Required",
            error_message="EMAIL_APP_PASSWORD not set. To send live real-world emails from forestnation08@gmail.com, generate a 16-character App Password at myaccount.google.com/apppasswords and set EMAIL_APP_PASSWORD.",
        )
        return {
            "success": False,
            "status": "config_required",
            "sender": from_email,
            "recipient": to_email,
            "message": (
                f"Email queued for {to_email} from permanent sender {from_email}. "
                "To deliver live to the recipient inbox, please enter your Gmail App Password for forestnation08@gmail.com."
            ),
        }

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, app_password)
            smtp.send_message(message)

        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=to_email,
            channel="Email",
            sender_email=from_email,
            subject=subject,
            message=body[:500],
            status="Delivered",
            error_message=None,
        )
        return {
            "success": True,
            "status": "delivered",
            "sender": from_email,
            "recipient": to_email,
            "message": f"Real-world email successfully delivered to {to_email} from {from_email}!",
        }

    except Exception as error:
        err_msg = str(error)
        log_communication(
            recipient_type="Student",
            recipient_name=recipient_name,
            recipient_contact=to_email,
            channel="Email",
            sender_email=from_email,
            subject=subject,
            message=body[:500],
            status="Failed",
            error_message=err_msg,
        )
        return {
            "success": False,
            "status": "failed",
            "sender": from_email,
            "recipient": to_email,
            "message": f"SMTP delivery failed: {err_msg}",
        }


def send_student_recommendations_email(
    to_email,
    full_name,
    roll_no,
    enrollment_no,
    risk_level,
    predicted_perf,
    cgpa,
    attendance,
    recommendations_list,
    xai_summary="",
):
    """
    Dispatch student's academic prediction, risk radar, and recommendations.
    """
    subject = f"Academic Progress & AI Recommendation Advisory - {full_name} ({roll_no})"

    recs_text = ""
    recs_html_items = ""
    for idx, r in enumerate(recommendations_list, 1):
        if isinstance(r, dict):
            txt = r.get("text", "")
            cat = r.get("category", "Advisory")
            prio = r.get("priority", "Medium")
            recs_text += f"{idx}. [{cat} | {prio} Priority] {txt}\n"
            recs_html_items += f"<li style='margin-bottom: 8px;'><b>[{cat} · {prio} Priority]:</b> {txt}</li>"
        else:
            recs_text += f"{idx}. {r}\n"
            recs_html_items += f"<li style='margin-bottom: 8px;'>{r}</li>"

    plain_body = f"""Dear {full_name},

This is an official academic advisory notice from the AI Academic Decision System (IFHE Faculty of Science & Technology).

Student Credentials:
• Full Name: {full_name}
• Roll Number: {roll_no}
• Enrollment No: {enrollment_no or 'N/A'}

AI Predictive Intelligence Forecast:
• Projected Academic Standing: {predicted_perf}
• Academic Risk Radar: {risk_level} Risk
• Cumulative Grade Point Average (CGPA): {cgpa:.2f} / 10.0
• Current Course Attendance: {attendance:.1f}%

Model Explainability (XAI) Insight:
{xai_summary or 'Predictive indicators balanced across 60/40 institutional evaluation model.'}

Targeted Action Recommendations:
{recs_text}

Please log in to your Student ERP Portal for your complete Gradebook, Course Timetable, and What-If Goal Simulator.

Regards,
Academic Administration & AI Decision Cell
The ICFAI Foundation for Higher Education (IFHE)
Sender: {get_configured_admin_email()}
"""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; padding: 20px; color: #1e293b;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
            <div style="background: linear-gradient(135deg, #091e3a 0%, #1e3a8a 100%); color: #ffffff; padding: 24px; text-align: center;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;">THE ICFAI FOUNDATION FOR HIGHER EDUCATION</h2>
                <div style="font-size: 13px; color: #ffd166; margin-top: 4px; font-weight: 600;">Faculty of Science & Technology (FST)</div>
                <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">AI-Based Autonomous Academic Decision System</div>
            </div>
            
            <div style="padding: 24px;">
                <p style="font-size: 15px; margin-top: 0;">Dear <b>{full_name}</b> (Roll No: <code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">{roll_no}</code>),</p>
                <p style="font-size: 14px; line-height: 1.5; color: #475569;">
                    Your personalized academic evaluation and AI trajectory forecast have been generated by the Institutional Decision Engine for <b>Year 1, Semester 1</b>.
                </p>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0;">
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Predicted Result</div>
                        <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 4px;">{predicted_perf}</div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Risk Classification</div>
                        <div style="font-size: 18px; font-weight: 700; color: {'#16a34a' if risk_level=='Low' else ('#d97706' if risk_level=='Medium' else '#dc2626')}; margin-top: 4px;">{risk_level} Risk</div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Current CGPA</div>
                        <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 4px;">{cgpa:.2f} / 10.0</div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Attendance Regularity</div>
                        <div style="font-size: 18px; font-weight: 700; color: {'#16a34a' if attendance >= 75 else '#dc2626'}; margin-top: 4px;">{attendance:.1f}%</div>
                    </div>
                </div>

                {f'''
                <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px; border-radius: 4px; margin: 16px 0; font-size: 13px; color: #1e3a8a;">
                    <b>Explainable AI (XAI) Insight:</b> {xai_summary}
                </div>
                ''' if xai_summary else ''}

                <h4 style="color: #0f172a; margin: 20px 0 10px 0; font-size: 15px;">🎯 Targeted Recommendations & Action Items:</h4>
                <ul style="font-size: 13px; color: #334155; line-height: 1.5; padding-left: 20px;">
                    {recs_html_items or '<li>Maintain consistent academic engagement in all registered courses.</li>'}
                </ul>

                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
                    Official Institutional Communication from <b>{get_configured_admin_email()}</b>.<br>
                    Autonomous Academic Decision System · IFHE Hyderabad
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        body=plain_body,
        html_body=html_body,
        recipient_name=full_name,
    )


def send_attendance_shortage_email(to_email, full_name, roll_no, attendance_pct, parent_email=None):
    """Dispatch statutory UGC attendance shortage alert to student and parent."""
    subject = f"URGENT: Statutory Attendance Shortage Notice (< 75%) - {full_name} ({roll_no})"
    body = f"""Dear {full_name},

This is an official statutory alert from the Examination Branch and Academic Dean Office.

Your current registered course attendance is {attendance_pct:.1f}%, which is below the mandatory 75% minimum attendance requirement mandated by University Grants Commission (UGC) regulations.

Under university academic governance:
• Students with attendance below 75% are ineligible to sit for End-Semester External Examinations.
• You must attend mandatory remedial tutorial classes conducted on Saturdays.
• Contact your Head of Department immediately.

Academic Administration
The ICFAI Foundation for Higher Education
Sender: {get_configured_admin_email()}
"""
    res = send_email(to_email, subject, body, recipient_name=full_name)

    if parent_email and "@" in parent_email:
        p_subject = f"URGENT: Academic Attendance Shortage Alert for Your Ward - {full_name} ({roll_no})"
        send_email(parent_email, p_subject, body, recipient_name=f"Parent of {full_name}")

    return res


def send_enrollment_email(to_email, full_name, enrollment_no):
    """Send student their newly generated permanent Enrollment Number."""
    subject = "Student Registration Successful - Enrollment Number"
    body = f"""Dear {full_name},

Your student registration has been successfully verified and completed.

Your permanent Enrollment Number is:
{enrollment_no}

This Enrollment Number will remain unchanged throughout your degree program.
You can use your Enrollment Number + Password to log in to the Student ERP Portal.

Regards,
University Academic Administration
AI Academic Decision System
The ICFAI Foundation for Higher Education
Sender: {get_configured_admin_email()}
"""
    return send_email(to_email, subject, body, recipient_name=full_name)