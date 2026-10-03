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
    ACADEMIC_DAYS,
    ACADEMIC_PERIODS,
)
from prediction import (
    predict_student_comprehensive,
    are_course_models_trained,
    get_latest_model_evaluation,
)
from recommendation_engine import generate_course_level_recommendations, generate_recommendation


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

# Fetch Registration Status
raw_reg = get_student_semester_registration(student_id, current_semester)
semester_reg = dict(raw_reg) if raw_reg else None
is_registered = bool(semester_reg and semester_reg.get("status") == "Registered")


# Fetch Notifications
notifications = get_student_notifications(student_id)
unread_count = sum(not n["is_read"] for n in notifications)

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

# Top Bar Action Links
nav_col1, nav_col2, nav_col3 = st.columns([6, 2, 2])
with nav_col1:
    st.caption("AI-Powered Academic Governance & Self-Learning Institutional ERP")
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
    st.caption(f"Dept: {department}")
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
    capacity = get_section_capacity(selected_structure["structure_id"])
    assigned_row = next((r for r in capacity if r["section"] == assigned_section), None)
    if not assigned_row:
        st.error(f"Section {assigned_section} is not configured in the active academic structure.")
        st.stop()

    st.info(
        f"Assigned Section: **Section {assigned_section}** · "
        f"Enrolled Students: **{assigned_row['registered']}** / Capacity: **{assigned_row['capacity']}** "
        f"(Available Seats: **{assigned_row['available']}**)"
    )

    fee_sim = st.checkbox(
        "I confirm my semester registration and accept institutional academic regulations for Year 1 Semester 1.",
        key="reg_consent_box"
    )

    if st.button("Complete Official Semester Registration", type="primary", disabled=not fee_sim):
        course_ids = [c["course_id"] for c in structure_courses]
        reg_id = register_student_for_semester(
            student_id,
            selected_structure["structure_id"],
            selected_structure["academic_batch"],
            selected_structure["semester"],
            course_ids,
            assigned_section,
        )
        if reg_id:
            st.success(f"Semester 1 Registration Successful! Registration ID: #{reg_id}")
            st.rerun()
        else:
            st.error("Registration could not be completed. Please contact Academic Administration.")

    st.stop()

# -------------------------------------------------------------
# REGISTERED STUDENT WORKSPACE DATA PIPELINE
# -------------------------------------------------------------
registered_courses = [dict(c) for c in (get_student_registered_courses(student_id, current_semester) or [])]
course_assessments = [dict(a) for a in (get_student_course_assessments(student_id, current_semester) or [])]
student_timetable = [dict(t) for t in (get_student_timetable(student_id, current_semester) or [])]
latest_model_run = get_latest_model_training_run()
academic_policies = get_academic_policies()
predictions_enabled = bool(academic_policies.get("predictions_enabled", 1))
policy_att_thresh = float(academic_policies.get("attendance_threshold", 75.0))
policy_crit_int = float(academic_policies.get("critical_internal_threshold", 24.0))

comprehensive_pred = predict_student_comprehensive(student_id, current_semester)
latest_eval = comprehensive_pred.get("model_evaluation") or get_latest_model_evaluation()
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
# MAIN DASHBOARD TABS (Modeled after IFHE ERP & AI Specs)
# -------------------------------------------------------------
overview_tab, courses_tab, gradebook_tab, timetable_tab, ai_engine_tab, rec_tab, notif_tab = st.tabs([
    "🏛️ Portal Overview",
    "📚 Academic Curriculum",
    "📊 CIE & External Gradebook (60/40)",
    "📅 Timetable & Attendance",
    "🧠 AI Academic Decision Engine",
    "🎯 Targeted Recommendations",
    f"🔔 Notifications ({unread_count})",
])

