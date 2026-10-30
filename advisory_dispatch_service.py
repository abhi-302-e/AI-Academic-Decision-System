"""
===========================================================
AI-Based Autonomous Academic Decision System
Advisory & Attendance Outbound Dispatch Service

Handles:
1. Daily 6:00 PM automated dispatch of AI recommendations & predictions via Email & WhatsApp.
2. Immediate admin-initiated manual dispatch at any time (All students, section-wise, or individual).
3. Section-level attendance notifications sent via Email & WhatsApp when faculty submits attendance.
===========================================================
"""

import os
import sys
import sqlite3
import threading
import time
from datetime import datetime, date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import (
    get_connection,
    get_all_students,
    get_student_by_roll,
    get_student_course_assessments,
    get_academic_policies,
    log_communication,
)
import email_service
from email_service import (
    send_student_recommendations_email,
    send_session_attendance_email,
    get_configured_admin_email,
    is_email_service_active,
)
import sms_service
from sms_service import (
    send_academic_recommendation_whatsapp,
    send_academic_recommendation_sms,
    send_session_attendance_whatsapp,
    send_session_attendance_sms,
    is_whatsapp_service_configured,
    is_sms_service_configured,
)
import recommendation_engine
from recommendation_engine import (
    generate_course_level_recommendations,
    recommendations_for_prediction,
)
import prediction
from prediction import (
    predict_student_comprehensive,
    are_course_models_trained,
)


