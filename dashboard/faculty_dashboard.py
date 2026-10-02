"""
===========================================================
AI-Based Autonomous Academic Decision System
Faculty Teaching, Assessment, and Academic Governance Workspace
Theme: AI Academic Governance
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
===========================================================
"""

import sys
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auth import require_faculty
from database import (
    ACADEMIC_DAYS,
    ACADEMIC_PERIODS,
    SECTION_NAMES,
    create_student_notification,
    get_connection,
    get_course_assessment_roster,
    get_course_attendance_percentage,
    get_faculty_timetable,
    get_recorded_attendance_session,
    get_session_attendance_roster,
    get_student_by_roll,
    get_student_course_assessments,
    get_teachable_course_options,
    request_faculty_teaching_assignment,
    save_course_assessment,
    submit_session_attendance,
)
from email_service import send_email
from prediction import predict_registered_course, are_course_models_trained
from recommendation_engine import generate_course_level_recommendations
from sms_service import send_academic_update_sms

require_faculty()
faculty = dict(st.session_state.user_data or {})

if not faculty or "faculty_id" not in faculty:
    st.info("Please log in as a faculty member to access this dashboard.")
    st.stop()

faculty_id = faculty["faculty_id"]
faculty_name = faculty.get("full_name", "Faculty")
dept = faculty.get("department", "Engineering & Technology")
designation = faculty.get("designation", "Faculty Instructor")
employee_id = faculty.get("employee_id", "FACULTY")

# Top Header
head_col, log_col = st.columns([5, 1], vertical_alignment="center")
with head_col:
    st.title("👨‍🏫 Faculty Academic & Evaluation Workspace")
    st.caption(
        f"**{faculty_name}** ({employee_id}) · {designation} · {dept} · "
        "Autonomous Academic Governance & CIE 60/40 Evaluation"
    )
with log_col:
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

schedule = get_faculty_timetable(faculty_id)

# Quick Schedule Summary Bar
if schedule:
    unique_courses = set(f"{item['course_code']} ({item['section']})" for item in schedule)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Weekly Class Sessions", f"{len(schedule)} Slots")
    k2.metric("Assigned Courses / Sections", f"{len(unique_courses)} Assigned")
    k3.metric("Section Strength", "50 Students / Section")
    k4.metric("Evaluation Framework", "60 Internal / 40 External")
else:
    st.warning("You do not have any approved timetable slots assigned yet. Request assignments below.")

# Tabs
tab_assess, tab_att, tab_search, tab_risk, tab_analytics, tab_req = st.tabs([
    "📝 Course Assessment (60/40 CIE)",
    "📋 Session Attendance",
    "🔍 Student Search & Summary",
    "🚨 At-Risk Student Detection",
    "📊 Section Analytics & Trends",
    "➕ Request Teaching Assignment",
])