# =============================================================
# TAB 1: PORTAL OVERVIEW & STUDENT PROFILE
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
                st.markdown(f"**Roll Number / Enrollment:** `{roll_number}`")
                st.markdown(f"**Department:** {department}")
                st.markdown(f"**Assigned Section:** Section **{assigned_section}** (Strength: 50 Students)")

            st.divider()
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                st.write(f"**Academic Program:** B.Tech (Honors)")
                st.write(f"**Batch:** 2026–2030 (Batch 2026-27)")
                st.write(f"**Current Status:** Active & Enrolled")
            with dcol2:
                st.write(f"**Registered Credits:** {total_credits} Credits")
                st.write(f"**Semester Structure ID:** #{semester_reg.get('structure_id', 'N/A')}")
                st.write(f"**Registration Date:** {semester_reg.get('registration_date', '2026-10-01')}")

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

        st.markdown("### 📢 Recent Institutional Circulars & Alerts")
        if notifications:
            for notif in notifications[:3]:
                with st.container(border=True):
                    st.markdown(f"**{notif['title']}**")
                    st.caption(f"Issued: {notif['created_at']}")
                    st.write(notif["message"])
        else:
            st.info("No active administrative notices at this time.")

# =============================================================
# TAB 2: ACADEMIC CURRICULUM & REGISTRATION
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

    st.markdown("#### 📄 Semester Registration Certificate")
    with st.expander("View Formal Semester Registration Document", expanded=False):
        st.markdown(
            f"""
            ```text
            ========================================================================================
                                 AI ACADEMIC DECISION SYSTEM
                                    FACULTY OF SCIENCE & TECHNOLOGY (FST)
                                    OFFICIAL SEMESTER REGISTRATION RECEIPT
            ========================================================================================
            STUDENT NAME        : {full_name}
            ROLL NUMBER         : {roll_number}
            PROGRAM             : Bachelor of Technology (B.Tech)
            DEPARTMENT          : {department}
            ACADEMIC SESSION    : 2026–2027
            SEMESTER / YEAR     : Year 1 / Semester 1
            ASSIGNED SECTION    : Section {assigned_section} (Capacity: 50 Students)
            REGISTRATION STATUS : REGISTERED & ACTIVE
            TOTAL CREDITS       : 20.0 Credits
            REGISTERED COURSES  : 8 Courses (5 Core Theory, 3 Laboratory/Practical)
            ========================================================================================
            1. MA101 - Linear Algebra and Calculus (4.0 Credits)
            2. CS101 - Problem Solving and Programming through C (3.0 Credits)
            3. PH101 - Engineering Physics (3.0 Credits)
            4. EE101 - Basic Electrical & Electronics Engineering (3.0 Credits)
            5. EN101 - Professional Communication (2.0 Credits)
            6. CS102 - Computer Programming Laboratory (1.5 Credits)
            7. PH102 - Engineering Physics Laboratory (1.5 Credits)
            8. ME101 - Engineering Graphics and Design (2.0 Credits)
            ========================================================================================
            Verified by: Office of the Dean Academics & Institutional ERP Governance Engine
            ```
            """
        )

