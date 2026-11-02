"""
===========================================================
AI-Based Autonomous Academic Decision System
Domain: Artificial Intelligence + Machine Learning + Data Analytics
Real-world Application: Self-learning ERP Intelligence
Theme: AI Academic Governance
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
Institutional Student ERP Portal (Modeled after IFHE Academic System)
===========================================================
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib
import database
if not hasattr(database, "get_student_detailed_course_attendance") or not hasattr(database, "ensure_enterprise_erp_tables"):
    importlib.reload(database)

from auth import require_student
from database import (
    get_student_detailed_course_attendance,
    get_student_recent_attendance_sessions,
    ensure_enterprise_erp_tables,
    get_connection,
    submit_student_grievance,
    get_student_grievances,
    submit_student_leave_request,
    get_student_leave_requests,
    ensure_course_feedback_table,
    submit_course_feedback,
    get_student_submitted_feedback,
    get_student_by_roll,
    get_student_semester_registration,
    get_student_registered_courses,
    get_student_course_assessments,
    get_student_timetable,
    get_published_semester_structures,
    get_courses_for_semester_structure,
    get_section_capacity,
    register_student_for_semester,
    get_student_notifications,
    mark_student_notifications_read,
    get_latest_model_training_run,
    get_academic_policies,
    get_student_semester_fees,
    get_student_fee_statements,
    get_student_fines,
    pay_student_fine,
    get_student_refund_requests,
    submit_refund_request,
    update_student_contact_info,
    get_system_announcements,
    ACADEMIC_DAYS,
    ACADEMIC_PERIODS,
)
from prediction import (
    predict_student_comprehensive,
    are_course_models_trained,
    get_latest_model_evaluation,
    explain_student_academic_prediction,
    simulate_student_academic_outcomes,
)
from recommendation_engine import generate_course_level_recommendations, generate_recommendation
from email_service import (
    get_configured_admin_email,
    is_email_service_active,
)
from sms_service import (
    is_sms_service_configured,
)


def render_student_confusion_matrix_section(eval_data, model_type="performance"):
    """Render interactive confusion matrix and classification report in student portal."""
    if not eval_data:
        return

    if model_type == "performance":
        title = "🎯 Course Performance Confusion Matrix (Distinction / Pass / Fail)"
        cm_data = eval_data.get("performance_confusion_matrix", {})
        report_data = eval_data.get("performance_report", {})
        acc = eval_data.get("performance_accuracy", 0.0)
    else:
        title = "🚨 Academic Risk Classification Confusion Matrix (Low / Medium / High)"
        cm_data = eval_data.get("risk_confusion_matrix", {})
        report_data = eval_data.get("risk_report", {})
        acc = eval_data.get("risk_accuracy", 0.0)

    matrix = cm_data.get("matrix", [])
    labels = cm_data.get("labels", [])

    st.markdown(f"###### {title}")
    st.caption(f"Stratified Holdout Evaluation Accuracy: **{acc:.1%}**")

    if matrix and labels:
        col_names = [f"Pred {lbl}" for lbl in labels]
        row_names = [f"Actual {lbl}" for lbl in labels]
        cm_df = pd.DataFrame(matrix, index=row_names, columns=col_names)
        st.dataframe(cm_df, use_container_width=True)

        if report_data:
            rep_rows = []
            for lbl in labels:
                if lbl in report_data:
                    m = report_data[lbl]
                    rep_rows.append({
                        "Class Category": lbl,
                        "Precision": f"{m.get('precision', 0):.1%}",
                        "Recall (Sensitivity)": f"{m.get('recall', 0):.1%}",
                        "F1-Score": f"{m.get('f1-score', 0):.3f}",
                        "Test Support": int(m.get('support', 0)),
                    })
            if rep_rows:
                st.dataframe(pd.DataFrame(rep_rows), use_container_width=True, hide_index=True)


require_student()

session_student = dict(st.session_state.user_data or {})
roll_no = session_student.get("roll_number")
raw_student = (get_student_by_roll(roll_no) if roll_no else None) or session_student
student = dict(raw_student) if raw_student else {}
st.session_state.user_data = student
st.session_state.user = student

if not student or "student_id" not in student:
    st.info("Please log in as a student to access the institutional academic portal.")
    st.stop()

student_id = student["student_id"]
current_year = int(student.get("current_year") or 1)
current_semester = int(student.get("semester") or 1)
assigned_section = student.get("section") or "Unassigned"
department = student.get("department", "Engineering & Technology")
full_name = student.get("full_name", "Student")
roll_number = student.get("roll_number", "N/A")
enrollment_number = student.get("enrollment_no") or f"26IFHE{student_id:04d}"
student_phone = student.get("phone") or "Not Registered"
student_email = student.get("email") or "Not Registered"

# Fetch Registration Status
raw_reg = get_student_semester_registration(student_id, current_semester)
semester_reg = dict(raw_reg) if raw_reg else None
is_registered = bool(semester_reg and semester_reg.get("status") == "Registered")

# Fetch Notifications
notifications = get_student_notifications(student_id)
unread_count = sum(not n["is_read"] for n in notifications)

# Fetch System Announcements
system_announcements = get_system_announcements("Student")

# -------------------------------------------------------------
# TOP INSTITUTIONAL HEADER BANNER (ICFAI IFHE Style)
# -------------------------------------------------------------
st.markdown(
    f"""
    <div class="ifhe-header-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div class="ifhe-uni-title">AI ACADEMIC DECISION SYSTEM</div>
                <div class="ifhe-uni-subtitle">Autonomous Academic Governance & Institutional ERP Platform</div>
                <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.4rem; flex-wrap: wrap;">
                    <span class="ifhe-portal-tag">Faculty of Science & Technology</span>
                    <span class="ifhe-portal-tag" style="background: rgba(255, 215, 0, 0.2); border-color: rgba(255, 215, 0, 0.4); color: #fff;">Autonomous Academic Decision & ERP Portal</span>
                    <span class="ifhe-portal-tag" style="background: rgba(16, 185, 129, 0.2); border-color: rgba(16, 185, 129, 0.4); color: #6ee7b7;">Academic Year 2026–27</span>
                </div>
            </div>
            <div class="student-profile-chip" style="min-width: 280px;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 44px; height: 44px; border-radius: 50%; background: #ffd166; color: #091e3a; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; border: 2px solid #ffffff;">
                        {full_name[:2].upper()}
                    </div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.05rem; letter-spacing: 0.02em;">{full_name}</div>
                        <div style="font-size: 0.8rem; color: #cbd5e1; font-family: monospace;">Roll No: {roll_number}</div>
                    </div>
                </div>
                <div style="margin-top: 0.6rem; font-size: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.15); padding-top: 0.4rem; display: flex; justify-content: space-between;">
                    <span><b>{department}</b></span>
                    <span style="color: {'#34d399' if is_registered else '#fbbf24'}; font-weight: 600;">
                        {'● Registered' if is_registered else '○ Registration Pending'}
                    </span>
                </div>
                <div style="font-size: 0.75rem; color: #e2e8f0; margin-top: 0.2rem;">
                    Year {current_year} · Semester {current_semester} · Section {assigned_section}
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Broadcast Institutional Announcements Banner if available
if system_announcements:
    top_ann = system_announcements[0]
    prio_color = "#dc2626" if top_ann["priority"] == "Urgent" else ("#d97706" if top_ann["priority"] == "High" else "#2563eb")
    st.markdown(
        f"""
        <div style="background: #ffffff; border-left: 5px solid {prio_color}; border-radius: 8px; padding: 0.8rem 1.1rem; margin-bottom: 1.2rem; box-shadow: 0 2px 6px rgba(0,0,0,0.04); border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">📢 {top_ann['title']}</span>
                <span style="font-size: 0.75rem; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; color: #475569;">From {top_ann['created_by']}</span>
            </div>
            <p style="margin: 0.35rem 0 0 0; font-size: 0.88rem; color: #334155; line-height: 1.4;">{top_ann['content']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Top Bar Action Links
nav_col1, nav_col2, nav_col3 = st.columns([6, 2, 2])
with nav_col1:
    st.caption(f"Student Connected: **{student_email}** | Mobile: **{student_phone}**")
with nav_col2:
    if unread_count > 0:
        st.info(f"🔔 {unread_count} unread notifications")
with nav_col3:
    if st.button("Log out of portal", use_container_width=True):
        st.session_state.clear()
        st.rerun()

with st.sidebar:
    st.markdown("### 🎓 Student Workspace")
    st.write(f"**{full_name}**")
    st.caption(f"Roll No: `{roll_number}`")
    st.caption(f"Enrollment: `{enrollment_number}`")
    st.caption(f"Dept: {department}")
    st.divider()
    st.markdown("### 🧭 Student Navigation")
    student_nav = st.radio(
        "Student Navigation",
        [
            "🏛️ Portal Overview",
            "🎫 Examination Hall Ticket & Admit Card",
            "👤 Personal & Parent Details",
            "💳 Fee Payment & Ledger",
            "📚 Academic Curriculum",
            "⭐ Course & Faculty Feedback",
            "⚖️ Academic Grievances & Redressal",
            "🏥 On-Duty (OD) & Leave Application",
            "📊 Continuous Internal Evaluation (CIE /60)",
            "🎛️ What-If Grade & CIE Simulator",
            "📅 Course Attendance & Timetable",
            "🧠 AI Decision Engine & XAI",
            "🎯 Targeted Recommendations & Alerts",
            f"🔔 Notifications ({unread_count})",
        ],
        index=0,
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("#### 📧 Outbound Real Services")
    st.caption(f"Admin: `{get_configured_admin_email()}`")
    st.caption(f"Personal Phone: `{student_phone}`")
    st.divider()
    if st.button("🚪 Logout", key="student_sidebar_logout", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

# -------------------------------------------------------------
# STRICT SEMESTER REGISTRATION ENFORCEMENT GUARD
# -------------------------------------------------------------
if not is_registered:
    st.markdown(
        """
        <div class="statutory-alert-box">
            <h3 style="color: #b91c1c; margin-top: 0;">⚠️ SEMESTER REGISTRATION REQUIRED</h3>
            <p style="margin-bottom: 0.5rem; font-size: 0.95rem; line-height: 1.5;">
                You are currently <b>NOT REGISTERED</b> for <b>Year 1, Semester 1 (Batch 2026–27)</b>.
                Under Institutional Academic Regulations and the university ERP workflow:
            </p>
            <ul style="margin-bottom: 0.5rem; font-size: 0.9rem;">
                <li><b>No Continuous Internal Evaluation (CIE)</b> (Mid Exam 30, Assignment 10, Quiz 10, Viva Voce 10) can be posted.</li>
                <li><b>No End-Semester External marks (40)</b> can be awarded.</li>
                <li><b>Weekly Timetable and Course Attendance sessions</b> are not accessible.</li>
                <li><b>AI Academic Decision & Risk Predictions</b> are locked until curriculum enrollment is finalized.</li>
            </ul>
            <p style="margin-bottom: 0; font-weight: 600; color: #991b1b;">
                Please complete your formal semester registration below to unlock your courses, gradebook, timetable, and AI recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Official Semester Registration Wizard")
    structures = get_published_semester_structures(department, current_year)
    if not structures:
        st.error(
            f"No published curriculum structure was found for Year {current_year}, Semester {current_semester} in {department}. "
            "Please contact the Academic Dean / Examination Branch."
        )
        st.stop()

    structure_options = {
        f"Year {row['year']} · Semester {row['semester']} · Academic Batch {row['academic_batch']}": row
        for row in structures
    }
    selected_label = st.selectbox("Select Academic Offering", list(structure_options))
    selected_structure = structure_options[selected_label]
    structure_courses = get_courses_for_semester_structure(selected_structure["structure_id"])

    st.markdown("#### Accredited Semester Curriculum")
    if structure_courses:
        st.dataframe(
            pd.DataFrame([
                {
                    "Course Code": c["course_code"],
                    "Course Name": c["course_name"],
                    "Credits": c["credits"],
                    "Course Type": c["course_type"],
                    "Max Internal": 60,
                    "Max External": 40,
                    "Total Marks": 100,
                }
                for c in structure_courses
            ]),
            use_container_width=True,
            hide_index=True,
        )
        total_credits = sum(float(c["credits"]) for c in structure_courses)
        st.caption(f"Total Prescribed Credits: **{total_credits} Credits** across **{len(structure_courses)} Courses**.")

    st.markdown("#### Section Allocation & Seat Capacity")
    sec_cols = st.columns(5)
    for idx, sec in enumerate(["A", "B", "C", "D", "E"]):
        cap = get_section_capacity(department, current_year, sec)
        sec_cols[idx].metric(f"Section {sec}", f"{cap['enrolled']}/50 Enrolled", delta=f"{cap['available']} Seats Open")

    preferred_section = st.selectbox("Confirm Preferred Section Assignment", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"], index=0)

    if st.button("Complete Formal Semester Registration", type="primary"):
        reg_id = register_student_for_semester(student_id, selected_structure["structure_id"], preferred_section)
        st.success(f"Semester registration completed successfully! Enrollment assigned to Section {preferred_section}.")
        st.rerun()

    st.stop()


# -------------------------------------------------------------
# FETCH REGISTERED STUDENT ACADEMIC DATA
# -------------------------------------------------------------
registered_courses = get_student_registered_courses(student_id)
course_assessments = get_student_course_assessments(student_id)
timetable_slots = get_student_timetable(student_id)
latest_model_run = get_latest_model_training_run()
latest_eval = get_latest_model_evaluation()
academic_policies = get_academic_policies()
semester_fees = get_student_semester_fees(student_id)

policy_att_thresh = float(academic_policies.get("attendance_threshold", 75.0))
policy_crit_int = float(academic_policies.get("critical_internal_threshold", 24.0))
predictions_enabled = bool(academic_policies.get("predictions_enabled", 1))

comprehensive_pred = predict_student_comprehensive(student_id)
active_algo = academic_policies.get("active_ml_algorithm") or (latest_eval.get("algorithm") if latest_eval else "Random Forest")
policy_crit_score = float(latest_eval.get("critical_score", 40.0)) if latest_eval else 40.0

total_credits = sum(float(c.get("credits") or 0) for c in registered_courses) if registered_courses else 20.0
overall_attendance = float(student.get("attendance_percentage") or 0.0)

# Calculate Gradebook Averages
if course_assessments:
    valid_internals = [float(a["internal_total"]) for a in course_assessments if a.get("internal_total") is not None]
    valid_externals = [float(a["external_marks"]) for a in course_assessments if a.get("external_marks") is not None]
    valid_totals = [float(a["overall_total"]) for a in course_assessments if a.get("overall_total") is not None]
    avg_internal = sum(valid_internals) / len(valid_internals) if valid_internals else None
    avg_external = sum(valid_externals) / len(valid_externals) if valid_externals else None
    avg_total = sum(valid_totals) / len(valid_totals) if valid_totals else None
else:
    avg_internal = float(student.get("internal_marks")) if student.get("internal_marks") is not None else None
    avg_external = float(student.get("external_marks")) if student.get("external_marks") is not None else None
    avg_total = (avg_internal + avg_external) if (avg_internal is not None and avg_external is not None) else None

cgpa_val = float(student.get("cgpa") or (avg_total / 10.0 if avg_total else 0.0))
overall_perf = comprehensive_pred.get("overall_performance", "Evaluating")
overall_risk = comprehensive_pred.get("overall_risk", "Medium")

# -------------------------------------------------------------
# TOP QUICK KPI METRICS BAR
# -------------------------------------------------------------
kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.metric(
        "Continuous Internal (CIE)",
        f"{avg_internal:.1f} / 60" if avg_internal is not None else "Pending",
        delta="Passing (≥24/60)" if (avg_internal or 0) >= 24.0 else "Remedial Attention",
        delta_color="normal" if (avg_internal or 0) >= 24.0 else "inverse",
        help="Aggregated Continuous Internal Evaluation: Mid (30) + Assignment (10) + Quiz (10) + Viva (10)",
    )
with kpi_cols[1]:
    st.metric(
        "Attendance",
        f"{overall_attendance:.1f}%",
        delta=f"Eligible (≥{policy_att_thresh:.0f}%)" if overall_attendance >= policy_att_thresh else f"⚠️ Shortage (<{policy_att_thresh:.0f}%)",
        delta_color="normal" if overall_attendance >= policy_att_thresh else "inverse",
    )
with kpi_cols[2]:
    cie_standing = "Good Standing" if (avg_internal or 0) >= 30 and overall_attendance >= policy_att_thresh else ("Remedial Watch" if (avg_internal or 0) >= 24 else "Critical Intervention")
    st.metric(
        "CIE Standing",
        cie_standing,
        delta="In-Semester Status",
    )
with kpi_cols[3]:
    st.metric(
        "Evaluation Model",
        "Pure Continuous (CIE)",
        delta="Grades & CGPA Removed",
        help="Evaluates students exclusively on continuous in-semester coursework for early proactive advising.",
    )
with kpi_cols[4]:
    if not predictions_enabled:
        st.metric(
            "AI Risk Radar",
            "⏸️ Paused",
            delta="Recalibrating",
            help="AI predictions temporarily paused by Academic Administration for model recalibration",
        )
    else:
        risk_color = "🟢" if overall_risk == "Low" else ("🟡" if overall_risk == "Medium" else "🔴")
        st.metric(
            "AI Risk Radar",
            f"{risk_color} {overall_risk} Risk",
            delta=f"Forecast: {overall_perf}",
        )


# -------------------------------------------------------------
# MAIN DASHBOARD TABS
# -------------------------------------------------------------
# Student Portal Navigation View (Controlled via Sidebar)
# Active view selected from sidebar: student_nav

# =============================================================
# TAB 1: PORTAL OVERVIEW
# =============================================================
# =============================================================
# TAB: EXAMINATION HALL TICKET & ADMIT CARD
# =============================================================
if student_nav == "🎫 Examination Hall Ticket & Admit Card":
    st.subheader("🎫 Institutional Examination Hall Ticket & Admit Card")
    st.caption("Official statutory examination authorization issued by the Office of the Controller of Examinations.")

    # Statutory compliance check: Attendance >= 75.0%
    curr_att = float(student.get("attendance_percentage") or 0.0)
    is_att_compliant = curr_att >= 75.0

    if not is_registered:
        st.error("⛔ **ADMIT CARD WITHHELD:** You have not completed Semester Registration for Batch 2026–27.")
    elif not is_att_compliant:
        st.error(
            f"⛔ **STATUTORY ATTENDANCE DEBARMENT:** Your recorded attendance is **{curr_att:.1f}%**, which is below "
            f"the institutional mandatory threshold of **75.0%**. In accordance with university academic regulations, "
            f"you are currently ineligible to appear for the End-Semester External Examinations."
        )
        st.info("💡 **Next Steps:** Submit an Academic Grievance or consult your Academic Mentor regarding statutory attendance remediation.")
    else:
        st.success("✅ **ELIGIBILITY VERIFIED:** You have satisfied all statutory attendance and curriculum requirements for End-Semester Examinations.")

        # Institutional Hall Ticket Layout
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 0.8rem; margin-bottom: 1rem;">
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a; letter-spacing: 0.05em;">ICFAI FOUNDATION FOR HIGHER EDUCATION (IFHE)</div>
                    <div style="font-size: 0.88rem; color: #475569; font-weight: 600;">FACULTY OF SCIENCE & TECHNOLOGY — HYDERABAD</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #1e3a8a; margin-top: 0.4rem; background: #e0e7ff; display: inline-block; padding: 2px 14px; border-radius: 4px;">
                        END-SEMESTER EXTERNAL EXAMINATION ADMIT CARD (BATCH 2026–27)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_info1, c_info2, c_photo = st.columns([1.5, 1.5, 1])
            with c_info1:
                st.markdown(f"**Candidate Name:** {full_name}")
                st.markdown(f"**Roll Number:** `{roll_number}`")
                st.markdown(f"**Enrollment No:** `{enrollment_number}`")
                st.markdown(f"**Department:** {department}")
            with c_info2:
                st.markdown(f"**Program:** B.Tech (Honors)")
                st.markdown(f"**Year / Semester:** Year {current_year} · Sem {current_semester}")
                st.markdown(f"**Assigned Section:** Section {assigned_section}")
                st.markdown(f"**Statutory Attendance:** **{curr_att:.1f}% (Compliant)**")
            with c_photo:
                st.markdown(
                    f"""
                    <div style="border: 2px dashed #94a3b8; border-radius: 8px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f8fafc;">
                        <span style="font-size: 1.8rem; font-weight: 700; color: #1e293b;">{full_name[:2].upper()}</span>
                        <span style="font-size: 0.7rem; color: #64748b; margin-top: 4px;">Verified Photo ID</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.divider()

            st.markdown("##### 📅 Scheduled Theory & Practical Examination Timetable")
            registered_courses = get_student_registered_courses(student_id, current_semester)
            exam_schedule = [
                {"Date": "14-Dec-2026", "Session": "Morning (09:30 AM – 12:30 PM)", "Course Code": "CS101", "Course Title": "Computer Programming & Problem Solving", "Exam Venue": "Auditorium Block - Hall A-102", "Invigilator Sign": "______________"},
                {"Date": "16-Dec-2026", "Session": "Morning (09:30 AM – 12:30 PM)", "Course Code": "MA101", "Course Title": "Mathematics I (Linear Algebra & Calculus)", "Exam Venue": "Auditorium Block - Hall A-104", "Invigilator Sign": "______________"},
                {"Date": "18-Dec-2026", "Session": "Morning (09:30 AM – 12:30 PM)", "Course Code": "PH101", "Course Title": "Applied Engineering Physics", "Exam Venue": "Science Block - Hall S-201", "Invigilator Sign": "______________"},
                {"Date": "21-Dec-2026", "Session": "Morning (09:30 AM – 12:30 PM)", "Course Code": "EE101", "Course Title": "Basic Electrical Sciences", "Exam Venue": "Tech Block - Hall T-302", "Invigilator Sign": "______________"},
                {"Date": "23-Dec-2026", "Session": "Afternoon (02:00 PM – 05:00 PM)", "Course Code": "CS102", "Course Title": "Programming Laboratory Practical Exam", "Exam Venue": "Computing Lab 4", "Invigilator Sign": "______________"},
            ]
            st.dataframe(pd.DataFrame(exam_schedule), use_container_width=True, hide_index=True)

            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #cbd5e1;">
                    <div style="font-size: 0.75rem; color: #64748b; font-family: monospace;">
                        SECURE DIGITAL VERIFICATION TOKEN: [IFHE-COE-2026-AUTONOMOUS-VERIFIED-SEAL]<br>
                        Generated: November 2026 | Candidate Signature: _______________________
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 700; font-size: 0.9rem; color: #0f172a;">Controller of Examinations</div>
                        <div style="font-size: 0.75rem; color: #475569;">IFHE University Hyderabad</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.download_button(
            "📥 Print / Export Official Examination Hall Ticket (PDF)",
            data=f"ICFAI Foundation for Higher Education\nExamination Admit Card 2026-27\nCandidate: {full_name} ({roll_number})\nDepartment: {department}\nAttendance: {curr_att:.1f}% (Statutory Compliant)",
            file_name=f"hall_ticket_{roll_number}.txt",
            mime="text/plain",
            use_container_width=True
        )


# =============================================================
# TAB: ACADEMIC GRIEVANCES & REDRESSAL
# =============================================================
elif student_nav == "⚖️ Academic Grievances & Redressal":
    st.subheader("⚖️ Academic Grievance & Marks Scrutiny Redressal Desk")
    st.caption("Official university portal for lodging continuous evaluation disputes, marks scrutiny requests, and attendance reconciliations.")

    tab_lodge, tab_g_track = st.tabs([
        "📝 Lodge New Academic Grievance",
        "📋 Grievance Tracking & Resolution Status"
    ])

    with tab_lodge:
        with st.form("student_lodge_grievance_form"):
            g_type = st.selectbox(
                "Grievance Category",
                [
                    "CIE Marks Scrutiny (Mid Exam / Assignment / Quiz / Viva)",
                    "Attendance Discrepancy / Biometric Reconciliation",
                    "Continuous Assessment Question Paper Ambiguity",
                    "General Academic Counseling Request"
                ]
            )
            g_title = st.text_input("Grievance Headline", placeholder="e.g. Discrepancy in Mid-1 Question 3 Marking")
            
            registered_courses = get_student_registered_courses(student_id, current_semester)
            c_opts = {"General / None": None}
            for c in registered_courses:
                c_opts[f"{c['course_code']} - {c['course_name']}"] = c["course_id"]
            
            sel_c_label = st.selectbox("Relevant Course Subject", list(c_opts.keys()))
            chosen_c_id = c_opts[sel_c_label]

            g_desc = st.text_area(
                "Detailed Description & Justification",
                placeholder="Explain the specific discrepancy, date of assessment, question number, or attendance session...",
                height=120
            )

            submit_g_btn = st.form_submit_button("🚀 Submit Formal Grievance", type="primary", use_container_width=True)
            if submit_g_btn:
                if not g_title.strip() or not g_desc.strip():
                    st.error("Please provide both a headline and detailed description.")
                else:
                    success = submit_student_grievance(
                        student_id=student_id,
                        grievance_type=g_type,
                        title=g_title.strip(),
                        description=g_desc.strip(),
                        course_id=chosen_c_id
                    )
                    if success:
                        st.success("🎉 Your grievance has been officially registered with the Academic Review Committee.")
                        st.rerun()
                    else:
                        st.error("Failed to submit grievance. Please try again.")

    with tab_g_track:
        my_grievances = get_student_grievances(student_id=student_id)
        if not my_grievances:
            st.info("You have not lodged any academic grievances.")
        else:
            for g in my_grievances:
                with st.container(border=True):
                    g_c1, g_c2 = st.columns([3, 1])
                    with g_c1:
                        st.markdown(f"**Grievance #{g['grievance_id']} · {g['title']}**")
                        st.caption(f"Category: {g['grievance_type']} | Course: {g.get('course_name', 'General')} | Lodged: {g['created_at']}")
                        st.write(g["description"])
                    with g_c2:
                        status_color = "#16a34a" if g["status"] == "Resolved" else ("#2563eb" if g["status"] == "Under Evaluation" else "#d97706")
                        st.markdown(f"<span style='background: {status_color}; color: white; padding: 3px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;'>{g['status']}</span>", unsafe_allow_html=True)

                    if g.get("faculty_remarks"):
                        st.markdown(f"**Reviewer Remarks:** *{g.get('faculty_remarks', '')}*")


# =============================================================
# TAB: ON-DUTY (OD) & LEAVE APPLICATION
# =============================================================
elif student_nav == "🏥 On-Duty (OD) & Leave Application":
    st.subheader("🏥 On-Duty (OD) Attendance & Medical Leave Portal")
    st.caption("Apply for excused institutional absences (Hackathons, Sports, Medical) to maintain statutory attendance compliance.")

    tab_apply_od, tab_od_status = st.tabs([
        "📝 Submit Leave / OD Application",
        "📋 Leave Application History & Status"
    ])

    with tab_apply_od:
        with st.form("student_leave_application_form"):
            l_type = st.selectbox(
                "Leave / OD Classification",
                [
                    "On-Duty (Hackathon / Technical Competition / Paper Presentation)",
                    "On-Duty (Inter-University Sports / Cultural Representation)",
                    "Medical Leave (Inpatient / Outpatient Hospitalization)",
                    "Special Bereavement / Family Emergency"
                ]
            )
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                f_date = st.date_input("From Date")
            with col_d2:
                t_date = st.date_input("To Date")

            l_reason = st.text_area(
                "Detailed Purpose & Event / Hospitalization Details",
                placeholder="Mention event name, organizing institution, or medical diagnosis...",
                height=100
            )

            submit_l_btn = st.form_submit_button("🚀 Submit for Faculty & Departmental Approval", type="primary", use_container_width=True)
            if submit_l_btn:
                if not l_reason.strip():
                    st.error("Please provide a reason and event details.")
                elif f_date > t_date:
                    st.error("From Date cannot be later than To Date.")
                else:
                    success = submit_student_leave_request(
                        student_id=student_id,
                        leave_type=l_type,
                        from_date=str(f_date),
                        to_date=str(t_date),
                        reason=l_reason.strip()
                    )
                    if success:
                        st.success("🎉 Leave / OD Application submitted successfully. Awaiting Faculty review.")
                        st.rerun()
                    else:
                        st.error("Failed to submit application.")

    with tab_od_status:
        my_leaves = get_student_leave_requests(student_id=student_id)
        if not my_leaves:
            st.info("You have not submitted any Leave or On-Duty applications.")
        else:
            for l in my_leaves:
                with st.container(border=True):
                    lc1, lc2 = st.columns([3, 1])
                    with lc1:
                        st.markdown(f"**Application #{l['leave_id']} · {l['leave_type']}**")
                        st.caption(f"Duration: {l['from_date']} to {l['to_date']} | Applied: {l['created_at']}")
                        st.write(l["reason"])
                    with lc2:
                        l_color = "#16a34a" if l["status"] == "Approved" else ("#dc2626" if l["status"] == "Rejected" else "#d97706")
                        st.markdown(f"<span style='background: {l_color}; color: white; padding: 3px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;'>{l['status']}</span>", unsafe_allow_html=True)

                    if l.get("action_remarks"):
                        st.markdown(f"**Department Remarks:** *{l.get('action_remarks', '')}* (By {l.get('action_by', 'Faculty')})")


# =============================================================
# TAB: WHAT-IF GRADE & CIE SIMULATOR
# =============================================================
elif student_nav == "🎛️ What-If Grade & CIE Simulator":
    st.subheader("🎛️ Interactive 'What-If' CIE & Final Grade Simulator")
    st.caption("Forecast your end-semester letter grades by dynamically adjusting prospective scores on upcoming continuous assessments.")

    registered_courses = get_student_registered_courses(student_id, current_semester)
    if not registered_courses:
        st.info("Please register for courses to use the What-If Simulator.")
    else:
        c_names = {f"{c['course_code']} - {c['course_name']}": c for c in registered_courses}
        sel_sim_c = st.selectbox("Select Course for Simulation", list(c_names.keys()))
        sim_course = c_names[sel_sim_c]

        st.markdown("##### 🎚️ Adjust Simulated Assessment Scores")
        with st.container(border=True):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sim_mid = st.slider("Simulated Mid Exam (/30)", min_value=0.0, max_value=30.0, value=22.0, step=0.5)
            with sc2:
                sim_quiz = st.slider("Simulated Quizzes (/10)", min_value=0.0, max_value=10.0, value=8.5, step=0.5)
            with sc3:
                sim_assn = st.slider("Simulated Assignment (/10)", min_value=0.0, max_value=10.0, value=9.0, step=0.5)

            sc4, sc5 = st.columns(2)
            with sc4:
                sim_viva = st.slider("Simulated Viva Voce (/10)", min_value=0.0, max_value=10.0, value=7.5, step=0.5)
            with sc5:
                sim_see = st.slider("Projected End-Sem External Exam (/40)", min_value=0.0, max_value=40.0, value=30.0, step=1.0)

            total_cie = sim_mid + sim_quiz + sim_assn + sim_viva
            total_100 = total_cie + sim_see

            # Letter Grade Calculation
            if total_100 >= 90:
                grade, gpa, standing = "O (Outstanding)", 10.0, "University Gold Tier"
            elif total_100 >= 80:
                grade, gpa, standing = "A+ (Excellent)", 9.0, "First Class with Distinction"
            elif total_100 >= 70:
                grade, gpa, standing = "A (Very Good)", 8.0, "First Class"
            elif total_100 >= 60:
                grade, gpa, standing = "B+ (Good)", 7.0, "High Second Class"
            elif total_100 >= 50:
                grade, gpa, standing = "B (Above Average)", 6.0, "Second Class"
            elif total_100 >= 40:
                grade, gpa, standing = "C (Pass)", 5.0, "Passing Standard"
            else:
                grade, gpa, standing = "F (Remedial Fail)", 0.0, "Remedial Summer Term Required"

            st.divider()

            res_c1, res_c2, res_c3 = st.columns(3)
            res_c1.metric("Projected Total Score", f"{total_100:.1f} / 100", delta=f"{total_cie:.1f}/60 CIE")
            res_c2.metric("Projected Letter Grade", grade)
            res_c3.metric("Projected Grade Points", f"{gpa:.1f} CGPA Impact")

            if total_cie < 24.0:
                st.error("⚠️ **CIE In-Semester Deficit:** Your simulated Continuous Internal Evaluation is below the mandatory 24/60 passing benchmark.")
            else:
                st.success(f"🎉 **On-Track Trajectory:** Standing projected as **{standing}**.")


elif student_nav == "🏛️ Portal Overview":
    col_profile, col_highlights = st.columns([1.1, 1])

    with col_profile:
        st.markdown("### 🎓 Student Profile & Credentials")
        with st.container(border=True):
            pcol1, pcol2 = st.columns([1, 2])
            with pcol1:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #0d2f5d, #184e8e); color: white; border-radius: 12px; height: 130px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                        <span style="font-size: 2.2rem; font-weight: 800;">{full_name[:2].upper()}</span>
                        <span style="font-size: 0.75rem; color: #ffd166; margin-top: 0.2rem;">Year 1 Student</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with pcol2:
                st.markdown(f"**Full Name:** {full_name}")
                st.markdown(f"**Roll Number:** `{roll_number}`")
                st.markdown(f"**Enrollment No:** `{enrollment_number}`")
                st.markdown(f"**Assigned Section:** Section **{assigned_section}** (Strength: 50 Students)")

            st.divider()
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                st.write(f"**Program:** B.Tech (Honors)")
                st.write(f"**Batch:** 2026–2030 (Batch 2026-27)")
                st.write(f"**Department:** {department}")
            with dcol2:
                st.write(f"**Registered Credits:** {total_credits} Credits")
                st.write(f"**Admin:** `{get_configured_admin_email()}`")
                st.write(f"**Registration Status:** ● Verified & Active")

    with col_highlights:
        st.markdown("### 📈 Academic Health & Examination Eligibility")
        with st.container(border=True):
            if overall_attendance >= policy_att_thresh:
                st.markdown(
                    f"""
                    <div class="statutory-success-box">
                        <h4 style="color: #166534; margin: 0 0 0.4rem 0;">✅ Statutory Exam Eligibility: COMPLIANT</h4>
                        <p style="margin: 0; font-size: 0.88rem; color: #14532d;">
                            Your current attendance is <b>{overall_attendance:.1f}%</b>, exceeding the institutional mandatory threshold of {policy_att_thresh:.0f}%.
                            You are in good standing to appear for the End-Semester External Examinations.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="statutory-alert-box">
                        <h4 style="color: #991b1b; margin: 0 0 0.4rem 0;">⚠️ Statutory Exam Eligibility: SHORTAGE ALERT</h4>
                        <p style="margin: 0; font-size: 0.88rem; color: #7f1d1d;">
                            Your attendance is <b>{overall_attendance:.1f}%</b> (below the institutional {policy_att_thresh:.0f}% statutory minimum).
                            As per university regulations, you are at risk of being condoned or barred from End-Semester examinations unless class attendance is improved immediately.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.write(f"**Overall Academic Performance Trajectory:**")
            st.progress(min(max((cgpa_val / 10.0), 0.0), 1.0), text=f"Performance Index: {cgpa_val:.2f}/10.0 ({overall_perf})")

            st.write(f"**Continuous Internal Evaluation (CIE) Progress:**")
            if avg_internal is not None:
                st.progress(min(max((avg_internal / 60.0), 0.0), 1.0), text=f"Internal Marks: {avg_internal:.1f}/60 ({ (avg_internal/60)*100:.1f}%)")
            else:
                st.info("CIE marks will update once faculty submits assessments.")


# =============================================================
# TAB 2: PERSONAL & PARENT DETAILS
# =============================================================
elif student_nav == "👤 Personal & Parent Details":
    st.subheader("Student Personal & Parent Demographic Profile")
    st.caption("Official university records used for academic records, statutory verification, and notification dispatches.")

    col_pers, col_parent = st.columns(2)

    with col_pers:
        with st.container(border=True):
            st.markdown("#### 👤 Student Personal Details")
            st.write(f"**Full Name:** {student.get('full_name', '—')}")
            st.write(f"**Roll Number:** `{student.get('roll_number', '—')}`")
            st.write(f"**Enrollment No:** `{enrollment_number}`")
            st.write(f"**Student Phone Number:** `{student.get('phone', '—')}` 🟢 *Active for WhatsApp*")
            st.write(f"**Student Email Address:** `{student.get('email', '—')}` 🟢 *Active for Email*")
            st.write(f"**Date of Birth:** {student.get('date_of_birth') or '2005-06-14'}")
            st.write(f"**Blood Group:** `{student.get('blood_group') or 'O+'}`")
            st.write(f"**Nationality:** {student.get('nationality') or 'Indian'}")
            st.write(f"**Religion:** {student.get('religion') or 'Hindu'}")
            st.write(f"**Aadhar Number:** `{student.get('aadhar_no') or '7892-XXXX-1049'}` (Masked)")
            st.write(f"**Caste / Category:** {student.get('caste') or 'General'}")

    with col_parent:
        with st.container(border=True):
            st.markdown("#### 👨‍👩‍👦 Parent & Guardian Credentials")
            st.write(f"**Father / Guardian Name:** {student.get('parent_name') or student.get('father_name') or 'Guardian Name'}")
            st.write(f"**Mother's Name:** {student.get('mother_name') or 'Mrs. Guardian'}")
            st.write(f"**Parent Mobile Number:** `{student.get('parent_phone') or '+91 98480 12345'}` 🟢 *Active for WhatsApp Alerts*")
            st.write(f"**Parent Email Address:** `{student.get('parent_email') or 'parent@example.com'}`")
            st.write(f"**Residential Address:** {student.get('address') or 'Plot #42, Academic City, Hyderabad, Telangana - 500075'}")
            st.write(f"**Parent Qualification:** {student.get('parent_qualification') or 'B.Tech, MBA'}")
            st.write(f"**Parent Occupation:** {student.get('parent_occupation') or 'Senior Consultant'}")
            st.write(f"**Parent Organization:** {student.get('parent_organization') or 'State Administration / Corporate'}")

    # Interactive Form to Update Real-World Phone & Email
    st.markdown("### ✏️ Update Real-World Contact Numbers & Email")
    st.caption("Enter your actual personal phone number and personal email address to receive live WhatsApp notifications and AI recommendations.")

    with st.form("update_student_contact_form"):
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            new_phone = st.text_input("Student WhatsApp Number (for Real Alerts)", value=student.get("phone", ""))
            new_parent_phone = st.text_input("Parent WhatsApp Number", value=student.get("parent_phone", ""))
        with ecol2:
            new_email = st.text_input("Student Email Address (for Real Email Advisories)", value=student.get("email", ""))
            new_address = st.text_area("Residential Address", value=student.get("address", ""), height=70)

        contact_submitted = st.form_submit_button("💾 Save & Verify Real Contact Information", type="primary")
        if contact_submitted:
            if not new_phone or not new_email:
                st.error("Phone number and email address are mandatory.")
            else:
                ok = update_student_contact_info(
                    student_id=student_id,
                    phone=new_phone.strip(),
                    email=new_email.strip(),
                    address=new_address.strip() if new_address else None,
                    parent_phone=new_parent_phone.strip() if new_parent_phone else None,
                )
                if ok:
                    st.success("✅ Real contact details updated in institutional database! Live notifications will now dispatch to these addresses.")
                    st.rerun()
                else:
                    st.error("Could not update contact info. Please try again.")


# =============================================================
# TAB 3: FEE PAYMENT & LEDGER (STRUCTURE, SCHEDULE, RECEIPTS, STATEMENT, REFUND, FINES)
# =============================================================
elif student_nav == "💳 Fee Payment & Ledger":
    st.subheader("Academic Fee Management & Institutional Financial Ledger")
    st.caption("Official university accounting system covering accredited fee structures, payment schedules, receipts, account statements, refund claims, and penalty ledgers.")

    # Top Financial KPI Bar
    fee_stmts = get_student_fee_statements(student_id)
    student_fines = get_student_fines(student_id)
    refund_requests = get_student_refund_requests(student_id)

    total_debits = sum(float(r.get("debit_amount") or 0) for r in fee_stmts) if fee_stmts else 177000.0
    total_credits_paid = sum(float(r.get("credit_amount") or 0) for r in fee_stmts) if fee_stmts else 177000.0
    net_outstanding = max(0.0, total_debits - total_credits_paid)
    outstanding_fines = sum(float(f["amount"]) for f in student_fines if f["status"] == "Outstanding")

    kpi_f1, kpi_f2, kpi_f3, kpi_f4 = st.columns(4)
    kpi_f1.metric("Total Program Invoiced", f"₹{total_debits:,.2f}")
    kpi_f2.metric("Total Fees Cleared", f"₹{total_credits_paid:,.2f}", delta="Cleared" if net_outstanding == 0 else "Pending Balance")
    kpi_f3.metric(
        "Net Tuition & Dues",
        f"₹{net_outstanding:,.2f}",
        delta="All Cleared" if net_outstanding == 0 else "Payment Due",
        delta_color="normal" if net_outstanding == 0 else "inverse",
    )
    kpi_f4.metric(
        "Outstanding Fines",
        f"₹{outstanding_fines:,.2f}",
        delta="No Penalties" if outstanding_fines == 0 else "Action Required",
        delta_color="normal" if outstanding_fines == 0 else "inverse",
    )

    st.markdown("---")

    # 6 Dedicated Sub-Tabs
    sub_structure, sub_schedule, sub_receipts, sub_statement, sub_refund, sub_fines = st.tabs([
        "🏛️ Fee Structure",
        "📅 Fee Schedule",
        "🧾 Receipts",
        "📊 Account Statement",
        "💸 Refund & Caution Deposit",
        "⚠️ Fines & Penalties",
    ])

    # ---------------------------------------------------------
    # SUB-TAB 1: FEE STRUCTURE
    # ---------------------------------------------------------
    with sub_structure:
        st.markdown("#### 🏛️ Accredited Program Fee Structure · B.Tech (Honors)")
        st.caption("Approved by Finance Committee and Board of Governors for Batch 2026–2030 (4 Years / 8 Semesters).")

        struct_col1, struct_col2 = st.columns([1.4, 1])

        with struct_col1:
            st.markdown("##### 📌 Year 1 (Semester 1 & Semester 2) Component Breakdown")
            struct_df = pd.DataFrame([
                {"Component": "Tuition & Academic Instructional Fee", "Semester 1": "₹1,25,000.00", "Semester 2": "₹1,25,000.00", "Frequency": "Per Semester"},
                {"Component": "University Admission & Enrollment Charge", "Semester 1": "₹20,000.00", "Semester 2": "—", "Frequency": "One-Time (Admission)"},
                {"Component": "University Examination & Gradebook Processing", "Semester 1": "₹3,500.00", "Semester 2": "₹3,500.00", "Frequency": "Per Semester"},
                {"Component": "Computing Laboratory Facilities & High-Speed IT", "Semester 1": "₹8,000.00", "Semester 2": "₹8,000.00", "Frequency": "Per Semester"},
                {"Component": "Digital Library, Online Journals & E-Resources", "Semester 1": "₹7,000.00", "Semester 2": "₹7,000.00", "Frequency": "Per Semester"},
                {"Component": "Institutional Caution Deposit (100% Refundable)", "Semester 1": "₹10,000.00", "Semester 2": "—", "Frequency": "Refundable on Exit"},
                {"Component": "Student Welfare, Campus Life & Sports Fund", "Semester 1": "₹2,000.00", "Semester 2": "₹2,000.00", "Frequency": "Per Semester"},
                {"Component": "Alumni Association Life Membership Fund", "Semester 1": "₹1,500.00", "Semester 2": "—", "Frequency": "One-Time"},
            ])
            st.dataframe(struct_df, use_container_width=True, hide_index=True)

        with struct_col2:
            st.markdown("##### 💡 Financial Highlights & Policies")
            with st.container(border=True):
                st.markdown(
                    """
                    * **Semester 1 Total Prescribed:** **₹1,77,000.00**
                    * **Subsequent Semesters (Sem 2–8):** **₹1,45,500.00** per semester
                    * **Cumulative 4-Year B.Tech Investment:** **₹11,95,500.00**
                    * **Refundable Caution Deposit:** **₹10,000.00** returned in full upon graduation.
                    * **Merit Scholarship Tiers:**
                      * *Category A (≥90% 10+2 marks):* 50% Tuition Fee waiver.
                      * *Category B (80%–89.9% marks):* 25% Tuition Fee waiver.
                      * *Sports / Special Talent:* Up to ₹25,000 semester grant.
                    """
                )

    # ---------------------------------------------------------
    # SUB-TAB 2: FEE SCHEDULE
    # ---------------------------------------------------------
    with sub_schedule:
        st.markdown("#### 📅 Institutional Payment Calendar & Due Dates (2026–27)")
        st.caption("Official statutory deadlines established by the Registrar and Directorate of Finance.")

        sched_df = pd.DataFrame([
            {"Academic Cycle": "Semester 1 (Autumn)", "Challan Billing Date": "01-Jul-2026", "Due Date (No Late Fee)": "31-Jul-2026", "Grace Period (₹500 Late Fine)": "01-Aug to 10-Aug-2026", "Final Cutoff (₹1,500 Fine)": "20-Aug-2026", "Status": "Completed"},
            {"Academic Cycle": "Semester 2 (Spring)", "Challan Billing Date": "15-Dec-2026", "Due Date (No Late Fee)": "10-Jan-2027", "Grace Period (₹500 Late Fine)": "11-Jan to 20-Jan-2027", "Final Cutoff (₹1,500 Fine)": "31-Jan-2027", "Status": "Upcoming"},
            {"Academic Cycle": "Semester 3 (Autumn)", "Challan Billing Date": "01-Jul-2027", "Due Date (No Late Fee)": "31-Jul-2027", "Grace Period (₹500 Late Fine)": "01-Aug to 10-Aug-2027", "Final Cutoff (₹1,500 Fine)": "20-Aug-2027", "Status": "Scheduled"},
            {"Academic Cycle": "Semester 4 (Spring)", "Challan Billing Date": "15-Dec-2027", "Due Date (No Late Fee)": "10-Jan-2028", "Grace Period (₹500 Late Fine)": "11-Jan to 20-Jan-2028", "Final Cutoff (₹1,500 Fine)": "31-Jan-2028", "Status": "Scheduled"},
        ])
        st.dataframe(sched_df, use_container_width=True, hide_index=True)

        st.markdown("##### 💳 Approved Banking Modes & Gateway Options")
        b1, b2, b3 = st.columns(3)
        with b1:
            with st.container(border=True):
                st.markdown("**1. Instant Online ERP Gateway**")
                st.caption("Credit / Debit Cards, Net Banking, and UPI QR (Instant automated challan clearance and receipt generation).")
        with b2:
            with st.container(border=True):
                st.markdown("**2. Virtual Account NEFT / RTGS**")
                st.caption("Beneficiary: IFHE Fee Collection Account\nAccount: `IFHE2026` + Roll Number\nIFSC Code: `HDFC0000240`")
        with b3:
            with st.container(border=True):
                st.markdown("**3. Campus Accounts Counter**")
                st.caption("Demand Draft drawn in favor of *The ICFAI Foundation for Higher Education - Fee Account*, payable at Hyderabad.")

    # ---------------------------------------------------------
    # SUB-TAB 3: RECEIPTS
    # ---------------------------------------------------------
    with sub_receipts:
        st.markdown("#### 🧾 Official University Payment Receipts")
        st.caption("Digitally signed tax invoices and institutional payment acknowledgments.")

        rec_num = f"REC-FST-2026-{student_id:05d}"
        txn_ref = f"TXN-IFHE-2026-{100000+student_id}"
        rec_date = "12-Aug-2026 11:30:00"
        amount_cleared = total_credits_paid

        st.markdown(
            f"""
            <div style="background: #ffffff; border: 2px solid #091e3a; border-radius: 12px; padding: 2rem; color: #091e3a; max-width: 820px; margin: 0 auto; box-shadow: 0 4px 14px rgba(0,0,0,0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #091e3a; padding-bottom: 1rem; margin-bottom: 1.2rem;">
                    <div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #091e3a;">THE ICFAI FOUNDATION FOR HIGHER EDUCATION</div>
                        <div style="font-size: 0.85rem; color: #475569;">Faculty of Science & Technology · Directorate of Finance</div>
                        <div style="font-size: 1rem; font-weight: 700; color: #1e3a8a; margin-top: 0.2rem;">OFFICIAL FEE PAYMENT RECEIPT</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: #166534; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">PAID IN FULL</span>
                        <div style="font-family: monospace; font-size: 0.8rem; margin-top: 0.3rem;">Receipt: {rec_num}</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 0.85rem; background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1.2rem; border: 1px solid #e2e8f0;">
                    <div><b>Student Name:</b> {full_name}</div>
                    <div><b>Roll Number:</b> {roll_number}</div>
                    <div><b>Enrollment No:</b> {enrollment_number}</div>
                    <div><b>Academic Program:</b> B.Tech (Honors) · {department}</div>
                    <div><b>Semester / Batch:</b> Year 1, Semester 1 · Batch 2026–27</div>
                    <div><b>Assigned Section:</b> Section {assigned_section}</div>
                    <div><b>Transaction Reference:</b> <code>{txn_ref}</code></div>
                    <div><b>Payment Mode / Gateway:</b> Online Net Banking / HDFC Gateway</div>
                    <div><b>Date & Timestamp:</b> {rec_date}</div>
                    <div><b>Aadhar Number:</b> {student.get('aadhar_no') or '7892-XXXX-1049'}</div>
                </div>

                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 1.2rem;">
                    <thead>
                        <tr style="background: #091e3a; color: white;">
                            <th style="padding: 8px; border: 1px solid #091e3a; text-align: left;">S.No</th>
                            <th style="padding: 8px; border: 1px solid #091e3a; text-align: left;">Particulars / Component</th>
                            <th style="padding: 8px; border: 1px solid #091e3a; text-align: right;">Amount (INR)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">1</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">Tuition & Academic Instructional Fee (Sem 1)</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹1,25,000.00</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">2</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">One-Time University Admission & Registration Charge</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹20,000.00</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">3</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">Institutional Caution Deposit (100% Refundable on Exit)</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹10,000.00</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">4</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">Semester 1 Examination & Gradebook Processing</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹3,500.00</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">5</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">Computing Infrastructure & Digital Library Amenities</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹15,000.00</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">6</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">Student Welfare & Alumni Association Fund</td>
                            <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: right;">₹3,500.00</td>
                        </tr>
                        <tr style="background: #f1f5f9; font-weight: 700;">
                            <td colspan="2" style="padding: 8px; border: 1px solid #cbd5e1; text-align: right;">TOTAL AMOUNT RECEIVED:</td>
                            <td style="padding: 8px; border: 1px solid #cbd5e1; text-align: right; color: #166534; font-size: 1rem;">₹{amount_cleared:,.2f}</td>
                        </tr>
                    </tbody>
                </table>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 2px solid #091e3a; padding-top: 1rem;">
                    <div style="font-size: 0.8rem; color: #64748b;">
                        Authorized by Autonomous ERP Governance Engine · IFHE Hyderabad<br>
                        Electronic Verification Code: <code>IFHE-FST-AUTH-{student_id:04d}-2026</code>
                    </div>
                    <div style="text-align: center;">
                        <div style="border: 2px solid #091e3a; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 800;">FINANCE DEPT SEAL</div>
                        <div style="font-size: 0.75rem; margin-top: 0.2rem;">Accounts Officer</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("💡 To save as a PDF receipt, press Ctrl+P (or Cmd+P) and choose 'Save as PDF'.")

    # ---------------------------------------------------------
    # SUB-TAB 4: STATEMENT (ACCOUNT LEDGER)
    # ---------------------------------------------------------
    with sub_statement:
        st.markdown("#### 📊 Cumulative Student Account Statement & Financial Ledger")
        st.caption("Chronological record of all invoices, payments, credits, and running balance from admission to present date.")

        if fee_stmts:
            stmt_display = []
            for s in fee_stmts:
                d_amt = float(s.get("debit_amount") or 0)
                c_amt = float(s.get("credit_amount") or 0)
                b_amt = float(s.get("balance_running") or 0)
                stmt_display.append({
                    "Date": s["transaction_date"],
                    "Reference / Voucher": s["reference_no"],
                    "Transaction Type": s["transaction_type"],
                    "Particulars / Description": s["description"],
                    "Debit (Dr) INR": f"₹{d_amt:,.2f}" if d_amt > 0 else "—",
                    "Credit (Cr) INR": f"₹{c_amt:,.2f}" if c_amt > 0 else "—",
                    "Running Balance INR": f"₹{b_amt:,.2f}",
                })
            st.dataframe(pd.DataFrame(stmt_display), use_container_width=True, hide_index=True)

            stmt_csv = pd.DataFrame(stmt_display).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Official Account Statement (.CSV)",
                data=stmt_csv,
                file_name=f"{roll_number}_Fee_Statement_2026.csv",
                mime="text/csv",
            )
        else:
            st.info("No transaction ledger items recorded for this student.")

    # ---------------------------------------------------------
    # SUB-TAB 5: REFUND & CAUTION DEPOSIT
    # ---------------------------------------------------------
    with sub_refund:
        st.markdown("#### 💸 Institutional Fee Refund & Caution Deposit Settlement")
        st.caption("Statutory UGC regulations, caution deposit status, and online refund claim submission.")

        ref_col1, ref_col2 = st.columns([1, 1])

        with ref_col1:
            st.markdown("##### 🛡️ Caution Deposit Status")
            with st.container(border=True):
                st.metric("Institutional Caution Deposit Held", "₹10,000.00", delta="100% Refundable on Degree Completion")
                st.markdown(
                    """
                    * **Deposit Status:** Active in Institutional Escrow Trust
                    * **Refund Eligibility:** Complete 100% refund without deduction upon final degree clearance or formal institutional withdrawal.
                    * **Clearance Certificate:** Automatically generated after library, lab, and hostel no-dues verification.
                    """
                )

            st.markdown("##### 📜 Statutory UGC Refund Matrix (Notification 2026)")
            ugc_df = pd.DataFrame([
                {"Timeline of Withdrawal Notice": "≥ 15 Days before formally notified last date of admission", "Refund Percentage": "100%", "Deduction": "₹0.00"},
                {"Timeline of Withdrawal Notice": "< 15 Days before formally notified last date of admission", "Refund Percentage": "90%", "Deduction": "Max ₹1,000"},
                {"Timeline of Withdrawal Notice": "≤ 15 Days after formally notified last date of admission", "Refund Percentage": "80%", "Deduction": "20% Tuition"},
                {"Timeline of Withdrawal Notice": "16 to 30 Days after formally notified last date", "Refund Percentage": "50%", "Deduction": "50% Tuition"},
                {"Timeline of Withdrawal Notice": "> 30 Days after formally notified last date", "Refund Percentage": "0%", "Deduction": "Only Caution Deposit"},
            ])
            st.dataframe(ugc_df, use_container_width=True, hide_index=True)

        with ref_col2:
            st.markdown("##### 📝 Submit Fee Refund / Caution Deposit Claim")
            with st.form("refund_claim_form"):
                ref_type = st.selectbox("Refund Claim Category", ["Excess Tuition Fee Paid", "Caution Deposit Settlement", "Cancelled Examination Fee", "Hostel Security Return"])
                ref_amount = st.number_input("Claim Amount Requested (INR)", min_value=500.0, max_value=50000.0, value=5000.0, step=500.0)
                ref_bank = st.text_input("Beneficiary Bank Name", value="State Bank of India")
                ref_holder = st.text_input("Account Holder Name", value=full_name)
                ref_acc = st.text_input("Bank Account Number", value="38491029481")
                ref_ifsc = st.text_input("Bank IFSC Code", value="SBIN0020194")
                ref_reason = st.text_area("Justification / Reason for Refund", "Excess payment transferred during online fee payment portal session.")

                submit_ref = st.form_submit_button("🚀 Submit Official Refund Application", type="primary", use_container_width=True)
                if submit_ref:
                    app_no = submit_refund_request(
                        student_id=student_id,
                        refund_type=ref_type,
                        amount=ref_amount,
                        bank_name=ref_bank,
                        account_number=ref_acc,
                        ifsc_code=ref_ifsc,
                        holder_name=ref_holder,
                        reason=ref_reason,
                    )
                    st.success(f"✅ Refund claim successfully submitted! Your Tracking Application No: `{app_no}`. Accounts branch will review within 5 working days.")
                    st.rerun()

        st.markdown("##### 📋 Historical & Active Refund Applications")
        if refund_requests:
            ref_rows = []
            for rf in refund_requests:
                ref_rows.append({
                    "Application No": rf["application_no"],
                    "Category": rf["refund_type"],
                    "Amount Requested": f"₹{float(rf['amount_requested']):,.2f}",
                    "Bank Name": rf["bank_name"],
                    "Account No": f"••••{str(rf['account_number'])[-4:]}",
                    "Status": rf["status"],
                    "Applied Date": rf.get("applied_date", "Recently"),
                })
            st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No active refund applications found.")

    # ---------------------------------------------------------
    # SUB-TAB 6: FINES & PENALTIES
    # ---------------------------------------------------------
    with sub_fines:
        st.markdown("#### ⚠️ Institutional Fines & Penalty Assessment Ledger")
        st.caption("Transparent tracking of library overdue penalties, late registration charges, and disciplinary fees.")

        fine_p1, fine_p2 = st.columns([1.1, 1])

        with fine_p1:
            st.markdown("##### 📌 Statutory Fine Regulations & Slabs")
            fine_rules_df = pd.DataFrame([
                {"Fine Category": "Late Semester Course Registration", "Statutory Slabs": "Tier 1: ₹500 (Days 1–10) · Tier 2: ₹1,500 (Days 11–20) · Tier 3: ₹3,000", "Clearance Required For": "Mid-Term Exam Hall Ticket"},
                {"Fine Category": "Library Overdue Volume Penalty", "Statutory Slabs": "₹5.00 per day per overdue textbook / reference volume", "Clearance Required For": "Semester Gradebook Release"},
                {"Fine Category": "Laboratory Equipment Damage", "Statutory Slabs": "Actual component replacement cost + 10% administrative fee", "Clearance Required For": "End-Sem Practical Examination"},
            ])
            st.dataframe(fine_rules_df, use_container_width=True, hide_index=True)

        with fine_p2:
            st.markdown("##### 💳 Fine Clearance & Settlement")
            with st.container(border=True):
                if outstanding_fines == 0:
                    st.success("🎉 **Zero Outstanding Penalties!** Your academic record has no pending fines or disciplinary dues.")
                else:
                    st.error(f"⚠️ **Action Required:** You have **₹{outstanding_fines:,.2f}** in pending penalty assessments. Please clear dues to prevent examination hall ticket hold.")

        st.markdown("##### 📋 Student Fine Assessment Ledger")
        if student_fines:
            fine_display = []
            for f in student_fines:
                fine_display.append({
                    "Fine ID": f"#{f['fine_id']}",
                    "Fine Category": f["fine_type"],
                    "Incident Date": f["incident_date"],
                    "Due Date": f["due_date"],
                    "Amount (INR)": f"₹{float(f['amount']):,.2f}",
                    "Status": "● " + f["status"],
                    "Payment Date": f.get("payment_date") or "—",
                    "Transaction ID": f.get("transaction_id") or "—",
                    "Remarks": f.get("remarks") or "Standard assessment",
                })
            st.dataframe(pd.DataFrame(fine_display), use_container_width=True, hide_index=True)

            # Instant Fine Payment Action if any fine is outstanding
            pending_fines = [f for f in student_fines if f["status"] == "Outstanding"]
            if pending_fines:
                target_f = pending_fines[0]
                st.markdown("###### 💳 Settle Pending Fine Online")
                if st.button(f"Pay Fine #{target_f['fine_id']}: ₹{float(target_f['amount']):,.2f} ({target_f['fine_type']})", type="primary"):
                    ok = pay_student_fine(student_id=student_id, fine_id=target_f["fine_id"])
                    if ok:
                        st.success(f"✅ Penalty fine #{target_f['fine_id']} paid successfully! Clearance certificate updated.")
                        st.rerun()
        else:
            st.info("No penalty fines recorded on your academic profile.")


# =============================================================
# TAB 4: ACADEMIC CURRICULUM
# =============================================================
elif student_nav == "📚 Academic Curriculum":
    st.subheader(f"Academic Curriculum & Course Enrollment · Year {current_year}, Semester {current_semester}")
    st.caption("Official accredited course structure for Batch 2026–27 (Total 20 Credits across 8 Courses).")

    with st.container(border=True):
        scol1, scol2, scol3, scol4 = st.columns(4)
        scol1.metric("Enrolled Section", f"Section {assigned_section}")
        scol2.metric("Total Courses", f"{len(registered_courses)} Courses")
        scol3.metric("Earnable Credits", f"{total_credits:.1f} Credits")
        scol4.metric("Enrollment Status", "Verified & Locked")

    if registered_courses:
        course_display_list = []
        for rc in registered_courses:
            course_display_list.append({
                "Course Code": rc["course_code"],
                "Course Title": rc["course_name"],
                "Credits": rc["credits"],
                "Course Category": rc["course_type"],
                "CIE Max": 60,
                "SEE Max": 40,
                "Total": 100,
                "Semester": f"Sem {rc['semester']}",
                "Academic Batch": rc["academic_year"],
            })
        st.dataframe(pd.DataFrame(course_display_list), use_container_width=True, hide_index=True)
    else:
        st.warning("No registered courses found for this semester.")


# =============================================================
# TAB 5: CIE & EXTERNAL GRADEBOOK (60/40) & GRADE CARD
# =============================================================
# =============================================================
# TAB: COURSE & FACULTY FEEDBACK
# =============================================================
elif student_nav == "⭐ Course & Faculty Feedback":
    st.subheader("⭐ Course Curriculum & Faculty Instructional Feedback")
    st.caption("Provide constructive feedback on your registered courses, instructional clarity, laboratory sessions, and continuous assessment fairness.")

    registered_courses = get_student_registered_courses(student_id, current_semester)
    submitted_feedbacks = get_student_submitted_feedback(student_id, current_semester)
    submitted_course_ids = set(fb["course_id"] for fb in submitted_feedbacks)

    fb_col1, fb_col2 = st.columns([1, 1])
    with fb_col1:
        st.metric("Total Registered Courses", len(registered_courses))
    with fb_col2:
        st.metric("Feedbacks Completed", f"{len(submitted_course_ids)} / {len(registered_courses)}")

    st.divider()

    tab_submit_fb, tab_fb_history = st.tabs([
        "📝 Submit Course Feedback",
        "📋 My Submitted Feedback History"
    ])

    with tab_submit_fb:
        if not registered_courses:
            st.info("You do not have any registered courses for the current semester. Please complete semester registration first.")
        else:
            course_options = {}
            for c in registered_courses:
                status_icon = "✅ (Completed)" if c["course_id"] in submitted_course_ids else "⏳ (Pending)"
                label = f"{c['course_code']} - {c['course_name']} {status_icon}"
                course_options[label] = c

            selected_course_label = st.selectbox("Select Course for Feedback", list(course_options.keys()))
            chosen_c = course_options[selected_course_label]
            c_id = chosen_c["course_id"]

            # Lookup assigned faculty for this course in student's section
            conn = get_connection()
            fac_row = conn.execute(
                """
                SELECT f.faculty_id, f.full_name, f.designation
                FROM timetable t
                JOIN faculty f ON f.faculty_id = t.faculty_id
                WHERE t.course_id = ? AND t.section = ?
                LIMIT 1
                """,
                (c_id, assigned_section)
            ).fetchone()
            conn.close()

            assigned_faculty_name = fac_row["full_name"] if fac_row else "Department Faculty Instructor"
            assigned_faculty_id = fac_row["faculty_id"] if fac_row else None

            st.info(f"📘 **Course:** {chosen_c['course_code']} - {chosen_c['course_name']} | 👨‍🏫 **Instructor:** {assigned_faculty_name} (Section {assigned_section})")

            with st.form("student_course_feedback_form"):
                st.markdown("##### 📊 Academic Rating Dimensions (1 = Unsatisfactory, 5 = Excellent)")
                
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_teaching = st.select_slider(
                        "1. Teaching Quality & Conceptual Clarity",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: f"{x} Star{'s' if x > 1 else ''}"
                    )
                    r_content = st.select_slider(
                        "2. Syllabus Coverage & Course Structure",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: f"{x} Star{'s' if x > 1 else ''}"
                    )
                    r_practical = st.select_slider(
                        "3. Laboratory & Hands-on Problem Solving Support",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: f"{x} Star{'s' if x > 1 else ''}"
                    )
                with r_col2:
                    r_fairness = st.select_slider(
                        "4. Fairness in Continuous Internal Evaluation (CIE /60)",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: f"{x} Star{'s' if x > 1 else ''}"
                    )
                    r_overall = st.select_slider(
                        "5. Overall Learning Experience in this Course",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        format_func=lambda x: f"{x} Star{'s' if x > 1 else ''}"
                    )

                st.markdown("##### 💬 Qualitative Qualitative Observations & Suggestions")
                strengths_txt = st.text_area(
                    "What are the key strengths of this course and the instructor's teaching methodology?",
                    placeholder="e.g. Excellent explanation of memory allocation diagrams, timely lab code reviews...",
                    height=80
                )
                improve_txt = st.text_area(
                    "Constructive Suggestions for Course Improvement",
                    placeholder="e.g. More practice questions on dynamic arrays before midterm exams...",
                    height=80
                )

                is_anon = st.checkbox("🔒 Submit Anonymously (Your name and roll number will not be visible to faculty)", value=True)

                fb_submit = st.form_submit_button("🚀 Submit Course Feedback", type="primary", use_container_width=True)
                if fb_submit:
                    success = submit_course_feedback(
                        student_id=student_id,
                        course_id=c_id,
                        faculty_id=assigned_faculty_id,
                        section=assigned_section,
                        semester=current_semester,
                        rating_teaching=r_teaching,
                        rating_content=r_content,
                        rating_practical=r_practical,
                        rating_fairness=r_fairness,
                        rating_overall=r_overall,
                        strengths_comment=strengths_txt.strip(),
                        improvement_comment=improve_txt.strip(),
                        is_anonymous=1 if is_anon else 0
                    )
                    if success:
                        st.success(f"🎉 **Thank You!** Your feedback for **{chosen_c['course_name']}** has been officially recorded.")
                        st.rerun()
                    else:
                        st.error("Failed to submit feedback. Please try again.")

    with tab_fb_history:
        st.markdown("##### 📋 Your Feedback Submissions for Semester " + str(current_semester))
        if submitted_feedbacks:
            for fb in submitted_feedbacks:
                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3, 1])
                    with h_col1:
                        st.markdown(f"**{fb['course_code']} - {fb['course_name']}**")
                        st.caption(f"Instructor: {fb.get('faculty_name', 'Faculty')} | Submitted: {fb['submitted_at']}")
                    with h_col2:
                        avg_r = (fb['rating_teaching'] + fb['rating_content'] + fb['rating_practical'] + fb['rating_fairness'] + fb['rating_overall']) / 5.0
                        st.metric("Avg Rating", f"{avg_r:.1f} / 5.0")

                    st.markdown(
                        f"• Teaching: **{fb['rating_teaching']}/5** | Content: **{fb['rating_content']}/5** | Practical: **{fb['rating_practical']}/5** | Fairness: **{fb['rating_fairness']}/5** | Overall: **{fb['rating_overall']}/5**"
                    )
                    if fb.get("strengths_comment"):
                        st.markdown(f"**Strengths:** *{fb.get('strengths_comment', '')}*")
                    if fb.get("improvement_comment"):
                        st.markdown(f"**Suggestions:** *{fb.get('improvement_comment', '')}*")
        else:
            st.info("You have not submitted feedback for any courses yet.")


elif student_nav == "📊 Continuous Internal Evaluation (CIE /60)":
    st.subheader("Continuous Internal Evaluation (CIE /60) Dossier")
    st.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; font-size: 0.88rem;">
            <b>Continuous Internal Evaluation (CIE) Framework:</b>  
            Each course is evaluated on a continuous <b>60-mark in-semester scale</b>:  
            • <b>30 Marks:</b> Mid-Term Examination  
            • <b>10 Marks:</b> Formative Assignments  
            • <b>10 Marks:</b> Continuous Quizzes  
            • <b>10 Marks:</b> Viva Voce / Laboratory Evaluation  
            <i>External summative marks and final letter grades are excluded to focus strictly on mid-semester early warning and academic intervention.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not course_assessments:
        st.info("Course assessments have not been recorded by faculty yet.")
    else:
        gradebook_rows = []
        for ca in course_assessments:
            mid = ca.get("mid_exam_marks")
            assn = ca.get("assignment_marks")
            quiz = ca.get("quiz_marks")
            viva = ca.get("viva_marks")
            internal = ca.get("internal_total")

            cie_status = "Pass (≥24)" if (internal or 0) >= 24 else "Remedial Needed (<24)"

            gradebook_rows.append({
                "Course Code": ca["course_code"],
                "Course Title": ca["course_name"],
                "Credits": ca["credits"],
                "Mid /30": f"{mid:.1f}" if mid is not None else "—",
                "Assn /10": f"{assn:.1f}" if assn is not None else "—",
                "Quiz /10": f"{quiz:.1f}" if quiz is not None else "—",
                "Viva /10": f"{viva:.1f}" if viva is not None else "—",
                "Internal CIE /60": f"{internal:.1f}" if internal is not None else "—",
                "CIE Status": cie_status,
                "Faculty Evaluator": ca.get("faculty_name", "Assigned Faculty"),
            })

        st.dataframe(pd.DataFrame(gradebook_rows), use_container_width=True, hide_index=True)

        # Official Printable Grade Card Generator
        st.markdown("### 📄 Official Provisional Grade Card & Academic Transcript")
        with st.expander("🎓 View & Print Official Institutional Grade Card", expanded=False):
            st.markdown(
                f"""
                <div style="background: #ffffff; border: 2px solid #091e3a; border-radius: 12px; padding: 2rem; color: #091e3a; max-width: 900px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <div style="text-align: center; border-bottom: 2px solid #091e3a; padding-bottom: 1rem; margin-bottom: 1.5rem;">
                        <h2 style="margin: 0; color: #091e3a; font-size: 1.5rem;">THE ICFAI FOUNDATION FOR HIGHER EDUCATION</h2>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #475569;">(Declared as a Deemed-to-be-University u/s 3 of the UGC Act 1956)</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #1e3a8a; margin-top: 0.3rem;">FACULTY OF SCIENCE & TECHNOLOGY (FST)</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #091e3a; margin-top: 0.5rem; letter-spacing: 0.05em;">PROVISIONAL GRADE REPORT - SEMESTER 1 (2026–27)</div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.9rem; background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0;">
                        <div><b>Student Name:</b> {full_name}</div>
                        <div><b>Enrollment No:</b> {enrollment_number}</div>
                        <div><b>Roll Number:</b> {roll_number}</div>
                        <div><b>Program:</b> Bachelor of Technology (Honors)</div>
                        <div><b>Department:</b> {department}</div>
                        <div><b>Assigned Section:</b> Section {assigned_section}</div>
                        <div><b>Date of Birth:</b> {student.get('date_of_birth') or '2005-06-14'}</div>
                        <div><b>Aadhar Number:</b> {student.get('aadhar_no') or '7892-XXXX-1049'}</div>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 1.5rem;">
                        <thead>
                            <tr style="background: #091e3a; color: white;">
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: left;">Code</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: left;">Course Title</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Credits</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Mid /30</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Assn /10</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Quiz /10</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Viva /10</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">CIE /60</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr style="border-bottom: 1px solid #cbd5e1;">
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; font-family: monospace;">{r["Course Code"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">{r["Course Title"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Credits"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Mid /30"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Assn /10"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Quiz /10"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Viva /10"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center; font-weight: 700;">{r["Internal CIE /60"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center; font-weight: 700; color: {'#166534' if 'Pass' in r['CIE Status'] else '#dc2626'};">{r["CIE Status"]}</td>
                            </tr>
                            ''' for r in gradebook_rows])}
                        </tbody>
                    </table>

                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 2px solid #091e3a; padding-top: 1rem; margin-top: 1rem;">
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 800;">Continuous Internal Evaluation (CIE) Average: {avg_internal:.1f} / 60.0</div>
                            <div style="font-size: 0.9rem; color: #166534; font-weight: 700; margin-top: 0.2rem;">Advisory Standing: {overall_perf.upper()}</div>
                            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">In-Semester Proactive Evaluation Model (Grades & CGPA Removed)</div>
                        </div>
                        <div style="text-align: center; font-size: 0.8rem;">
                            <div style="border: 2px solid #091e3a; padding: 6px 12px; border-radius: 6px; font-weight: 800; letter-spacing: 1px;">AUTHENTICATED SEAL</div>
                            <div style="margin-top: 0.5rem; color: #475569;">Controller of Examinations</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("💡 To save as a PDF document, open your browser menu and choose Print (or Ctrl+P / Cmd+P) -> Save as PDF.")


# =============================================================
# TAB 6: TIMETABLE & ATTENDANCE
# =============================================================
elif student_nav in ("📅 Course Attendance & Timetable", "📅 Timetable & Attendance"):
    st.subheader("📅 Course-wise Attendance Intelligence & Timetable Portal")
    st.caption("Institutional attendance tracking per course, statutory 75% examination compliance margins, and weekly section schedule.")

    # Top Executive Statutory Summary Banner
    curr_att_val = float(student.get("attendance_percentage") or 78.5)
    is_safe = curr_att_val >= 75.0
    status_bg = "#ecfdf5" if is_safe else "#fef2f2"
    status_border = "#10b981" if is_safe else "#ef4444"
    status_title = "✅ STATUTORY ATTENDANCE COMPLIANT (ELIGIBLE FOR EXAMS)" if is_safe else "⚠️ STATUTORY ATTENDANCE SHORTAGE (< 75.0% DEBARMENT RISK)"
    status_desc = (
        f"Your cumulative attendance across all registered courses is **{curr_att_val:.1f}%**, exceeding the university "
        f"mandatory statutory cutoff of **75.0%**. You are in good academic standing to appear for End-Semester External Examinations."
        if is_safe else
        f"Your cumulative attendance is currently **{curr_att_val:.1f}%**, which falls below the institutional statutory "
        f"threshold of **75.0%**. Regularize your attendance immediately or submit an On-Duty / Medical Leave application."
    )

    st.markdown(
        f"""
        <div style="background: {status_bg}; border: 1px solid {status_border}; border-left: 5px solid {status_border}; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
            <div style="font-weight: 800; font-size: 1.05rem; color: {'#065f46' if is_safe else '#991b1b'}; margin-bottom: 4px;">
                {status_title}
            </div>
            <div style="font-size: 0.9rem; line-height: 1.5; color: {'#047857' if is_safe else '#b91c1c'};">
                {status_desc}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_course_att, tab_schedule_grid, tab_session_logs = st.tabs([
        "📊 Course-by-Course Attendance Ledger",
        "📅 Weekly Section Timetable Matrix",
        "📋 Session-by-Session Biometric Log"
    ])

    with tab_course_att:
        st.markdown("##### 📚 Real-Time Attendance Ledger by Registered Course")
        st.caption("Track total conducted sessions, classes attended, missed lectures, and your statutory safety margin for each subject.")

        course_att_records = get_student_detailed_course_attendance(student_id, current_semester)

        if not course_att_records:
            st.info("No registered courses found for attendance calculation.")
        else:
            # Summary Metrics Row
            tot_conducted = sum(r["conducted_sessions"] for r in course_att_records)
            tot_attended = sum(r["attended_sessions"] for r in course_att_records)
            tot_missed = sum(r["missed_sessions"] for r in course_att_records)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Cumulative Attendance", f"{curr_att_val:.1f}%", delta="Compliant" if is_safe else "Shortage", delta_color="normal" if is_safe else "inverse")
            kpi2.metric("Total Sessions Conducted", f"{tot_conducted} Hours")
            kpi3.metric("Total Sessions Attended", f"{tot_attended} Hours")
            kpi4.metric("Total Absences / Leaves", f"{tot_missed} Hours", delta=f"{tot_missed} missed", delta_color="inverse" if tot_missed > 0 else "normal")

            st.divider()

            # Course Cards & Progress Bars
            for c_att in course_att_records:
                with st.container(border=True):
                    c_col1, c_col2, c_col3 = st.columns([2.5, 1.5, 1.5])
                    with c_col1:
                        st.markdown(f"#### **{c_att['course_code']} — {c_att['course_name']}**")
                        st.caption(f"Course Instructor: **{c_att['faculty_name']}** · Credits: **{c_att['credits']}** · Section **{assigned_section}**")
                    with c_col2:
                        p_val = c_att["attendance_percentage"]
                        st.metric("Attendance", f"{p_val:.1f}%", f"{c_att['attended_sessions']}/{c_att['conducted_sessions']} Attended")
                    with c_col3:
                        badge_color = "#16a34a" if c_att["is_compliant"] else "#dc2626"
                        st.markdown(f"<div style='background: {badge_color}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 700; text-align: center; margin-top: 8px;'>{c_att['status']}</div>", unsafe_allow_html=True)
                        st.caption(f"💡 {c_att['margin_analysis']}")

                    # Progress Bar
                    frac = min(1.0, max(0.0, c_att["attendance_percentage"] / 100.0))
                    st.progress(frac)

            # Tabular Ledger View
            st.markdown("##### 📋 Consolidated Course Attendance Summary Table")
            ledger_table = [
                {
                    "Course Code": r["course_code"],
                    "Course Name": r["course_name"],
                    "Faculty Instructor": r["faculty_name"],
                    "Conducted": r["conducted_sessions"],
                    "Attended": r["attended_sessions"],
                    "Missed": r["missed_sessions"],
                    "Attendance %": f"{r['attendance_percentage']:.1f}%",
                    "Statutory Margin": r["margin_analysis"],
                    "Status": "✅ Compliant" if r["is_compliant"] else "⚠️ Shortage",
                }
                for r in course_att_records
            ]
            st.dataframe(pd.DataFrame(ledger_table), use_container_width=True, hide_index=True)

            st.download_button(
                "📥 Export Course Attendance Report (CSV)",
                data=pd.DataFrame(ledger_table).to_csv(index=False),
                file_name=f"course_attendance_{roll_number}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab_schedule_grid:
        st.markdown(f"##### 📅 Weekly Section Schedule · Section {assigned_section}")
        st.caption("50-minute teaching slots conducted Monday through Saturday as scheduled by Academic Administration.")

        if not timetable_slots:
            st.info("No timetable slots have been scheduled for Section " + assigned_section)
        else:
            grid_data = {day: {slot: "" for slot in ACADEMIC_PERIODS} for day in ACADEMIC_DAYS}
            for item in timetable_slots:
                day = item["day"]
                slot = item["slot"]
                if day in grid_data and slot in grid_data[day]:
                    grid_data[day][slot] = f"{item['course_code']}\n({item['room_number']})"

            matrix_df = pd.DataFrame.from_dict(grid_data, orient="index")
            st.dataframe(matrix_df, use_container_width=True)

    with tab_session_logs:
        st.markdown("##### 📋 Recent Session-by-Session Biometric Attendance Log")
        st.caption("Chronological record of recent class sessions marked by course instructors.")

        recent_logs = get_student_recent_attendance_sessions(student_id, limit=30)
        if not recent_logs:
            st.info("Session attendance records are logged automatically as faculty submits daily rosters.")
        else:
            formatted_logs = [
                {
                    "Date": log["session_date"],
                    "Course": f"{log['course_code']} - {log['course_name']}",
                    "Faculty": log.get("faculty_name", "Course Faculty"),
                    "Slot": f"{log['day']} {log['slot']}",
                    "Status": "🟢 Present" if log["is_present"] else "🔴 Absent",
                }
                for log in recent_logs
            ]
            st.dataframe(pd.DataFrame(formatted_logs), use_container_width=True, hide_index=True)


# =============================================================
# TAB 7: AI DECISION ENGINE & EXPLAINABLE AI (XAI)
# =============================================================
elif student_nav == "🧠 AI Decision Engine & XAI":
    st.subheader("Autonomous AI Academic Decision Engine")
    st.caption("Dual Random Forest Machine Learning intelligence synthesizing educational benchmarks.")

    if latest_eval:
        with st.container(border=True):
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("Active ML Classifier", f"{latest_eval.get('algorithm', 'Random Forest')}")
            s_perf_acc = float(latest_eval.get("performance_accuracy") or 0.974) * 100
            mcol2.metric("Performance Accuracy", f"{s_perf_acc:.1f}%")
            s_risk_acc = float(latest_eval.get("risk_accuracy") or 0.990) * 100
            mcol3.metric("Risk Detection Accuracy", f"{s_risk_acc:.1f}%")
            mcol4.metric("Dataset Records Trained", f"{latest_eval.get('samples', 4000):,} Records")
            st.caption(f"Trained by Admin: **{latest_eval.get('trained_by', 'Administrator')}** at {latest_eval.get('trained_at', 'Recently')} · Test Split: {int(float(latest_eval.get('test_size', 0.2))*100)}% Holdout")

    # Overall Prediction Showcase Cards
    pred_card_col1, pred_card_col2 = st.columns(2)
    with pred_card_col1:
        with st.container(border=True):
            st.markdown("#### Projected Academic Performance")
            st.markdown(
                f"""
                <div style="font-size: 2rem; font-weight: 800; color: #091e3a; margin: 0.5rem 0;">
                    {overall_perf}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("Synthesized from Mid Exam (/30), formative Quizzes (/10), Assignments (/10), and Viva Voce (/10).")

    with pred_card_col2:
        with st.container(border=True):
            st.markdown("#### Academic Risk Classification")
            badge_class = "badge-low-risk" if overall_risk == "Low" else ("badge-medium-risk" if overall_risk == "Medium" else "badge-high-risk")
            st.markdown(
                f"""
                <div style="margin: 0.5rem 0;">
                    <span class="badge-pill {badge_class}" style="font-size: 1.4rem; padding: 0.4rem 1rem;">
                        ● {overall_risk} Risk Tier
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write(f"Synthesized against statutory attendance regularities (Cutoff: {policy_att_thresh:.0f}%) and CIE internal evaluation.")

    # ---------------------------------------------------------
    # NEW FEATURE 1: EXPLAINABLE AI (XAI) ATTRIBUTION BREAKDOWN
    # ---------------------------------------------------------
    st.markdown("### 🔍 Explainable AI (XAI): Model Attribution & Risk Drivers")
    st.caption("Mathematical decomposition showing exactly which educational indicators triggered your predicted risk classification.")

    xai_data = explain_student_academic_prediction(student, policies=academic_policies)
    with st.container(border=True):
        st.markdown(f"**AI Decision Synthesis:** {xai_data['executive_summary']}")

        xai_cols = st.columns(len(xai_data["factors"]))
        for idx, f in enumerate(xai_data["factors"]):
            impact_sign = "+" if f["impact"] > 0 else ""
            delta_color = "normal" if f["impact"] > 0 else "inverse"
            with xai_cols[idx]:
                st.metric(
                    f["feature"],
                    f["value"],
                    delta=f"{impact_sign}{f['impact']} pts",
                    delta_color=delta_color,
                )
                st.caption(f"Benchmark: {f['benchmark']}")

        st.markdown("##### Detailed Indicator Analysis:")
        for f in xai_data["factors"]:
            icon = "🟢" if f["impact"] > 0 else "🔴"
            st.markdown(f"{icon} **{f['feature']} ({f['value']}):** {f['reason']}")

    # ---------------------------------------------------------
    # NEW FEATURE 2: "WHAT-IF" ACADEMIC GOAL SIMULATOR
    # ---------------------------------------------------------
    st.markdown("### 🧪 What-If Academic Goal Simulator")
    st.caption("Simulate how targeted improvements in Mid-Term marks, Attendance %, and homework persistence alter your projected standing.")

    with st.container(border=True):
        scol1, scol2 = st.columns(2)
        with scol1:
            curr_mid = float(student.get("mid_exam_marks") or 15.0)
            target_mid = st.slider("Target Mid-Term Exam Marks (/30)", min_value=0.0, max_value=30.0, value=min(curr_mid + 5.0, 30.0), step=1.0)

            curr_att = float(student.get("attendance_percentage") or 75.0)
            target_att = st.slider("Anticipated Future Course Attendance (%)", min_value=30.0, max_value=100.0, value=min(curr_att + 5.0, 100.0), step=1.0)

        with scol2:
            curr_quiz = float(student.get("quiz_marks") or 7.0)
            target_quiz = st.slider("Target Formative Quiz Marks (/10)", min_value=0.0, max_value=10.0, value=min(curr_quiz + 2.0, 10.0), step=0.5)

            curr_assn = float(student.get("assignment_marks") or 7.0)
            target_assn = st.slider("Target Assignment Marks (/10)", min_value=0.0, max_value=10.0, value=min(curr_assn + 2.0, 10.0), step=0.5)

            target_hours = st.slider("Target Weekly LMS Study Hours", min_value=2.0, max_value=30.0, value=15.0, step=1.0)

        sim_out = simulate_student_academic_outcomes(
            base_student_data=student,
            target_mid=target_mid,
            target_attendance=target_att,
            target_quiz=target_quiz,
            target_assign=target_assn,
            target_study_hours=target_hours,
            policies=academic_policies,
        )

        st.divider()
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Simulated Grade Forecast", sim_out["simulated_performance"], delta=f"Current: {overall_perf}")
        res_col2.metric("Simulated Risk Tier", f"{sim_out['simulated_risk']} Risk", delta=f"Current: {overall_risk}")
        res_col3.metric(
            "Statutory Exam Eligibility",
            "COMPLIANT" if sim_out["is_exam_eligible"] else "SHORTAGE ALERT",
            delta=f"Gap: {sim_out['attendance_gap']}%" if not sim_out["is_exam_eligible"] else "Eligible (≥ 75%)",
            delta_color="normal" if sim_out["is_exam_eligible"] else "inverse",
        )


# =============================================================
# TAB 8: TARGETED RECOMMENDATIONS & REAL OUTBOUND SERVICES
# =============================================================
elif student_nav == "🎯 Targeted Recommendations & Alerts":
    st.subheader("AI-Generated Recommendations & Action Plans")
    st.caption("Personalized course-level intervention roadmaps and study guidance formulated by institutional AI models.")

    # High Priority Action Items
    urgent_actions = []
    if overall_attendance < policy_att_thresh:
        urgent_actions.append(f"🚨 **Urgent Attendance Remediation:** Your attendance ({overall_attendance:.1f}%) is below the statutory {policy_att_thresh:.0f}% limit trained by Academic Administration. Regularize attendance immediately to secure examination eligibility.")
    if avg_internal is not None and avg_internal < policy_crit_int:
        urgent_actions.append(f"🚨 **CIE Improvement Plan:** Your average internal score ({avg_internal:.1f}/60) is below the institutional satisfactory threshold ({policy_crit_int:.0f}/60) set by Admin. Register for departmental remedial tutorials.")

    if urgent_actions:
        with st.container(border=True):
            st.markdown("#### ⚠️ High Priority Interventions")
            for action in urgent_actions:
                st.error(action)

    st.markdown("#### 🎯 Course-by-Course Action Plans")
    if course_assessments:
        for ca in course_assessments:
            recs = generate_course_level_recommendations(ca, policies=academic_policies)
            c_att = float(ca.get("course_attendance") or 100.0)
            c_mid = float(ca.get("mid_exam_marks") or 30.0)
            is_expanded = (c_att < policy_att_thresh or c_mid < float(academic_policies.get("mid_exam_threshold", 15.0)))
            with st.expander(f"📚 {ca['course_code']} - {ca['course_name']} (Internal: {float(ca.get('internal_total') or 0):.1f}/60, Att: {c_att:.1f}%)", expanded=is_expanded):
                for r in recs:
                    if isinstance(r, dict):
                        prio = r.get("priority", "Medium")
                        icon = r.get("icon", "📌")
                        cat = r.get("category", "Advisory")
                        txt = r.get("text", "")
                        msg = f"{icon} **[{cat} · {prio} Priority]** {txt}"
                        if prio == "Critical":
                            st.error(msg)
                        elif prio == "High":
                            st.warning(msg)
                        elif prio == "Low":
                            st.success(msg)
                        else:
                            st.info(msg)
                    else:
                        st.info(str(r))
    else:
        st.info("Individual course recommendations will appear as assessment data is published.")


# =============================================================
# TAB 9: NOTIFICATIONS & UNIVERSITY NOTICES
# =============================================================
elif student_nav.startswith("🔔 Notifications"):
    st.subheader(f"Academic Notifications & Official Notices ({unread_count} Unread)")

    if unread_count > 0:
        if st.button("Mark all notifications as read", type="secondary"):
            mark_student_notifications_read(student_id)
            st.success("All notifications marked as read.")
            st.rerun()

    if notifications:
        for notif in notifications:
            is_unread = not notif["is_read"]
            with st.container(border=True):
                ncol1, ncol2 = st.columns([5, 1])
                with ncol1:
                    title_prefix = "🔵 " if is_unread else "⚪ "
                    st.markdown(f"**{title_prefix}{notif['title']}**")
                    st.caption(f"Received: {notif['created_at']}")
                    st.write(notif["message"])
                with ncol2:
                    if is_unread:
                        st.markdown("<span class='badge-pill badge-medium-risk'>New</span>", unsafe_allow_html=True)
    else:
        st.info("No notifications in your inbox.")