# =============================================================
# TAB 1: COURSE ASSESSMENT (60/40 CIE)
# =============================================================
with tab_assess:
    st.subheader("Continuous Internal Evaluation (CIE) & External Marks Entry")
    st.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; margin-bottom: 1rem; font-size: 0.85rem;">
            <b>Institutional Assessment Model:</b> Total Course Score = 100 Marks.  
            • <b>60 Internal:</b> 30 Mid Exam + 10 Assignment + 10 Quiz + 10 Viva Voce.  
            • <b>40 External:</b> Summative End-Semester University Examination.  
            <i>Note: Only assigned faculty can submit marks for registered students in their assigned sections.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not schedule:
        st.info("Approved teaching timetable slots are required to enter assessments.")
    else:
        schedule_options = {
            f"{item['course_code']} - {item['course_name']} · Section {item['section']} ({item['day']} {item['slot']})": item
            for item in schedule
        }
        selected_slot_label = st.selectbox("Select Assigned Course & Section", list(schedule_options.keys()), key="assess_slot_picker")
        selected_slot = schedule_options[selected_slot_label]

        roster = get_course_assessment_roster(selected_slot["timetable_id"], faculty_id)
        if not roster:
            st.info("No registered students found for this course and section.")
        else:
            st.markdown(f"#### Roster & Assessment Ledger · Section {selected_slot['section']} ({len(roster)} Registered Students)")
            
            # Overview Table of Roster
            roster_summary = []
            for s in roster:
                mid = s.get("mid_exam_marks")
                assn = s.get("assignment_marks")
                quiz = s.get("quiz_marks")
                viva = s.get("viva_marks")
                ext = s.get("external_marks")
                internal = (mid or 0) + (assn or 0) + (quiz or 0) + (viva or 0) if mid is not None else None
                overall = internal + ext if (internal is not None and ext is not None) else None
                
                roster_summary.append({
                    "Roll Number": s["roll_number"],
                    "Student Name": s["full_name"],
                    "Mid /30": f"{mid:.1f}" if mid is not None else "—",
                    "Assn /10": f"{assn:.1f}" if assn is not None else "—",
                    "Quiz /10": f"{quiz:.1f}" if quiz is not None else "—",
                    "Viva /10": f"{viva:.1f}" if viva is not None else "—",
                    "Internal /60": f"{internal:.1f}" if internal is not None else "—",
                    "External /40": f"{ext:.1f}" if ext is not None else "—",
                    "Total /100": f"{overall:.1f}" if overall is not None else "—",
                })
            
            with st.expander(f"View Complete Section {selected_slot['section']} Assessment Table ({len(roster)} Students)", expanded=False):
                st.dataframe(pd.DataFrame(roster_summary), use_container_width=True, hide_index=True)

            # Single Student Marks Entry Form
            st.markdown("##### ✏️ Enter / Update Student Assessment")
            student_options = {
                f"{item['roll_number']} · {item['full_name']}": item
                for item in roster
            }
            selected_student_label = st.selectbox("Select Student to Grade", list(student_options.keys()))
            selected_student = student_options[selected_student_label]

            with st.form("course_assessment_form"):
                fcol1, fcol2, fcol3 = st.columns(3)
                with fcol1:
                    mid_exam = st.number_input(
                        "Mid Exam (/30)", min_value=0.0, max_value=30.0,
                        value=float(selected_student["mid_exam_marks"]) if selected_student["mid_exam_marks"] is not None else 18.0,
                        step=0.5,
                    )
                    viva = st.number_input(
                        "Viva Voce (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["viva_marks"]) if selected_student["viva_marks"] is not None else 7.0,
                        step=0.5,
                    )
                with fcol2:
                    assignment = st.number_input(
                        "Assignment (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["assignment_marks"]) if selected_student["assignment_marks"] is not None else 7.5,
                        step=0.5,
                    )
                    external = st.number_input(
                        "End-Semester External Exam (/40)", min_value=0.0, max_value=40.0,
                        value=float(selected_student["external_marks"]) if selected_student["external_marks"] is not None else 28.0,
                        step=0.5,
                    )
                with fcol3:
                    quiz = st.number_input(
                        "Formative Quiz (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["quiz_marks"]) if selected_student["quiz_marks"] is not None else 8.0,
                        step=0.5,
                    )
                    current_int = mid_exam + assignment + quiz + viva
                    current_tot = current_int + external
                    st.metric("Internal Total", f"{current_int:.1f} / 60")
                    st.metric("Course Total", f"{current_tot:.1f} / 100")

                save_assessment = st.form_submit_button("Save Assessment Record", type="primary", use_container_width=True)

            if save_assessment:
                success, message = save_course_assessment(
                    selected_slot["timetable_id"],
                    faculty_id,
                    selected_student["student_id"],
                    {
                        "assignment_marks": assignment,
                        "quiz_marks": quiz,
                        "mid_exam_marks": mid_exam,
                        "viva_marks": viva,
                        "external_marks": external,
                    },
                )
                if not success:
                    st.error(message)
                else:
                    internal_total = assignment + quiz + mid_exam + viva
                    course_att = get_course_attendance_percentage(
                        selected_student["student_id"],
                        selected_slot["course_id"],
                        selected_slot["section"],
                    )
                    att_str = f", attendance {course_att:.1f}%" if course_att is not None else ""
                    update_msg = (
                        f"{selected_slot['course_name']} marks saved: "
                        f"Internal {internal_total:.1f}/60, External {external:.1f}/40{att_str}."
                    )
                    create_student_notification(selected_student["student_id"], "Course Assessment Updated", update_msg)
                    st.success(f"Assessment saved successfully for {selected_student['full_name']}!")
                    st.rerun()