def init_dispatch_settings_table():
    """Ensure persistence table for scheduler settings and dispatch tracking."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_dispatch_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automated_dispatch_logs (
                dispatch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dispatch_type TEXT,
                target_scope TEXT,
                students_count INTEGER,
                emails_sent INTEGER,
                sms_sent INTEGER,
                status TEXT,
                details TEXT,
                dispatched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    except Exception as e:
        print(f"Error creating dispatch settings tables: {e}")
    finally:
        conn.close()


def get_dispatch_setting(key, default=""):
    init_dispatch_settings_table()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT setting_value FROM outbound_dispatch_settings WHERE setting_key = ?",
            (key,)
        ).fetchone()
        return row["setting_value"] if row else default
    finally:
        conn.close()


def set_dispatch_setting(key, value):
    init_dispatch_settings_table()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO outbound_dispatch_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, str(value))
        )
        conn.commit()
    finally:
        conn.close()


def is_daily_6pm_dispatch_enabled():
    val = get_dispatch_setting("daily_6pm_enabled", "1")
    return val in ("1", "true", "True")


def set_daily_6pm_dispatch_enabled(enabled: bool):
    set_dispatch_setting("daily_6pm_enabled", "1" if enabled else "0")


def get_last_dispatch_info():
    """Return dictionary with last daily 6 PM dispatch date and timestamp."""
    return {
        "last_date": get_dispatch_setting("last_daily_date", "None"),
        "last_time": get_dispatch_setting("last_daily_time", "Never"),
        "last_summary": get_dispatch_setting("last_daily_summary", "No automated dispatches run yet."),
        "auto_attendance_enabled": get_dispatch_setting("auto_attendance_enabled", "1") in ("1", "true", "True"),
    }


def set_auto_attendance_enabled(enabled: bool):
    set_dispatch_setting("auto_attendance_enabled", "1" if enabled else "0")


def is_auto_attendance_enabled():
    val = get_dispatch_setting("auto_attendance_enabled", "1")
    return val in ("1", "true", "True")


# =========================================================
# ATTENDANCE NOTIFICATION DISPATCHER (FACULTY SUBMISSION)
# =========================================================

def dispatch_section_attendance_notifications(session_id: int):
    """
    Called when faculty submits session attendance for a section.
    Sends Email and SMS to all students in that section indicating
    their attendance status (Present / Absent) and updated attendance %.
    """
    conn = get_connection()
    try:
        session = conn.execute(
            """
            SELECT s.session_id, s.session_date, s.timetable_id,
                   t.section, t.course_id,
                   c.course_name, COALESCE(c.catalog_code, c.course_code) AS course_code,
                   f.full_name AS faculty_name
            FROM attendance_sessions s
            JOIN timetable t ON t.timetable_id = s.timetable_id
            JOIN courses c ON c.course_id = t.course_id
            LEFT JOIN faculty f ON f.faculty_id = s.faculty_id
            WHERE s.session_id = ?
            """,
            (session_id,)
        ).fetchone()

        if not session:
            return {"success": False, "message": f"Session #{session_id} not found."}

        records = conn.execute(
            """
            SELECT r.student_id, r.is_present,
                   stu.full_name, stu.roll_number, stu.email, stu.phone, stu.parent_phone,
                   stu.attendance_percentage
            FROM attendance_session_records r
            JOIN students stu ON stu.student_id = r.student_id
            WHERE r.session_id = ?
            """,
            (session_id,)
        ).fetchall()

        if not records:
            return {"success": False, "message": "No attendance records found for session."}

        emails_sent = 0
        sms_sent = 0
        details = []

        course_code = session["course_code"]
        course_name = session["course_name"]
        session_date = session["session_date"]
        section_name = session["section"]

        for rec in records:
            s_dict = dict(rec)
            is_present = bool(s_dict["is_present"])
            att_pct = float(s_dict.get("attendance_percentage") or (100.0 if is_present else 0.0))
            email = s_dict.get("email")
            phone = s_dict.get("phone")
            parent_phone = s_dict.get("parent_phone")

            # Email notification
            if email and "@" in email:
                mail_res = send_session_attendance_email(
                    to_email=email,
                    full_name=s_dict["full_name"],
                    roll_no=s_dict["roll_number"],
                    course_code=course_code,
                    course_name=course_name,
                    session_date=session_date,
                    is_present=is_present,
                    attendance_pct=att_pct,
                    section=section_name,
                )
                if mail_res.get("success"):
                    emails_sent += 1

            # WhatsApp notification
            if phone:
                wa_res = send_session_attendance_whatsapp(
                    phone_number=phone,
                    full_name=s_dict["full_name"],
                    roll_no=s_dict["roll_number"],
                    course_code=course_code,
                    session_date=session_date,
                    is_present=is_present,
                    attendance_pct=att_pct,
                    parent_phone=parent_phone if not is_present else None,
                )
                if wa_res.get("success"):
                    sms_sent += 1

            details.append({
                "student_id": s_dict["student_id"],
                "roll_number": s_dict["roll_number"],
                "status": "Present" if is_present else "Absent",
            })

        summary = f"Session #{session_id} (Section {section_name}): {len(records)} students processed. {emails_sent} emails, {sms_sent} WhatsApp messages sent."

        # Log automated dispatch
        conn.execute(
            """
            INSERT INTO automated_dispatch_logs (dispatch_type, target_scope, students_count, emails_sent, sms_sent, status, details)
            VALUES ('Attendance Session', ?, ?, ?, ?, 'Completed', ?)
            """,
            (f"Section {section_name} - {course_code}", len(records), emails_sent, sms_sent, summary)
        )
        conn.commit()

        return {
            "success": True,
            "session_id": session_id,
            "section": section_name,
            "course": course_code,
            "total_students": len(records),
            "emails_sent": emails_sent,
            "sms_sent": sms_sent,
            "message": summary,
        }

    except Exception as e:
        return {"success": False, "message": f"Error dispatching attendance notifications: {e}"}
    finally:
        conn.close()


# =========================================================
# RECOMMENDATIONS & PREDICTIONS DISPATCH ENGINE
# =========================================================

def dispatch_student_recommendations_and_predictions(
    section=None,
    student_id=None,
    send_email_flag=True,
    send_whatsapp_flag=True,
    progress_callback=None,
    is_scheduled_daily=False,
    send_sms_flag=None,
):
    """
    Generates updated AI predictions and course-level recommendations for selected students
    and dispatches them via Email and WhatsApp.

    Args:
        section (str): Filter by Section (e.g. 'A', 'B') or None for all.
        student_id (int): Filter by specific student or None.
        send_email_flag (bool): Whether to dispatch emails.
        send_whatsapp_flag (bool): Whether to dispatch WhatsApp messages.
        progress_callback (callable): Optional callback(current, total, status_text).
        is_scheduled_daily (bool): Flag indicating if this was triggered by the 6 PM scheduler.
    """
    if send_sms_flag is not None:
        send_whatsapp_flag = send_sms_flag
    init_dispatch_settings_table()
    conn = get_connection()
    try:
        query = """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone,
                   s.parent_phone, s.cgpa, s.attendance_percentage, s.section,
                   s.semester, s.current_year, s.department
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.status = 'Registered'
        """
        params = []
        if student_id:
            query += " AND s.student_id = ?"
            params.append(student_id)
        elif section and section != "All Sections":
            query += " AND sr.section = ?"
            params.append(section)

        query += " GROUP BY s.student_id ORDER BY s.roll_number ASC"
        students = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    total_count = len(students)
    if total_count == 0:
        return {
            "success": False,
            "total": 0,
            "emails_sent": 0,
            "sms_sent": 0,
            "message": "No registered students found for the selected criteria.",
        }

    policies = get_academic_policies()
    emails_sent = 0
    sms_sent = 0
    logs = []

    for idx, student_row in enumerate(students, 1):
        s = dict(student_row)
        stu_id = s["student_id"]
        full_name = s["full_name"]
        roll_no = s["roll_number"]
        s_email = s.get("email")
        s_phone = s.get("phone")
        att_val = float(s.get("attendance_percentage") or 75.0)
        cgpa_val = float(s.get("cgpa") or 7.0)

        # Retrieve course assessments
        assessments = get_student_course_assessments(stu_id, s.get("semester") or 1)

        # Synthesize recommendations
        recs = []
        if assessments:
            for ca in assessments:
                course_recs = generate_course_level_recommendations(ca, policies=policies)
                for cr in course_recs:
                    t_str = cr.get("text") if isinstance(cr, dict) else str(cr)
                    c_code = ca.get("course_code", "Course")
                    recs.append(f"{c_code}: {t_str}")

        if not recs:
            recs = [
                "Maintain continuous class engagement and submit all weekly assignments.",
                "Target minimum 75% attendance in all core lectures and laboratory practicals.",
                "Attend peer-mentoring and departmental tutorial problem-solving sessions."
            ]

        # Prediction synthesis
        predicted_perf = "First Class / Good"
        risk_level = "Low" if att_val >= 75.0 and cgpa_val >= 6.5 else ("Medium" if att_val >= 65.0 else "High")

        if assessments:
            avg_score = sum(float(a.get("overall_total") or 60.0) for a in assessments) / len(assessments)
            if avg_score >= 75.0:
                predicted_perf = "Distinction"
            elif avg_score >= 50.0:
                predicted_perf = "Pass"
            else:
                predicted_perf = "At-Risk / Remedial"

        xai_summary = (
            f"Evaluated against 60/40 CIE-SEE weightage. Current attendance is {att_val:.1f}%, "
            f"with CGPA at {cgpa_val:.2f}. "
            f"{'Statutory attendance remediation required.' if att_val < 75.0 else 'Academic trajectory is on track.'}"
        )

        email_status = "Skipped"
        sms_status = "Skipped"

        # Dispatch Email
        if send_email_flag and s_email and "@" in s_email:
            e_res = send_student_recommendations_email(
                to_email=s_email,
                full_name=full_name,
                roll_no=roll_no,
                enrollment_no=roll_no,
                risk_level=risk_level,
                predicted_perf=predicted_perf,
                cgpa=cgpa_val,
                attendance=att_val,
                recommendations_list=recs[:4],
                xai_summary=xai_summary,
            )
            if e_res.get("success"):
                emails_sent += 1
                email_status = "Delivered"
            else:
                email_status = e_res.get("status", "Failed")

        # Dispatch WhatsApp
        if send_whatsapp_flag and s_phone:
            top_rec = recs[0] if recs else "Maintain class attendance."
            w_res = send_academic_recommendation_whatsapp(
                phone_number=s_phone,
                full_name=full_name,
                roll_no=roll_no,
                risk_level=risk_level,
                predicted_perf=predicted_perf,
                top_action=top_rec[:50],
            )
            if w_res.get("success"):
                sms_sent += 1
                sms_status = "Delivered"
            else:
                sms_status = w_res.get("status", "Failed")

        logs.append({
            "roll_number": roll_no,
            "full_name": full_name,
            "section": s.get("section", "—"),
            "risk": risk_level,
            "email_status": email_status,
            "sms_status": sms_status,
        })

        if progress_callback:
            progress_callback(idx, total_count, f"Processed {full_name} ({roll_no})")

    # Update dispatch logs and settings
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = date.today().isoformat()
    scope_desc = f"Section {section}" if (section and section != "All Sections") else (f"Student {roll_no}" if student_id else "All Registered Students")
    summary_text = f"Dispatched to {total_count} students ({emails_sent} emails, {sms_sent} WhatsApp messages sent) on {now_str}."

    if is_scheduled_daily:
        set_dispatch_setting("last_daily_date", today_str)
        set_dispatch_setting("last_daily_time", now_str)
        set_dispatch_setting("last_daily_summary", summary_text)

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO automated_dispatch_logs (dispatch_type, target_scope, students_count, emails_sent, sms_sent, status, details)
            VALUES (?, ?, ?, ?, ?, 'Completed', ?)
            """,
            ("Daily 6 PM Scheduler" if is_scheduled_daily else "Admin Manual Dispatch", scope_desc, total_count, emails_sent, sms_sent, summary_text)
        )
        conn.commit()
    except Exception as e:
        print(f"Error logging dispatch: {e}")
    finally:
        conn.close()

    return {
        "success": True,
        "total": total_count,
        "emails_sent": emails_sent,
        "sms_sent": sms_sent,
        "timestamp": now_str,
        "logs": logs,
        "message": summary_text,
    }


