"""
===========================================================
AI-Based Autonomous Academic Decision System
Recommendations & Predictions Dispatch Center (Admin)

Outbound delivery hub for:
1. Automated daily 6:00 PM recommendation and prediction dispatches.
2. Manual on-demand dispatch at any time (All students, section-wise, or individual).
3. Section-level attendance notification controls when faculty marks attendance.
4. Live delivery logs and gateway diagnostics.
===========================================================
"""

import sys
from pathlib import Path
from datetime import datetime, date

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from auth import require_admin
from database import (
    get_connection,
    get_all_students,
    get_default_section_names,
    get_communication_logs,
    get_student_course_assessments,
    get_student_by_roll,
)
from email_service import (
    send_email,
    get_configured_admin_email,
    is_email_service_active,
)
from sms_service import (
    send_academic_update_sms,
    is_sms_service_configured,
)
from advisory_dispatch_service import (
    dispatch_student_recommendations_and_predictions,
    dispatch_section_attendance_notifications,
    is_daily_6pm_dispatch_enabled,
    set_daily_6pm_dispatch_enabled,
    is_daily_6pm_email_enabled,
    set_daily_6pm_email_enabled,
    is_daily_6pm_whatsapp_enabled,
    set_daily_6pm_whatsapp_enabled,
    get_last_dispatch_info,
    is_auto_attendance_enabled,
    set_auto_attendance_enabled,
    check_and_run_daily_6pm_dispatch,
    get_single_student_advisory_preview,
    update_student_email_in_db,
)

# Enforce admin authentication
require_admin()

admin = dict(st.session_state.user_data or {})
if not admin:
    st.info("Please log in as an administrator to access the Dispatch Center.")
    st.stop()

# Header
st.title("📡 Recommendations & Predictions Dispatch Center")
st.caption("Central institutional outbound delivery engine for AI predictions, explainable recommendations, and daily attendance notifications via Email and WhatsApp.")

admin_email = get_configured_admin_email()

# Gateway Diagnostics Ribbon
with st.container(border=True):
    dcol1, dcol2, dcol3, dcol4 = st.columns(4)

    with dcol1:
        st.markdown("**🏛️ Institutional Sender**")
        st.code(admin_email)

    with dcol2:
        mail_active = is_email_service_active()
        st.markdown("**📧 Gmail SMTP Gateway**")
        if mail_active:
            st.success("● Connected / Live")
        else:
            st.warning("○ Password Required")

    with dcol3:
        wa_active = is_sms_service_configured()
        st.markdown("**💬 Twilio WhatsApp Gateway**")
        if wa_active:
            st.success("● Twilio WhatsApp Armed")
        else:
            st.info("○ Queued / Simulation")

    with dcol4:
        sched_on = is_daily_6pm_dispatch_enabled()
        st.markdown("**⏰ Daily 6:00 PM Scheduler**")
        if sched_on:
            st.success("● Active (18:00 IST)")
        else:
            st.error("○ Disabled")

st.divider()

# Dispatch Tabs
tab_manual, tab_daily, tab_att, tab_logs = st.tabs([
    "🚀 Send at Any Time (Manual Dispatch)",
    "⏰ Automated Daily 6:00 PM Dispatcher",
    "📋 Section Attendance Notification Center",
    "📜 Outbound Audit Logs",
])