# =============================================================
# TAB 2: SESSION ATTENDANCE
# =============================================================
with tab_att:
    st.subheader("Classroom Session Attendance Register")
    st.caption("Mark attendance for the 50 students in your assigned section. Once submitted, session attendance is locked to maintain audit integrity.")

    if not schedule:
        st.info("Approved teaching timetable slots are required to record attendance.")
    else:
        att_slot_options = {
            f"{item['course_code']} · Section {item['section']} ({item['day']} {item['slot']})": item
            for item in schedule
        }
        sel_att_slot_label = st.selectbox("Select Scheduled Class", list(att_slot_options.keys()), key="att_slot_picker")
        sel_att_slot = att_slot_options[sel_att_slot_label]

        session_date = st.date_input("Class Date", value=date.today())
        date_text = session_date.isoformat()

        if session_date.strftime("%a") != sel_att_slot["day"]:
            st.warning(f"Note: This timetable slot is designated for {sel_att_slot['day']}. Today is {session_date.strftime('%a')}.")

        already_submitted = get_recorded_attendance_session(sel_att_slot["timetable_id"], date_text)
        if already_submitted:
            st.success(f"✅ Attendance has already been submitted and locked for {sel_att_slot['course_code']} Section {sel_att_slot['section']} on {date_text}.")
        else:
            att_roster = get_session_attendance_roster(sel_att_slot["timetable_id"], faculty_id)
            if not att_roster:
                st.info("No registered students found for this course and section.")
            else:
                st.write(f"Marking attendance for **Section {sel_att_slot['section']}** ({len(att_roster)} Students):")
                with st.form("session_attendance_form"):
                    roster_frame = pd.DataFrame([
                        {
                            "Student ID": item["student_id"],
                            "Roll Number": item["roll_number"],
                            "Student Name": item["full_name"],
                            "Present": True,
                        }
                        for item in att_roster
                    ])
                    marked = st.data_editor(
                        roster_frame,
                        use_container_width=True,
                        hide_index=True,
                        disabled=["Student ID", "Roll Number", "Student Name"],
                        column_config={"Present": st.column_config.CheckboxColumn("Present", default=True)},
                        key=f"att_editor_{sel_att_slot['timetable_id']}_{date_text}",
                    )
                    submit_att = st.form_submit_button("Submit & Lock Session Attendance", type="primary", use_container_width=True)

                if submit_att:
                    records = {
                        int(row["Student ID"]): bool(row["Present"])
                        for _, row in marked.iterrows()
                    }
                    session_id = submit_session_attendance(
                        sel_att_slot["timetable_id"], faculty_id, date_text, records
                    )
                    if session_id:
                        st.success(f"Attendance recorded and locked for {len(records)} students. Session ID: #{session_id}")
                        st.rerun()
                    else:
                        st.error("Attendance submission failed or was already submitted.")