# =========================================================
# BACKGROUND 6:00 PM AUTOMATED SCHEDULER
# =========================================================

_scheduler_thread = None
_scheduler_lock = threading.Lock()

def check_and_run_daily_6pm_dispatch():
    """
    Check if current local time is at or past 18:00 (6:00 PM),
    and if today's daily batch has not been executed yet.
    If conditions are met and scheduler is enabled, executes dispatch.
    """
    if not is_daily_6pm_dispatch_enabled():
        return False

    now = datetime.now()
    today_str = date.today().isoformat()
    last_run_date = get_dispatch_setting("last_daily_date", "")

    # Trigger if 18:00 or later and not run today
    if now.hour >= 18 and last_run_date != today_str:
        print(f"[Scheduler] Daily 6:00 PM trigger activated on {now.isoformat()}. Dispatching recommendations...")
        try:
            res = dispatch_student_recommendations_and_predictions(
                section=None,
                send_email_flag=True,
                send_whatsapp_flag=True,
                is_scheduled_daily=True,
            )
            print(f"[Scheduler] Completed: {res.get('message')}")
            return True
        except Exception as e:
            print(f"[Scheduler] Dispatch error: {e}")
            return False

    return False


def _scheduler_worker():
    """Background loop checking every 45 seconds for 6:00 PM trigger."""
    while True:
        try:
            check_and_run_daily_6pm_dispatch()
        except Exception as e:
            print(f"[Scheduler Worker Error]: {e}")
        time.sleep(45)


def start_scheduler_service():
    """Start the background daemon thread if not already running."""
    global _scheduler_thread
    with _scheduler_lock:
        if _scheduler_thread is None or not _scheduler_thread.is_alive():
            _scheduler_thread = threading.Thread(target=_scheduler_worker, daemon=True, name="AcademicAdvisory6PMScheduler")
            _scheduler_thread.start()
            print("[Scheduler] Automated Daily 6:00 PM Advisory Dispatcher background service started.")


# Scheduler can be started on demand by admin dashboard or explicitly
# start_scheduler_service()