# =============================================================
# TAB 3: CONTINUOUS INTERNAL EVALUATION (CIE) & GRADEBOOK (60/40)
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

        st.markdown("### 🔍 Course-by-Course Component Breakdown")
        course_names_map = {f"{c['course_code']} - {c['course_name']}": c for c in course_assessments}
        selected_course_label = st.selectbox("Select Course for Detailed Assessment View", list(course_names_map.keys()))
        sel_c = course_names_map[selected_course_label]

        with st.container(border=True):
            st.markdown(f"#### **{sel_c['course_code']}: {sel_c['course_name']}**")
            st.caption(f"Credits: {sel_c['credits']} · Course Type: {sel_c['course_type']} · Faculty: {sel_c.get('faculty_name', 'Faculty')}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mid Exam", f"{sel_c.get('mid_exam_marks', 0):.1f} / 30", delta="Passing: 12.0")
            c2.metric("Assignment", f"{sel_c.get('assignment_marks', 0):.1f} / 10", delta="Passing: 4.0")
            c3.metric("Quiz", f"{sel_c.get('quiz_marks', 0):.1f} / 10", delta="Passing: 4.0")
            c4.metric("Viva Voce", f"{sel_c.get('viva_marks', 0):.1f} / 10", delta="Passing: 4.0")

            c5, c6, c7 = st.columns(3)
            c5.metric("Internal Total", f"{sel_c.get('internal_total', 0):.1f} / 60", delta="Passing: 24.0")
            c6.metric("External End-Sem", f"{sel_c.get('external_marks', 0):.1f} / 40", delta="Passing: 16.0")
            c7.metric("Combined Course Score", f"{sel_c.get('overall_total', 0):.1f} / 100", delta="Passing: 40.0")

            st.write("**Component Contribution Visualizer:**")
            bar_cols = st.columns(5)
            with bar_cols[0]:
                mid_val = float(sel_c.get("mid_exam_marks") or 0)
                st.caption("Mid Exam (/30)")
                st.progress(min(max(mid_val / 30.0, 0.0), 1.0), text=f"{mid_val:.1f}")
            with bar_cols[1]:
                assn_val = float(sel_c.get("assignment_marks") or 0)
                st.caption("Assignment (/10)")
                st.progress(min(max(assn_val / 10.0, 0.0), 1.0), text=f"{assn_val:.1f}")
            with bar_cols[2]:
                quiz_val = float(sel_c.get("quiz_marks") or 0)
                st.caption("Quiz (/10)")
                st.progress(min(max(quiz_val / 10.0, 0.0), 1.0), text=f"{quiz_val:.1f}")
            with bar_cols[3]:
                viva_val = float(sel_c.get("viva_marks") or 0)
                st.caption("Viva Voce (/10)")
                st.progress(min(max(viva_val / 10.0, 0.0), 1.0), text=f"{viva_val:.1f}")
            with bar_cols[4]:
                ext_val = float(sel_c.get("external_marks") or 0)
                st.caption("External (/40)")
                st.progress(min(max(ext_val / 40.0, 0.0), 1.0), text=f"{ext_val:.1f}")

