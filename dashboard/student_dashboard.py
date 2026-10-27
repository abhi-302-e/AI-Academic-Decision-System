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

from auth import require_student
from database import (
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
    send_student_recommendations_email,
    get_configured_admin_email,
    is_email_service_active,
)
from sms_service import (
    send_academic_recommendation_sms,
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
    st.markdown("#### 📧 Outbound Real Services")
    st.caption(f"Permanent Admin: `{get_configured_admin_email()}`")
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
kpi_cols = st.columns(6)
with kpi_cols[0]:
    st.metric(
        "CGPA / SGPA",
        f"{cgpa_val:.2f} / 10.0",
        delta="Good Standing" if cgpa_val >= 7.0 else ("At-Risk" if cgpa_val < 5.0 else "Satisfactory"),
    )
with kpi_cols[1]:
    st.metric(
        "Attendance",
        f"{overall_attendance:.1f}%",
        delta=f"Eligible (≥{policy_att_thresh:.0f}%)" if overall_attendance >= policy_att_thresh else f"⚠️ Shortage (<{policy_att_thresh:.0f}%)",
        delta_color="normal" if overall_attendance >= policy_att_thresh else "inverse",
    )
with kpi_cols[2]:
    st.metric(
        "Internal (CIE)",
        f"{avg_internal:.1f} / 60" if avg_internal is not None else "Pending",
        help="Continuous Internal Evaluation: Mid (30) + Assignment (10) + Quiz (10) + Viva (10)",
    )
with kpi_cols[3]:
    st.metric(
        "External Exam",
        f"{avg_external:.1f} / 40" if avg_external is not None else "Pending",
        help="End-Semester University Assessment out of 40 marks",
    )
with kpi_cols[4]:
    st.metric(
        "Total Assessment",
        f"{avg_total:.1f} / 100" if avg_total is not None else "Pending",
        delta="Combined Marks",
    )
with kpi_cols[5]:
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
(
    overview_tab,
    profile_tab,
    fees_tab,
    courses_tab,
    gradebook_tab,
    timetable_tab,
    ai_engine_tab,
    rec_tab,
    notif_tab,
) = st.tabs([
    "🏛️ Portal Overview",
    "👤 Personal & Parent Details",
    "💳 Fee Payment & Ledger",
    "📚 Academic Curriculum",
    "📊 CIE & External Gradebook (60/40)",
    "📅 Timetable & Attendance",
    "🧠 AI Decision Engine & XAI",
    "🎯 Targeted Recommendations & Alerts",
    f"🔔 Notifications ({unread_count})",
])

# =============================================================
# TAB 1: PORTAL OVERVIEW
# =============================================================
with overview_tab:
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
                st.write(f"**Permanent Admin:** `{get_configured_admin_email()}`")
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
with profile_tab:
    st.subheader("Student Personal & Parent Demographic Profile")
    st.caption("Official university records used for academic records, statutory verification, and notification dispatches.")

    col_pers, col_parent = st.columns(2)

    with col_pers:
        with st.container(border=True):
            st.markdown("#### 👤 Student Personal Details")
            st.write(f"**Full Name:** {student.get('full_name', '—')}")
            st.write(f"**Roll Number:** `{student.get('roll_number', '—')}`")
            st.write(f"**Permanent Enrollment No:** `{enrollment_number}`")
            st.write(f"**Student Phone Number:** `{student.get('phone', '—')}` 🟢 *Active for SMS*")
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
            st.write(f"**Parent Mobile Number:** `{student.get('parent_phone') or '+91 98480 12345'}` 🟢 *Active for Alerts*")
            st.write(f"**Parent Email Address:** `{student.get('parent_email') or 'parent@example.com'}`")
            st.write(f"**Permanent Residential Address:** {student.get('address') or 'Plot #42, Academic City, Hyderabad, Telangana - 500075'}")
            st.write(f"**Parent Qualification:** {student.get('parent_qualification') or 'B.Tech, MBA'}")
            st.write(f"**Parent Occupation:** {student.get('parent_occupation') or 'Senior Consultant'}")
            st.write(f"**Parent Organization:** {student.get('parent_organization') or 'State Administration / Corporate'}")

    # Interactive Form to Update Real-World Phone & Email
    st.markdown("### ✏️ Update Real-World Contact Numbers & Email")
    st.caption("Enter your actual personal phone number and personal email address to receive live notifications and AI recommendations.")

    with st.form("update_student_contact_form"):
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            new_phone = st.text_input("Student Mobile Number (for Real SMS Alerts)", value=student.get("phone", ""))
            new_parent_phone = st.text_input("Parent Mobile Number", value=student.get("parent_phone", ""))
        with ecol2:
            new_email = st.text_input("Student Email Address (for Real Email Advisories)", value=student.get("email", ""))
            new_address = st.text_area("Permanent Residential Address", value=student.get("address", ""), height=70)

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
with fees_tab:
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
                    <div><b>Permanent Enrollment No:</b> {enrollment_number}</div>
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
with courses_tab:
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
with gradebook_tab:
    st.subheader("Continuous Internal Evaluation (CIE) & End-Semester Gradebook")
    st.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; font-size: 0.88rem;">
            <b>Institutional Evaluation Architecture:</b>  
            Each course is evaluated on a <b>100-mark scheme</b> split into:  
            • <b>60 Internal Marks (CIE):</b> <b>30</b> for Mid-Term Exam + <b>10</b> for Assignments + <b>10</b> for Formative Quizzes + <b>10</b> for Viva Voce / Practical Evaluation.  
            • <b>40 External Marks (SEE):</b> End-Semester Summative University Examination.  
            <i>Note: Marks and session attendance can only be submitted by the course faculty assigned to your section.</i>
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
            ext = ca.get("external_marks")
            total = ca.get("overall_total")

            # Grade letter determination
            if total is not None:
                if total >= 90: grade = "O (Outstanding)"
                elif total >= 80: grade = "A+ (Excellent)"
                elif total >= 70: grade = "A (Very Good)"
                elif total >= 60: grade = "B+ (Good)"
                elif total >= 50: grade = "B (Above Average)"
                elif total >= 40: grade = "C (Pass)"
                else: grade = "F (Fail)"
            else:
                grade = "Incomplete"

            gradebook_rows.append({
                "Course Code": ca["course_code"],
                "Course Title": ca["course_name"],
                "Credits": ca["credits"],
                "Mid /30": f"{mid:.1f}" if mid is not None else "—",
                "Assn /10": f"{assn:.1f}" if assn is not None else "—",
                "Quiz /10": f"{quiz:.1f}" if quiz is not None else "—",
                "Viva /10": f"{viva:.1f}" if viva is not None else "—",
                "Internal /60": f"{internal:.1f}" if internal is not None else "—",
                "External /40": f"{ext:.1f}" if ext is not None else "—",
                "Total /100": f"{total:.1f}" if total is not None else "—",
                "Grade": grade,
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
                        <div><b>Permanent Enrollment No:</b> {enrollment_number}</div>
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
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">CIE /60</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">SEE /40</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Total /100</th>
                                <th style="padding: 8px; border: 1px solid #091e3a; text-align: center;">Grade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr style="border-bottom: 1px solid #cbd5e1;">
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; font-family: monospace;">{r["Course Code"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0;">{r["Course Title"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Credits"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["Internal /60"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center;">{r["External /40"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center; font-weight: 700;">{r["Total /100"]}</td>
                                <td style="padding: 6px 8px; border: 1px solid #e2e8f0; text-align: center; font-weight: 700;">{r["Grade"].split()[0]}</td>
                            </tr>
                            ''' for r in gradebook_rows])}
                        </tbody>
                    </table>

                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 2px solid #091e3a; padding-top: 1rem; margin-top: 1rem;">
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 800;">Semester Grade Point Average (SGPA): {cgpa_val:.2f} / 10.0</div>
                            <div style="font-size: 0.9rem; color: #166534; font-weight: 700; margin-top: 0.2rem;">Final Trajectory: {overall_perf.upper()}</div>
                            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">Total Earned Credits: 20.0 / 20.0 Credits</div>
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
with timetable_tab:
    st.subheader(f"Weekly Class Schedule · Section {assigned_section}")
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


# =============================================================
# TAB 7: AI DECISION ENGINE & EXPLAINABLE AI (XAI)
# =============================================================
with ai_engine_tab:
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
with rec_tab:
    st.subheader("AI-Generated Recommendations & Outbound Notification Services")
    st.caption("Personalized action plans and real-world delivery to your verified email and mobile devices.")

    # Real-World Outbound Delivery Panel
    st.markdown("### 📡 Real-World Outbound Delivery Center")
    admin_sender = get_configured_admin_email()

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 1rem;">
                <b>🏛️ Outbound Institutional Gateway Configuration:</b><br>
                • <b>Permanent Admin Sender:</b> <code>{admin_sender}</code><br>
                • <b>Student Recipient Email:</b> <code>{student_email}</code><br>
                • <b>Student Mobile Number:</b> <code>{student_phone}</code><br>
                • <b>Parent Mobile Number:</b> <code>{student.get('parent_phone', 'Not Set')}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button("📧 Send AI Recommendations to My Email", type="primary", use_container_width=True):
                all_recs = []
                if course_assessments:
                    for ca in course_assessments:
                        r_items = generate_course_level_recommendations(ca, policies=academic_policies)
                        for itm in r_items:
                            all_recs.append(f"{ca['course_code']}: {itm.get('text') if isinstance(itm, dict) else itm}")
                else:
                    all_recs = ["Maintain continuous class attendance and submit all formative homework assignments."]

                email_res = send_student_recommendations_email(
                    to_email=student_email,
                    full_name=full_name,
                    roll_no=roll_number,
                    enrollment_no=enrollment_number,
                    risk_level=overall_risk,
                    predicted_perf=overall_perf,
                    cgpa=cgpa_val,
                    attendance=overall_attendance,
                    recommendations_list=all_recs[:5],
                    xai_summary=xai_data.get("executive_summary", ""),
                )

                if email_res.get("success"):
                    st.success(f"✅ {email_res.get('message')}")
                elif email_res.get("status") == "config_required":
                    st.info(f"ℹ️ {email_res.get('message')}")
                else:
                    st.error(f"❌ {email_res.get('message')}")

        with btn_col2:
            if st.button("📱 Send Academic Advisory via SMS", use_container_width=True):
                top_action = f"Attendance: {overall_attendance:.1f}%. Keep engaging in lectures."
                sms_res = send_academic_recommendation_sms(
                    phone_number=student_phone,
                    full_name=full_name,
                    roll_no=roll_number,
                    risk_level=overall_risk,
                    predicted_perf=overall_perf,
                    top_action=top_action,
                )

                if sms_res.get("success"):
                    st.success(f"✅ {sms_res.get('message')}")
                elif sms_res.get("status") == "config_required":
                    st.info(f"ℹ️ {sms_res.get('message')}")
                else:
                    st.error(f"❌ {sms_res.get('message')}")

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
with notif_tab:
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