# =============================================================
# TAB 3: STUDENT SEARCH & SUMMARY
# =============================================================
with tab_search:
    st.subheader("🔍 Institutional Student Lookup & Academic Profile")
    st.caption("Search across the 500 registered first-year students across Sections A through J.")

    search_query = st.text_input("Enter Roll Number (e.g., 26STU0001) or Name", "").strip()

    if search_query:
        conn = get_connection()
        matched = conn.execute(
            """
            SELECT student_id, roll_number, full_name, department, section,
                   current_year, semester, cgpa, attendance_percentage,
                   internal_marks, external_marks
            FROM students
            WHERE roll_number LIKE ? OR full_name LIKE ?
            LIMIT 10
            """,
            (f"%{search_query}%", f"%{search_query}%")
        ).fetchall()
        conn.close()

        if not matched:
            st.warning("No students matched your search criteria.")
        else:
            for s in matched:
                s_dict = dict(s)
                with st.container(border=True):
                    sc1, sc2, sc3 = st.columns([2, 1, 1])
                    with sc1:
                        st.markdown(f"#### **{s_dict['full_name']}** (`{s_dict['roll_number']}`)")
                        st.write(f"**Department:** {s_dict['department']} · **Section:** Section {s_dict.get('section', 'N/A')}")
                        st.write(f"**Year/Sem:** Year {s_dict['current_year']}, Semester {s_dict['semester']}")
                    with sc2:
                        att_v = float(s_dict.get("attendance_percentage") or 0)
                        st.metric("Attendance", f"{att_v:.1f}%")
                        cgpa_v = float(s_dict.get("cgpa") or 0)
                        st.metric("CGPA", f"{cgpa_v:.2f}")
                    with sc3:
                        int_v = s_dict.get("internal_marks")
                        ext_v = s_dict.get("external_marks")
                        st.metric("CIE Internal", f"{int_v:.1f}/60" if int_v is not None else "Pending")
                        st.metric("External", f"{ext_v:.1f}/40" if ext_v is not None else "Pending")

                    # Course assessments for this student
                    stu_assess = get_student_course_assessments(s_dict["student_id"], s_dict["semester"])
                    if stu_assess:
                        with st.expander(f"View {s_dict['full_name']}'s Course Assessment Breakdown (8 Courses)", expanded=False):
                            st.dataframe(
                                pd.DataFrame([
                                    {
                                        "Course Code": a["course_code"],
                                        "Course Name": a["course_name"],
                                        "Mid /30": a.get("mid_exam_marks"),
                                        "Assn /10": a.get("assignment_marks"),
                                        "Quiz /10": a.get("quiz_marks"),
                                        "Viva /10": a.get("viva_marks"),
                                        "Internal /60": a.get("internal_total"),
                                        "External /40": a.get("external_marks"),
                                        "Total /100": a.get("overall_total"),
                                        "Attendance %": f"{a.get('course_attendance', 0):.1f}%",
                                    }
                                    for a in stu_assess
                                ]),
                                use_container_width=True,
                                hide_index=True,
                            )
    else:
        st.info("Enter a student's roll number or name above to view their academic records.")

# =============================================================
# TAB 4: AT-RISK STUDENT DETECTION
# =============================================================
with tab_risk:
    st.subheader("🚨 Early Warning & At-Risk Student Detection")
    st.markdown(
        """
        <div style="background: #fff8f6; border: 1px solid #fecaca; border-left: 4px solid #ef4444; border-radius: 6px; padding: 0.75rem; margin-bottom: 1rem; font-size: 0.85rem;">
            <b>Institutional Early Intervention Trigger:</b>  
            Students with <b>Attendance < 75%</b> OR <b>Average Internal Score < 24/60</b> OR <b>High Risk Classification</b>  
            require immediate academic intervention (advising session, remedial tutorials, and attendance recovery).
        </div>
        """,
        unsafe_allow_html=True,
    )

    conn = get_connection()
    risk_students = conn.execute(
        """
        SELECT student_id, roll_number, full_name, department, section,
               attendance_percentage, internal_marks, external_marks, cgpa
        FROM students
        WHERE attendance_percentage < 75.0 OR internal_marks < 24.0
        ORDER BY attendance_percentage ASC, internal_marks ASC
        """
    ).fetchall()
    conn.close()

    if not risk_students:
        st.success("🎉 No students in your assigned sections are currently flagged for critical academic risk.")
    else:
        st.metric("Total Students Flagged for Intervention", f"{len(risk_students)} Students")

        risk_rows = []
        for r in risk_students:
            r_dict = dict(r)
            att_val = float(r_dict.get("attendance_percentage") or 0)
            int_val = float(r_dict.get("internal_marks") or 0)
            
            triggers = []
            if att_val < 75.0:
                triggers.append(f"Shortage ({att_val:.1f}%)")
            if int_val < 24.0:
                triggers.append(f"Low CIE ({int_val:.1f}/60)")

            risk_rows.append({
                "Roll Number": r_dict["roll_number"],
                "Student Name": r_dict["full_name"],
                "Section": f"Section {r_dict['section']}",
                "Department": r_dict["department"],
                "Attendance": f"{att_val:.1f}%",
                "Internal /60": f"{int_val:.1f}",
                "CGPA": f"{float(r_dict.get('cgpa') or 0):.2f}",
                "Risk Triggers": ", ".join(triggers),
                "Recommended Action": "Schedule Remedial Tutorial & Parent Notice" if att_val < 70 else "Academic Counseling Session",
            })

        st.dataframe(pd.DataFrame(risk_rows), use_container_width=True, hide_index=True)

        st.markdown("#### 📢 Send Bulk Early Warning Notice")
        with st.form("bulk_warning_notice"):
            notice_title = st.text_input("Notice Subject", "Academic Advisory: Mandatory Attendance & Performance Meeting")
            notice_body = st.text_area(
                "Notice Message",
                "Your academic performance indicators and/or attendance percentage fall below institutional regulatory requirements. Please attend the remedial counseling session this Friday at 03:40 PM."
            )
            send_notice = st.form_submit_button("Send Notice to All Flagged Students")
            if send_notice:
                sent_count = 0
                for r in risk_students:
                    create_student_notification(r["student_id"], notice_title, notice_body)
                    sent_count += 1
                st.success(f"Early warning advisory successfully sent to {sent_count} students.")