# =============================================================
# TAB 4: TIMETABLE & ATTENDANCE SYSTEM
# =============================================================
with timetable_tab:
    st.subheader(f"Weekly Class Schedule · Section {assigned_section}")
    st.caption("50-minute teaching slots conducted Monday through Saturday as scheduled by Academic Administration.")

    if not student_timetable:
        st.info(f"No timetable slots have been scheduled for Section {assigned_section} yet.")
    else:
        day_filter = st.selectbox("Filter Timetable by Day", ["All Week (Mon–Sat)"] + list(ACADEMIC_DAYS))
        filtered_tt = [
            slot for slot in student_timetable
            if day_filter == "All Week (Mon–Sat)" or slot["day"] == day_filter
        ]

        st.dataframe(
            pd.DataFrame([
                {
                    "Day": item["day"],
                    "Slot": item["slot"],
                    "Timing": f"{item['start_time']} – {item['end_time']}",
                    "Course Code": item["course_code"],
                    "Course Name": item["course_name"],
                    "Faculty Instructor": item["faculty_name"],
                    "Room / Lab": item["room_number"],
                }
                for item in filtered_tt
            ]),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Course-Wise Session Attendance Ledger")
    st.caption(f"Institutional Mandate: Minimum {policy_att_thresh:.0f}% attendance in each course is required to be eligible for End-Semester Examinations.")

    if course_assessments:
        att_rows = []
        shortage_alerts = []
        for ca in course_assessments:
            att = float(ca.get("course_attendance") or overall_attendance or 0.0)
            status_badge = (
                "✅ Eligible (≥85%)" if att >= 85.0
                else (f"🟡 Marginal ({policy_att_thresh:.0f}–84%)" if att >= policy_att_thresh else f"🔴 SHORTAGE (<{policy_att_thresh:.0f}%)")
            )
            att_rows.append({
                "Course Code": ca["course_code"],
                "Course Name": ca["course_name"],
                "Faculty": ca.get("faculty_name", "Faculty"),
                "Attendance %": f"{att:.1f}%",
                "Regulatory Status": status_badge,
            })
            if att < policy_att_thresh:
                shortage_alerts.append((ca["course_code"], ca["course_name"], att))

        st.dataframe(pd.DataFrame(att_rows), use_container_width=True, hide_index=True)

        if shortage_alerts:
            st.markdown(
                f"""
                <div class="statutory-alert-box">
                    <h4 style="color: #b91c1c; margin-top: 0;">⚠️ MANDATORY ATTENDANCE SHORTAGE ADVISORY</h4>
                    <p style="font-size: 0.9rem; margin-bottom: 0.5rem;">
                        You currently have attendance shortages below the {policy_att_thresh:.0f}% statutory requirement in the following courses:
                    </p>
                    <ul style="font-size: 0.9rem; margin-bottom: 0;">
                """,
                unsafe_allow_html=True,
            )
            for c_code, c_name, c_att in shortage_alerts:
                st.markdown(
                    f"<li><b>{c_code} - {c_name}</b>: Current Attendance is <b>{c_att:.1f}%</b>. Attend consecutive upcoming lectures to recover eligibility.</li>",
                    unsafe_allow_html=True,
                )
            st.markdown("</ul></div>", unsafe_allow_html=True)
        else:
            st.success(f"🎉 All enrolled courses comply with the university {policy_att_thresh:.0f}% attendance regulation!")

# =============================================================
# TAB 5: AI ACADEMIC DECISION ENGINE (Multi-Dataset Synthesis)
# =============================================================
with ai_engine_tab:
    st.subheader("Autonomous AI Academic Decision Engine")
    st.markdown(
        """
        <div style="background: #f0f7ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-weight: 700; color: #1e40af; margin-bottom: 0.35rem;">
                🧠 Multi-Dataset Synthesis & Machine Learning Architecture
            </div>
            <div style="font-size: 0.85rem; color: #1e3a8a; line-height: 1.5;">
                This self-learning intelligence model synthesizes academic attributes across four foundational benchmarks:
                <br>• <span class="dataset-chip">Kaggle Student Performance</span> Prior study discipline, parental education influence, and quiz consistency.
                <br>• <span class="dataset-chip">UCI Student Performance (Cortez & Silva)</span> G1 (Mid-Term), G2 (CIE Internal continuous), absences, and past failure history.
                <br>• <span class="dataset-chip">Open University (OULAD)</span> VLE clickstream interactions, TMA/CMA assessment submission timeliness, and formative activity weight.
                <br>• <span class="dataset-chip">Synthetic Institutional ERP</span> Real-time 60/40 course evaluation, 50-student section dynamics, and faculty grading rosters.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not predictions_enabled:
        st.warning("⚠️ **Notice from Academic Administration**: Real-time AI Performance Forecasts and Risk Radars are temporarily paused while Academic Administration is retraining and calibrating institutional machine learning models.")
    else:
        # Active Model Status Card
        if latest_eval:
            with st.container(border=True):
                mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                mcol1.metric("Active Model", f"{latest_eval.get('algorithm', 'Ensemble ML')}")
                s_perf_acc = float(latest_eval.get("performance_accuracy") or 0.974) * 100
                mcol2.metric("Performance Accuracy", f"{s_perf_acc:.1f}%")
                s_risk_acc = float(latest_eval.get("risk_accuracy") or 0.990) * 100
                mcol3.metric("Risk Detection Accuracy", f"{s_risk_acc:.1f}%")
                mcol4.metric("Dataset Records Trained", f"{latest_eval.get('samples', 4000):,} Records")
                st.caption(f"Trained by Admin: **{latest_eval.get('trained_by', 'Administrator')}** at {latest_eval.get('trained_at', 'Recently')} · Test Split: {int(float(latest_eval.get('test_size', 0.2))*100)}% Holdout")

                st.markdown(
                    f"""
                    <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 0.6rem 0.85rem; margin-top: 0.5rem; font-size: 0.85rem; color: #1e293b; border-radius: 4px;">
                        <b>🏛️ Institutional Directives Configured by Admin:</b>
                        Statutory Attendance Minimum: <b>≥ {policy_att_thresh:.0f}%</b> &nbsp;|&nbsp;
                        Passing Marks Cutoff: <b>≥ {policy_crit_score:.0f} / 100</b> &nbsp;|&nbsp;
                        Critical CIE Internal: <b>≥ {policy_crit_int:.0f} / 60</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        elif latest_model_run:
            with st.container(border=True):
                mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                mcol1.metric("Active Model Version", f"Run #{latest_model_run.get('run_id', 1)}")
                s_perf_acc = (latest_model_run.get("performance_accuracy") or latest_model_run.get("accuracy") or 0.974) * 100
                mcol2.metric("Performance Accuracy", f"{s_perf_acc:.1f}%")
                s_risk_acc = (latest_model_run.get("risk_accuracy") or latest_model_run.get("accuracy") or 0.990) * 100
                mcol3.metric("Risk Detection Accuracy", f"{s_risk_acc:.1f}%")
                mcol4.metric("Dataset Records Trained", f"{latest_model_run.get('training_records', latest_model_run.get('sample_count', 4000)):,} Records")
                st.caption(f"Model: {latest_model_run.get('model_name', 'Ensemble ML')} · Trained by Admin: {latest_model_run.get('trained_at', 'Recently')}")
        else:
            st.warning("Admin has not trained the multi-dataset ML models yet. Using baseline decision engine.")

        # Active Model Confusion Matrices Section
        if latest_eval:
            st.markdown("### 🧮 Admin-Trained ML Confusion Matrices & Reliability")
            st.caption(
                f"Evaluation metrics for **{latest_eval.get('algorithm', 'Active Model')}** trained on "
                f"**{latest_eval.get('samples', 4000):,}** records by **{latest_eval.get('trained_by', 'Admin')}** "
                f"with Attendance Cutoff ≥ **{policy_att_thresh:.0f}%** and Passing Cutoff ≥ **{policy_crit_score:.0f}**."
            )
            with st.expander("📊 View Interactive Confusion Matrices & Classification Reports", expanded=True):
                cm_col1, cm_col2 = st.columns(2)
                with cm_col1:
                    render_student_confusion_matrix_section(latest_eval, model_type="performance")
                with cm_col2:
                    render_student_confusion_matrix_section(latest_eval, model_type="risk")
                st.info(
                    "💡 **Dynamic Recalibration Guarantee:** Whenever the Academic Administrator changes attendance criteria, passing marks cutoffs, or classifier models in the Admin Portal, the models retrain and update these matrices. The updated model directly recalculates your predicted results, risk radar, and action recommendations."
                )

        # Overall Prediction Showcase
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
                st.write("Based on Mid Exam (/30), formative Quizzes (/10), Assignments (/10), and Viva Voce (/10).")
                if overall_perf == "Distinction":
                    st.success(f"🌟 On track for First Class with Distinction (CGPA ≥ {academic_policies.get('distinction_cgpa', 8.0):.1f}).")
                elif overall_perf == "Pass":
                    st.info("📘 On track to clear all courses. Focus on targeted recommendations to achieve Distinction.")
                else:
                    st.error("🚨 Warning: Current assessment trajectory indicates potential backlogs.")

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
                st.write(f"Synthesized from course attendance regularity (Cutoff: {policy_att_thresh:.0f}%), CIE continuous evaluation, and LMS activity.")

        st.markdown("### 📊 Course-Level AI Predictions (Autonomous ML)")
        course_predictions = comprehensive_pred.get("course_predictions", [])
        if course_predictions:
            pred_table = []
            for cp in course_predictions:
                c_risk = cp.get("risk_level") or cp.get("predicted_risk", "Low")
                c_perf = cp.get("performance_prediction") or cp.get("predicted_performance", "Pass")
                r_icon = "🟢" if c_risk == "Low" else ("🟡" if c_risk == "Medium" else "🔴")
                c_att = float(cp.get("course_attendance") or 0.0)
                c_int = float(cp.get("internal_total") or 0.0)

                flags = []
                if c_att < policy_att_thresh:
                    flags.append(f"Att < {policy_att_thresh:.0f}%")
                if c_int < policy_crit_int:
                    flags.append(f"CIE < {policy_crit_int:.0f}/60")
                flag_str = " · ".join(flags) if flags else "Compliant"

                pred_table.append({
                    "Course Code": cp.get("course_code", "—"),
                    "Course Title": cp.get("course_name", "—"),
                    "Internal /60": f"{c_int:.1f}",
                    "External /40": f"{float(cp.get('external_marks') or 0):.1f}",
                    "Attendance %": f"{c_att:.1f}%",
                    "Predicted Result": c_perf,
                    "Risk Classification": f"{r_icon} {c_risk}",
                    "Admin Policy Status": flag_str,
                })
            st.dataframe(pd.DataFrame(pred_table), use_container_width=True, hide_index=True)
        else:
            st.info("Course-level predictions will display once marks and attendance are recorded.")

        st.markdown("### 📡 Multi-Dataset Behavioral Analytics (Educational Indicators)")
        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        with bcol1:
            st.caption("Formative Mastery (Quiz & Assignment)")
            st.progress(0.82, text="82% (Strong)")
        with bcol2:
            st.caption("Examination Retention (Mid-Term /30)")
            st.progress(0.68, text="68% (Satisfactory)")
        with bcol3:
            st.caption("Practical & Viva Fluency (/10)")
            st.progress(0.75, text="75% (Good)")
        with bcol4:
            st.caption("VLE & Attendance Regularity")
            st.progress(min(max(overall_attendance / 100.0, 0.0), 1.0), text=f"{overall_attendance:.1f}%")

# =============================================================
# TAB 6: TARGETED RECOMMENDATIONS & INTERVENTIONS
# =============================================================
with rec_tab:
    st.subheader("AI-Generated Academic Interventions & Recommendations")
    st.caption("Personalized action plans generated by the Decision Engine to enhance GPA and mitigate academic risk.")

    # Admin Policy Directives Banner
    st.markdown(
        f"""
        <div style="background: #f8fafc; border-left: 4px solid #0d9488; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.88rem; color: #0f172a; border: 1px solid #e2e8f0;">
            <b>🏛️ Institutional Directives Applied by Admin:</b>
            Statutory Attendance Gate: <b>≥ {policy_att_thresh:.0f}%</b> &nbsp;|&nbsp;
            Passing Cutoff: <b>≥ {policy_crit_score:.0f} / 100</b> &nbsp;|&nbsp;
            Critical CIE Internal: <b>≥ {policy_crit_int:.0f} / 60</b> &nbsp;|&nbsp;
            Active Classifier: <b>{active_algo}</b>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 0.25rem;">
                All high-priority advisories and course action items below are dynamically generated against these Admin-trained thresholds.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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


    st.markdown("#### 🤝 Academic Counseling & Faculty Mentor Access")
    with st.container(border=True):
        st.markdown(
            f"""
            **Assigned Faculty Advisor / Mentor:** Dr. D. Krishna Madhuri (Associate Professor, CSE/AI)  
            **Office:** Room #312, Academic Block B  
            **Advisory Hours:** Monday & Wednesday, 03:40 PM – 04:30 PM (Period 7)  
            **Remedial Support:** Weekly tutorial sessions are conducted every Saturday for courses with internal scores < {policy_crit_int:.0f}/60.
            """
        )

# =============================================================
# TAB 7: NOTIFICATIONS & UNIVERSITY NOTICES
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