# =========================================================
# TAB 1: SEND AT ANY TIME (MANUAL DISPATCH)
# =========================================================
with tab_manual:
    st.subheader("⚡ Send Recommendations & Predictions (Manual Dispatch)")
    st.caption("Administrator-initiated on-demand dispatch. Generate real-time AI predictions, explainable insights, and course action plans, then deliver them immediately to students via Email and WhatsApp.")

    scope_mode = st.radio(
        "Select Target Scope",
        ["Individual Student", "Specific Section (A–J)", "All Registered Students (All Sections)"],
        horizontal=True,
    )

    if scope_mode == "Individual Student":
        st.markdown("---")
        students_df = get_all_students()
        students_list = students_df.to_dict("records") if hasattr(students_df, "to_dict") else list(students_df)
        stu_choices = {
            f"{s.get('roll_number', '')} - {s.get('full_name', '')} (Section {s.get('section', '—')})": s.get("student_id")
            for s in students_list
        }

        if stu_choices:
            sel_label = st.selectbox("🎯 Select Student to Dispatch", list(stu_choices.keys()), index=0)
            target_student_id = stu_choices[sel_label]
            preview = get_single_student_advisory_preview(target_student_id)

            if preview:
                stu = preview["student"]

                with st.container(border=True):
                    st.markdown(f"### 👤 Student Profile: **{stu.get('full_name')}** (`{stu.get('roll_number')}`)")
                    col_p1, col_p2 = st.columns([1, 1])

                    with col_p1:
                        st.markdown(f"• **Department:** {stu.get('department', 'CSE')}")
                        st.markdown(f"• **Section:** {stu.get('section', 'A')} | **Semester:** {stu.get('semester', 1)}")

                        curr_email = stu.get("email") or ""
                        new_email_input = st.text_input("📧 Destination Email Address", value=curr_email, key=f"email_inp_{target_student_id}")
                        if new_email_input.strip() != curr_email.strip():
                            if st.button("💾 Save Updated Email Address", key=f"btn_save_email_{target_student_id}"):
                                if update_student_email_in_db(target_student_id, new_email_input.strip()):
                                    st.success(f"Email updated to `{new_email_input.strip()}`!")
                                    st.rerun()

                        st.markdown(f"• **WhatsApp Contact:** `{stu.get('phone') or 'Not provided'}`")

                    with col_p2:
                        st.markdown("**Academic & AI Diagnostic Snapshot**")
                        scol1, scol2 = st.columns(2)
                        with scol1:
                            st.metric("CIE Internal Score", f"{preview['cie_marks']:.1f} / 60.0")
                            st.metric("Attendance Regularity", f"{preview['attendance']:.1f}%")
                        with scol2:
                            r_col = "🟢" if preview['risk_level'] == "Low" else ("🟠" if preview['risk_level'] == "Medium" else "🔴")
                            st.markdown(f"**Risk Radar:** {r_col} `{preview['risk_level']} Risk`")
                            st.markdown(f"**Predicted Result:** `{preview['predicted_perf']}`")

                    # Custom counselor note
                    custom_note_input = st.text_area(
                        "📝 Add Personalized Counselor / Dean Note (optional - will be included prominently in the student's email):",
                        placeholder="e.g. Please meet your academic mentor during office hours on Tuesday at 3:00 PM to review Quiz 2 preparation.",
                        key=f"custom_note_{target_student_id}",
                    )

                    with st.expander("👁️ Preview AI Recommendations & Action Plan that will be Dispatched", expanded=False):
                        st.info(f"**Explainable AI (XAI) Insight:** {preview['xai_summary']}")
                        st.markdown("**Course Action Items:**")
                        for idx, r in enumerate(preview["recommendations"], 1):
                            st.markdown(f"{idx}. {r}")

                    st.markdown("**Delivery Channels**")
                    col_ch1, col_ch2 = st.columns(2)
                    with col_ch1:
                        send_email_ind = st.checkbox("📧 Deliver via Email (Recommended)", value=True, key="ind_email_cb")
                    with col_ch2:
                        send_wa_ind = st.checkbox("💬 Deliver via WhatsApp", value=False, key="ind_wa_cb")

                    if st.button(f"🚀 Send Academic Advisory Email to {stu.get('full_name')} Now", type="primary", use_container_width=True):
                        if not send_email_ind and not send_wa_ind:
                            st.error("Please select at least one delivery channel (Email or WhatsApp).")
                        else:
                            with st.spinner(f"Sending real-time advisory evaluation to {stu.get('full_name')}..."):
                                res = dispatch_student_recommendations_and_predictions(
                                    student_id=target_student_id,
                                    send_email_flag=send_email_ind,
                                    send_whatsapp_flag=send_wa_ind,
                                    custom_note=custom_note_input.strip(),
                                    is_scheduled_daily=False,
                                )

                            if res.get("success"):
                                st.success(f"🎉 **Email Successfully Dispatched to {stu.get('full_name')}!** ({stu.get('email')})")
                                if res.get("logs"):
                                    st.dataframe(pd.DataFrame(res.get("logs")), use_container_width=True, hide_index=True)
                            else:
                                st.error(f"❌ Dispatch error: {res.get('message')}")
        else:
            st.warning("No students available in the database.")

    else:
        # Batch scope (Section or All)
        col_target, col_channels = st.columns([2, 1])
        target_section = None

        with col_target:
            if scope_mode == "Specific Section (A–J)":
                section_opts = get_default_section_names()
                target_section = st.selectbox("Choose Section", section_opts)

        with col_channels:
            st.markdown("**Delivery Channels**")
            send_email_choice = st.checkbox("📧 Deliver via Email", value=True, key="batch_email_cb")
            send_whatsapp_choice = st.checkbox("💬 Deliver via WhatsApp", value=False, key="batch_wa_cb")

        # Preview count & summary
        conn = get_connection()
        preview_query = """
            SELECT COUNT(DISTINCT s.student_id) as count
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.status = 'Registered'
        """
        params = []
        if target_section:
            preview_query += " AND sr.section = ?"
            params.append(target_section)

        row = conn.execute(preview_query, params).fetchone()
        conn.close()
        target_count = row["count"] if row else 0

        st.info(f"🎯 **Target Summary:** Ready to batch-dispatch AI recommendations & predictions to **{target_count}** student(s).")

        if st.button("🚀 Batch Dispatch Recommendations & Predictions Now", type="primary", use_container_width=True):
            if not send_email_choice and not send_whatsapp_choice:
                st.error("Please select at least one delivery channel (Email or WhatsApp).")
            elif target_count == 0:
                st.warning("No registered students found matching the selected scope.")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                def update_progress(curr, total, msg):
                    frac = curr / total if total > 0 else 1.0
                    progress_bar.progress(frac)
                    status_text.caption(f"Processing ({curr}/{total}): {msg}")

                with st.spinner("Generating AI evaluations and batch dispatching communications..."):
                    res = dispatch_student_recommendations_and_predictions(
                        section=target_section,
                        student_id=None,
                        send_email_flag=send_email_choice,
                        send_whatsapp_flag=send_whatsapp_choice,
                        progress_callback=update_progress,
                        is_scheduled_daily=False,
                    )

                progress_bar.progress(1.0)
                status_text.empty()

                if res.get("success"):
                    st.success(f"🎉 **Batch Dispatch Completed!** {res.get('message')}")
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.metric("Emails Delivered", res.get("emails_sent", 0))
                    with col_res2:
                        st.metric("WhatsApp Messages Delivered", res.get("whatsapp_sent", res.get("sms_sent", 0)))

                    if res.get("logs"):
                        with st.expander("View Delivery Details", expanded=False):
                            st.dataframe(pd.DataFrame(res.get("logs")), use_container_width=True, hide_index=True)
                else:
                    st.error(f"❌ Dispatch failed: {res.get('message')}")