# =============================================================
# TAB 5: SECTION ANALYTICS & TRENDS
# =============================================================
with tab_analytics:
    st.subheader("📊 Section Performance Analytics & Distribution")
    st.caption("Aggregated analytics across Section A through J assessments and attendance.")

    conn = get_connection()
    sec_stats = conn.execute(
        """
        SELECT section, COUNT(*) as student_count,
               AVG(attendance_percentage) as avg_attendance,
               AVG(internal_marks) as avg_internal,
               AVG(external_marks) as avg_external,
               AVG(cgpa) as avg_cgpa
        FROM students
        GROUP BY section
        ORDER BY section ASC
        """
    ).fetchall()
    conn.close()

    if sec_stats:
        sec_df = pd.DataFrame([dict(r) for r in sec_stats])
        
        st.markdown("##### Section-wise Academic Comparative Metrics")
        st.dataframe(
            pd.DataFrame([
                {
                    "Section": f"Section {r['section']}",
                    "Enrolled Strength": r["student_count"],
                    "Avg Attendance": f"{float(r['avg_attendance'] or 0):.1f}%",
                    "Avg CIE /60": f"{float(r['avg_internal'] or 0):.1f}",
                    "Avg External /40": f"{float(r['avg_external'] or 0):.1f}",
                    "Avg CGPA": f"{float(r['avg_cgpa'] or 0):.2f}",
                }
                for r in sec_stats
            ]),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("##### Average Internal Marks by Section (/60)")
        st.bar_chart(sec_df.set_index("section")["avg_internal"])

        st.markdown("##### Average Attendance by Section (%)")
        st.bar_chart(sec_df.set_index("section")["avg_attendance"])

# =============================================================
# TAB 6: REQUEST TEACHING ASSIGNMENT
# =============================================================
with tab_req:
    st.subheader("➕ Request Teaching Assignment")
    st.caption("Submit a request for an accredited course, section, and 50-minute weekday period for Admin approval.")

    teachable = get_teachable_course_options(dept)
    if not teachable:
        st.info("No published courses are available for assignment in your department.")
    else:
        c_opts = {
            f"{c['course_code']} · {c['course_name']} · Year {c['year']} Sem {c['semester']}": c
            for c in teachable
        }
        with st.form("fac_teaching_req_form"):
            c_label = st.selectbox("Course", list(c_opts.keys()))
            c_obj = c_opts[c_label]
            req_sec = st.selectbox("Section", list(SECTION_NAMES))
            req_day = st.selectbox("Weekday", list(ACADEMIC_DAYS))
            req_slot = st.selectbox(
                "Period",
                list(ACADEMIC_PERIODS),
                format_func=lambda v: f"{v} · {ACADEMIC_PERIODS[v][0]}–{ACADEMIC_PERIODS[v][1]}",
            )
            req_room = st.text_input("Preferred Room / Lab (optional)", "LH-101")
            submit_req = st.form_submit_button("Submit Request for Admin Approval", type="primary")

        if submit_req:
            r_id = request_faculty_teaching_assignment(
                faculty_id, c_obj["course_id"], req_sec, req_day, req_slot, req_room
            )
            if r_id:
                st.success(f"Teaching request submitted for Admin review. Request ID: #{r_id}")
            else:
                st.error("Request conflicts with an existing timetable slot or could not be saved.")