# =========================================================
# TAB 2: AUTOMATED DAILY 6:00 PM DISPATCHER
# =========================================================
with tab_daily:
    st.subheader("⏰ Automated Daily 6:00 PM Recommendation & Prediction Dispatcher")
    st.caption("Autonomous daily background dispatches scheduled for 6:00 PM (18:00 IST) every evening. When armed, the system scans all registered students across all sections, runs the latest AI predictions, compiles course recommendations, and transmits live Email notifications.")

    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST)

    dispatch_info = get_last_dispatch_info()
    curr_enabled = is_daily_6pm_dispatch_enabled()

    with st.container(border=True):
        col_toggle, col_meta = st.columns([1, 2])

        with col_toggle:
            st.markdown("#### Autonomous Scheduler Switch")
            new_enabled = st.toggle("Enable Daily 6:00 PM Dispatcher", value=curr_enabled)
            if new_enabled != curr_enabled:
                set_daily_6pm_dispatch_enabled(new_enabled)
                st.success(f"Daily 6:00 PM Dispatcher is now {'ENABLED' if new_enabled else 'DISABLED'}.")
                st.rerun()

            status_badge = "🟢 ARMED & RUNNING" if new_enabled else "🔴 INACTIVE"
            st.markdown(f"**Current Status:** `{status_badge}`")

            st.markdown("---")
            st.markdown("#### Delivery Channels for 6:00 PM Batch")
            curr_email_on = is_daily_6pm_email_enabled()
            new_email_on = st.toggle("📧 Send Automated Emails", value=curr_email_on)
            if new_email_on != curr_email_on:
                set_daily_6pm_email_enabled(new_email_on)
                st.rerun()

            curr_wa_on = is_daily_6pm_whatsapp_enabled()
            new_wa_on = st.toggle("💬 Send Automated WhatsApp Messages", value=curr_wa_on)
            if new_wa_on != curr_wa_on:
                set_daily_6pm_whatsapp_enabled(new_wa_on)
                st.rerun()

        with col_meta:
            st.markdown("#### Automated Schedule Metrics (IST / UTC+5:30)")
            st.write(f"• **Current Indian Standard Time (IST):** `{now_ist.strftime('%I:%M:%S %p (%d %b %Y)')}`")
            st.write(f"• **Fixed Daily Dispatch Time:** `6:00 PM (18:00 IST)`")
            st.write(f"• **Active Channels:** `{'Email' if is_daily_6pm_email_enabled() else ''} {'+ WhatsApp' if is_daily_6pm_whatsapp_enabled() else ''}`")
            st.write(f"• **Last Dispatch Date:** `{dispatch_info['last_date']}`")
            st.write(f"• **Last Dispatch Timestamp:** `{dispatch_info['last_time']}`")
            st.write(f"• **Last Run Summary:** {dispatch_info['last_summary']}")

    today_str = now_ist.date().isoformat()
    already_run_today = (dispatch_info["last_date"] == today_str)

    st.markdown("#### ⚡ Manual Trigger for Today's Scheduled Batch")
    if already_run_today:
        st.info(f"ℹ️ Today's daily 6:00 PM batch has already completed on `{dispatch_info['last_time']}`. You can force-rerun below if needed.")
    else:
        st.warning(f"⚠️ Today's 6:00 PM batch has not run yet. The autonomous scheduler will trigger it automatically at 18:00 IST (current time: {now_ist.strftime('%I:%M %p IST')}).")

    if st.button("⚡ Run Today's 6:00 PM Batch Immediately", type="secondary", use_container_width=True):
        send_e = is_daily_6pm_email_enabled()
        send_w = is_daily_6pm_whatsapp_enabled()
        with st.spinner("Executing scheduled daily recommendations & predictions batch..."):
            res = dispatch_student_recommendations_and_predictions(
                section=None,
                send_email_flag=send_e,
                send_whatsapp_flag=send_w,
                is_scheduled_daily=True,
            )
        if res.get("success"):
            st.success(f"✅ {res.get('message')}")
            st.rerun()
        else:
            st.error(f"❌ Scheduled run failed: {res.get('message')}")

# =========================================================
# TAB 3: SECTION ATTENDANCE NOTIFICATION CENTER
# =========================================================
with tab_att:
    st.subheader("📋 Section Classroom Attendance Notifications")
    st.caption("When faculty members record and lock classroom attendance for a section, the system automatically sends Email and WhatsApp alerts to students of that respective section with their status (Present / Absent) and updated attendance percentage.")

    curr_att_enabled = is_auto_attendance_enabled()
    with st.container(border=True):
        col_att_toggle, col_att_info = st.columns([1, 2])
        with col_att_toggle:
            st.markdown("#### Auto-Attendance Switch")
            new_att_enabled = st.toggle("Auto-notify on Faculty Attendance Submission", value=curr_att_enabled)
            if new_att_enabled != curr_att_enabled:
                set_auto_attendance_enabled(new_att_enabled)
                st.success(f"Auto-Attendance notifications are now {'ENABLED' if new_att_enabled else 'DISABLED'}.")
                st.rerun()
        with col_att_info:
            st.markdown("#### Notification Policy")
            st.write("• **Present Students:** Receive confirmation email and WhatsApp with cumulative attendance %.")
            st.write("• **Absent Students:** Receive high-priority warning email + WhatsApp, plus mandatory parent WhatsApp alerts.")
            st.write("• **Institutional Sender:** `forestnation08@gmail.com` (AI Academic Decision System).")

    st.markdown("#### 📅 Recorded Attendance Sessions")
    conn = get_connection()
    sessions = []
    try:
        sessions = conn.execute(
            """
            SELECT s.session_id, s.session_date, s.timetable_id, s.created_at,
                   t.section, t.day, t.slot,
                   c.course_name, COALESCE(c.catalog_code, c.course_code) AS course_code,
                   f.full_name AS faculty_name,
                   COUNT(r.student_id) AS total_marked,
                   SUM(r.is_present) AS present_count
            FROM attendance_sessions s
            JOIN timetable t ON t.timetable_id = s.timetable_id
            JOIN courses c ON c.course_id = t.course_id
            LEFT JOIN faculty f ON f.faculty_id = s.faculty_id
            LEFT JOIN attendance_session_records r ON r.session_id = s.session_id
            GROUP BY s.session_id
            ORDER BY s.session_date DESC, s.session_id DESC
            LIMIT 30
            """
        ).fetchall()
    except Exception as e:
        print(f"Notice: attendance_sessions query fallback: {e}")
        sessions = []
    finally:
        conn.close()

    if not sessions:
        st.info("No classroom attendance sessions have been submitted by faculty yet.")
    else:
        sess_rows = []
        for s in sessions:
            sd = dict(s)
            tot = sd.get("total_marked") or 0
            pres = sd.get("present_count") or 0
            absent = tot - pres
            sess_rows.append({
                "Session ID": sd["session_id"],
                "Date": sd["session_date"],
                "Section": f"Section {sd['section']}",
                "Course": f"{sd['course_code']} - {sd['course_name']}",
                "Faculty": sd["faculty_name"] or "Faculty Instructor",
                "Total Marked": tot,
                "Present": pres,
                "Absent": absent,
                "Submitted At": sd.get("created_at") or "—",
            })

        st.dataframe(pd.DataFrame(sess_rows), use_container_width=True, hide_index=True)

        st.markdown("##### ✉️ Resend Notifications for a Submitted Session")
        sel_sess_map = {
            f"Session #{r['Session ID']} · {r['Section']} · {r['Course']} ({r['Date']})": r["Session ID"]
            for r in sess_rows
        }
        chosen_sess_label = st.selectbox("Choose Session to Resend Alerts", list(sel_sess_map.keys()))
        chosen_sess_id = sel_sess_map[chosen_sess_label]

        if st.button("📤 Resend Email & WhatsApp to This Section", type="primary"):
            with st.spinner("Resending session attendance notifications..."):
                res = dispatch_section_attendance_notifications(chosen_sess_id)
            if res.get("success"):
                st.success(f"✅ {res.get('message')}")
            else:
                st.error(f"❌ Failed: {res.get('message')}")

# =========================================================
# TAB 4: OUTBOUND AUDIT LOGS
# =========================================================
with tab_logs:
    st.subheader("📜 Real-World Outbound Delivery Audit Logs")
    st.caption("Immutable transaction ledger recording every Email and WhatsApp message transmitted by the system.")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        chan_filter = st.selectbox("Filter Channel", ["All", "Email", "WhatsApp"])
    with filter_col2:
        log_limit = st.slider("Max Logs to Display", min_value=20, max_value=200, value=50, step=10)

    conn = get_connection()
    q = "SELECT log_id, recipient_type, recipient_name, recipient_contact, channel, sender_email, subject, message, status, error_message, created_at FROM communication_logs"
    p = []
    if chan_filter != "All":
        q += " WHERE channel = ?"
        p.append(chan_filter)
    q += " ORDER BY log_id DESC LIMIT ?"
    p.append(log_limit)

    logs = conn.execute(q, p).fetchall()
    conn.close()

    if logs:
        st.dataframe(pd.DataFrame([dict(r) for r in logs]), use_container_width=True, hide_index=True)
    else:
        st.info("No outbound communication logs recorded yet.")
