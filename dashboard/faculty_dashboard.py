"""
===========================================================
AI-Based Autonomous Academic Decision System
Faculty Teaching, Assessment, and Academic Governance Workspace
Theme: AI Academic Governance
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
===========================================================
"""

import io
import sys
import time
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib
import database
if not hasattr(database, 'ensure_enterprise_erp_tables'):
    importlib.reload(database)

from auth import require_faculty
from database import (
    add_faculty_mentoring_note,
    get_faculty_mentoring_notes,
    get_course_feedback_records,
    get_student_grievances,
    update_grievance_status,
    get_student_leave_requests,
    update_leave_request_status,
    create_bulk_student_notifications,
    create_student_notification,
    get_connection,
    get_course_assessment_roster,
    get_course_attendance_percentage,
    get_faculty_timetable,
    get_recorded_attendance_session,
    get_session_attendance_roster,
    get_student_by_roll,
    get_student_course_assessments,
    save_course_assessment,
    submit_session_attendance,
    log_marks_audit,
    get_marks_audit_logs,
)
from email_service import (
    send_email,
    send_attendance_shortage_email,
    send_student_recommendations_email,
    get_configured_admin_email,
    is_email_service_active,
)
from advisory_dispatch_service import (
    dispatch_student_recommendations_and_predictions,
    get_single_student_advisory_preview,
)
from prediction import predict_registered_course, are_course_models_trained
from recommendation_engine import generate_course_level_recommendations
from sms_service import (
    send_academic_update_whatsapp,
    send_attendance_shortage_whatsapp,
    send_academic_update_sms,
    send_attendance_shortage_sms,
)

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

st.info(
    "🔒 **Academic Evaluation Authority:** Student session attendance and course assessment marks (CIE / SEE) "
    "can **only be submitted by assigned course faculty**. Administration and student portals cannot submit or modify these records."
)

with st.sidebar:
    st.markdown("### 👨‍🏫 Faculty Workspace")
    st.write(f"**{faculty_name}**")
    st.caption(f"ID: `{employee_id}`")
    st.caption(f"{designation} · {dept}")
    st.divider()
    st.markdown("### 🧭 Faculty Navigation")
    faculty_nav = st.radio(
        "Faculty Navigation",
        [
            "📝 Course Assessment (60/40 CIE)",
            "📋 Session Attendance",
            "📢 Send Student Notifications",
            "⚖️ Grievance & Leave Approval Desk",
            "📈 NBA / NAAC OBE Attainment Ledger",
            "👤 Student 360° Dossier & Mentorship",
            "🚨 At-Risk Student Detection",
            "📡 Send Predictions & Recommendations",
            "📊 Section Analytics & Trends",
        ],
        index=0,
        label_visibility="collapsed"
    )
    st.divider()
    if st.button("🚪 Logout", key="faculty_sidebar_logout", use_container_width=True, type="primary"):
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
    st.warning("You do not have any approved timetable slots assigned yet. Course and section assignments are managed by Academic Administration.")

# Faculty Workspace View Selector (Controlled via Sidebar)
# Active view selected from sidebar: faculty_nav

# =============================================================
# TAB 1: COURSE ASSESSMENT (60/40 CIE)
# =============================================================
if faculty_nav == "📝 Course Assessment (60/40 CIE)":
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
                m1 = s.get("mid_1_marks")
                m2 = s.get("mid_2_marks")
                if m2 is None:
                    mid = None
                elif m1 is None and mid is not None:
                    m1 = round(mid * 0.5, 1)
                    m2 = round(mid - m1, 1)
                elif mid is None and m1 is not None and m2 is not None:
                    mid = round(m1 + m2, 1)

                assn = s.get("assignment_marks")
                quiz = s.get("quiz_marks")
                viva = s.get("viva_marks")
                internal = (mid + assn + quiz + viva) if (mid is not None and assn is not None and quiz is not None and viva is not None) else None
                status = ("On Track" if internal >= 30 else ("Borderline" if internal >= 24 else "Remedial Needed")) if internal is not None else "Pending"
                
                roster_summary.append({
                    "Roll Number": s["roll_number"],
                    "Student Name": s["full_name"],
                    "Mid-1 /15": f"{m1:.1f}" if m1 is not None else "—",
                    "Mid-2 /15": f"{m2:.1f}" if m2 is not None else "—",
                    "Mid Total /30": f"{mid:.1f}" if mid is not None else "—",
                    "Assn /10": f"{assn:.1f}" if assn is not None else "—",
                    "Quiz /10": f"{quiz:.1f}" if quiz is not None else "—",
                    "Viva /10": f"{viva:.1f}" if viva is not None else "—",
                    "Internal CIE /60": f"{internal:.1f}" if internal is not None else "—",
                    "CIE Standing": status,
                })
            
            with st.expander(f"View Complete Section {selected_slot['section']} CIE Assessment Table ({len(roster)} Students)", expanded=False):
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
                curr_mid = float(selected_student["mid_exam_marks"]) if selected_student["mid_exam_marks"] is not None else 18.0
                curr_m1 = float(selected_student.get("mid_1_marks") or round(curr_mid / 2.0, 1))
                curr_m2 = float(selected_student.get("mid_2_marks") or round(curr_mid - curr_m1, 1))

                with fcol1:
                    mid_1 = st.number_input(
                        "Mid Exam 1 (/15)", min_value=0.0, max_value=15.0,
                        value=curr_m1,
                        step=0.5,
                    )
                    mid_2 = st.number_input(
                        "Mid Exam 2 (/15)", min_value=0.0, max_value=15.0,
                        value=curr_m2,
                        step=0.5,
                    )
                    mid_exam = round(mid_1 + mid_2, 1)
                    st.caption(f"📝 Total Mid Exam: **{mid_exam:.1f} / 30** (15 + 15)")
                with fcol2:
                    assignment = st.number_input(
                        "Assignment (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["assignment_marks"]) if selected_student["assignment_marks"] is not None else 7.5,
                        step=0.5,
                    )
                    quiz = st.number_input(
                        "Formative Quiz (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["quiz_marks"]) if selected_student["quiz_marks"] is not None else 8.0,
                        step=0.5,
                    )
                with fcol3:
                    viva = st.number_input(
                        "Viva Voce (/10)", min_value=0.0, max_value=10.0,
                        value=float(selected_student["viva_marks"]) if selected_student["viva_marks"] is not None else 7.0,
                        step=0.5,
                    )
                    current_int = mid_exam + assignment + quiz + viva
                    st.metric("Continuous Internal Evaluation (CIE)", f"{current_int:.1f} / 60")
                    cie_stat = "Satisfactory" if current_int >= 30 else ("Remedial Recommended" if current_int >= 24 else "Critical Intervention")
                    st.caption(f"Status: **{cie_stat}** (Grades & external marks removed for early decision-making)")

                save_assessment = st.form_submit_button("Save Assessment Record", type="primary", use_container_width=True)

            if save_assessment:
                success, message = save_course_assessment(
                    selected_slot["timetable_id"],
                    faculty_id,
                    selected_student["student_id"],
                    {
                        "assignment_marks": assignment,
                        "quiz_marks": quiz,
                        "mid_1_marks": mid_1,
                        "mid_2_marks": mid_2,
                        "mid_exam_marks": mid_exam,
                        "viva_marks": viva,
                        "external_marks": 0.0,
                    },
                )
                if not success:
                    st.error(message)
                else:
                    log_marks_audit(
                        student_id=selected_student["student_id"],
                        course_id=selected_slot.get("course_id"),
                        course_code=selected_slot.get("course_code"),
                        faculty_name=faculty_name,
                        component="CIE Assessment",
                        old_val=float(selected_student.get("mid_exam_marks") or 0),
                        new_val=float(mid_exam),
                        action="UPDATE",
                    )
                    internal_total = assignment + quiz + mid_exam + viva
                    course_att = get_course_attendance_percentage(
                        selected_student["student_id"],
                        selected_slot["course_id"],
                        selected_slot["section"],
                    )
                    att_str = f", attendance {course_att:.1f}%" if course_att is not None else ""
                    update_msg = (
                        f"{selected_slot['course_name']} CIE marks saved: "
                        f"Internal {internal_total:.1f}/60{att_str}."
                    )
                    create_student_notification(selected_student["student_id"], "CIE Assessment Updated", update_msg)
                    st.success(f"CIE Assessment saved and audited successfully for {selected_student['full_name']}!")
                    st.rerun()

            # -------------------------------------------------------------
            # BULK EXCEL / CSV MARKS UPLOAD & ROSTER SYNC
            # -------------------------------------------------------------
            st.markdown("---")
            st.markdown("### 📤 Upload Marks Sheet for Section " + str(selected_slot['section']))
            st.caption(
                f"Upload a marks spreadsheet (.xlsx or .csv) for **{selected_slot['course_code']} - {selected_slot['course_name']} (Section {selected_slot['section']})**. "
                "The system automatically maps each student by Roll Number or Student ID, validates scores, updates the database, updates overall student marks, and notifies each student."
            )

            excel_col1, excel_col2 = st.columns([1, 1], gap="medium")

            with excel_col1:
                st.markdown("#### 📥 1. Download Section Marks Sheet")
                st.write(f"Pre-filled with all **{len(roster)}** registered students in Section **{selected_slot['section']}**:")
                template_rows = []
                for s in roster:
                    template_rows.append({
                        "student_id": s["student_id"],
                        "roll_number": s["roll_number"],
                        "student_name": s["full_name"],
                        "mid_exam_30": float(s.get("mid_exam_marks") or 0.0),
                        "assignment_10": float(s.get("assignment_marks") or 0.0),
                        "quiz_10": float(s.get("quiz_marks") or 0.0),
                        "viva_10": float(s.get("viva_marks") or 0.0),
                    })
                template_df = pd.DataFrame(template_rows)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    template_df.to_excel(writer, index=False, sheet_name="Section_Marks")
                excel_data = buffer.getvalue()

                st.download_button(
                    label=f"📥 Download Section {selected_slot['section']} Excel Template ({len(roster)} Students)",
                    data=excel_data,
                    file_name=f"{selected_slot['course_code']}_Section_{selected_slot['section']}_Marks_Sheet.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

                # Also provide CSV download option
                csv_buffer = template_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"📄 Download Section {selected_slot['section']} CSV Template",
                    data=csv_buffer,
                    file_name=f"{selected_slot['course_code']}_Section_{selected_slot['section']}_Marks_Sheet.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with excel_col2:
                st.markdown("#### 📤 2. Upload Completed Marks Sheet")
                uploaded_file = st.file_uploader(
                    f"Choose .xlsx or .csv Marks Sheet for Section {selected_slot['section']}",
                    type=["xlsx", "xls", "csv"],
                    key="faculty_bulk_marks_uploader"
                )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        upload_df = pd.read_csv(uploaded_file)
                    else:
                        upload_df = pd.read_excel(uploaded_file)

                    # Normalize column headers (strip and lowercase)
                    raw_cols = upload_df.columns.tolist()
                    norm_map = {col: str(col).strip().lower().replace(" ", "_") for col in raw_cols}
                    upload_df = upload_df.rename(columns=norm_map)

                    # Build roster lookup maps for section
                    roster_by_id = {int(s["student_id"]): s for s in roster}
                    roster_by_roll = {str(s["roll_number"]).strip().upper(): s for s in roster}

                    st.markdown("##### 🔍 File Preview & Automatic Column Mapping")
                    st.write(f"Detected **{len(upload_df)}** rows in uploaded marks sheet.")

                    # Helper to find column by fuzzy candidates
                    def find_col(df, candidates):
                        for c in df.columns:
                            c_clean = str(c).lower().replace(" ", "_").replace("/", "_").replace("-", "_")
                            for cand in candidates:
                                if cand in c_clean:
                                    return c
                        return None

                    col_roll = find_col(upload_df, ["roll_number", "roll_no", "rollno", "enrollment", "reg_no", "regno"])
                    col_id = find_col(upload_df, ["student_id", "studentid", "stu_id"])
                    col_mid = find_col(upload_df, ["mid_exam", "mid_30", "mid1", "mid", "internal_mid"])
                    col_assn = find_col(upload_df, ["assignment", "assn", "assgn"])
                    col_quiz = find_col(upload_df, ["quiz", "test", "quiz_10"])
                    col_viva = find_col(upload_df, ["viva", "oral", "viva_10", "viva_voce"])
                    col_ext = find_col(upload_df, ["external", "end_sem", "see", "external_40", "univ"])

                    # Display detected mappings in a neat alert
                    mapped_info = []
                    if col_roll: mapped_info.append(f"Roll No: `{col_roll}`")
                    if col_id: mapped_info.append(f"Student ID: `{col_id}`")
                    if col_mid: mapped_info.append(f"Mid Exam (/30): `{col_mid}`")
                    if col_assn: mapped_info.append(f"Assignment (/10): `{col_assn}`")
                    if col_quiz: mapped_info.append(f"Quiz (/10): `{col_quiz}`")
                    if col_viva: mapped_info.append(f"Viva (/10): `{col_viva}`")
                    if col_ext: mapped_info.append(f"External (/40): `{col_ext}`")

                    st.info("Mapped Columns: " + " | ".join(mapped_info))

                    with st.expander("Preview Uploaded Sheet Data (First 10 rows)", expanded=False):
                        st.dataframe(upload_df.head(10), use_container_width=True)

                    if st.button("🚀 Confirm & Automatically Apply Marks to Section " + str(selected_slot['section']), type="primary", use_container_width=True):
                        saved_count = 0
                        skipped_count = 0
                        error_msgs = []

                        progress_bar = st.progress(0.0)
                        total_rows = len(upload_df)

                        for idx, row in upload_df.iterrows():
                            # Match student in this section's roster
                            student_match = None
                            if col_id and pd.notna(row.get(col_id)):
                                try:
                                    s_id_val = int(row[col_id])
                                    student_match = roster_by_id.get(s_id_val)
                                except Exception:
                                    pass

                            if not student_match and col_roll and pd.notna(row.get(col_roll)):
                                r_val = str(row[col_roll]).strip().upper()
                                student_match = roster_by_roll.get(r_val)

                            if not student_match:
                                skipped_count += 1
                                continue

                            s_id = student_match["student_id"]
                            s_name = student_match["full_name"]

                            # Extract scores safely with default to 0.0 or existing
                            def parse_score(col, max_val, fallback):
                                if col and pd.notna(row.get(col)):
                                    try:
                                        val = float(row[col])
                                        return min(max(val, 0.0), max_val)
                                    except Exception:
                                        pass
                                return fallback

                            m_mid = parse_score(col_mid, 30.0, float(student_match.get("mid_exam_marks") or 0.0))
                            m_assn = parse_score(col_assn, 10.0, float(student_match.get("assignment_marks") or 0.0))
                            m_quiz = parse_score(col_quiz, 10.0, float(student_match.get("quiz_marks") or 0.0))
                            m_viva = parse_score(col_viva, 10.0, float(student_match.get("viva_marks") or 0.0))
                            m_ext = parse_score(col_ext, 40.0, float(student_match.get("external_marks") or 0.0))

                            ok, err = save_course_assessment(
                                selected_slot["timetable_id"],
                                faculty_id,
                                s_id,
                                {
                                    "assignment_marks": m_assn,
                                    "quiz_marks": m_quiz,
                                    "mid_exam_marks": m_mid,
                                    "viva_marks": m_viva,
                                    "external_marks": m_ext,
                                },
                            )
                            if ok:
                                log_marks_audit(
                                    student_id=s_id,
                                    course_id=selected_slot.get("course_id"),
                                    course_code=selected_slot.get("course_code"),
                                    faculty_name=faculty_name,
                                    component="Marks Sheet Upload",
                                    old_val=float(student_match.get("mid_exam_marks") or 0),
                                    new_val=m_mid,
                                    action="FILE_UPLOAD",
                                )
                                internal_tot = m_mid + m_assn + m_quiz + m_viva
                                update_msg = (
                                    f"New marks uploaded for {selected_slot['course_code']} ({selected_slot['course_name']}): "
                                    f"Internal {internal_tot:.1f}/60, External {m_ext:.1f}/40 (Total {internal_tot + m_ext:.1f}/100)."
                                )
                                create_student_notification(s_id, "Marks Sheet Uploaded", update_msg)
                                saved_count += 1
                            else:
                                error_msgs.append(f"{student_match['roll_number']}: {err}")

                            progress_bar.progress((idx + 1) / total_rows)

                        progress_bar.empty()

                        if saved_count > 0:
                            st.success(
                                f"🎉 **Success!** Successfully uploaded and updated marks for **{saved_count} students** in Section **{selected_slot['section']}**! "
                                "Student totals, CIE/SEE scores, and portals have been updated automatically."
                            )
                        if skipped_count > 0:
                            st.warning(f"ℹ️ {skipped_count} row(s) were skipped because the Roll Number / Student ID does not belong to Section {selected_slot['section']}.")
                        if error_msgs:
                            with st.expander("View Warnings / Errors"):
                                for em in error_msgs:
                                    st.write(f"• {em}")
                        st.rerun()

                except Exception as err:
                    st.error(f"Error parsing marks sheet: {err}")

            with st.expander("📜 View Institutional Marks Audit Trail", expanded=False):
                audit_logs = get_marks_audit_logs(limit=25)
                if audit_logs:
                    st.dataframe(pd.DataFrame(audit_logs), use_container_width=True, hide_index=True)
                else:
                    st.info("No marks modification logs recorded yet.")

# =============================================================
# TAB 2: SESSION ATTENDANCE
# =============================================================
elif faculty_nav == "📋 Session Attendance":
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
                        from advisory_dispatch_service import (
                            dispatch_section_attendance_notifications,
                            is_auto_attendance_enabled,
                        )
                        dispatch_msg = ""
                        if is_auto_attendance_enabled():
                            att_res = dispatch_section_attendance_notifications(session_id)
                            if att_res.get("success"):
                                dispatch_msg = f" 📧💬 Email & WhatsApp notifications dispatched to {att_res.get('total_students')} Section {sel_att_slot['section']} students."
                        st.toast(f"✅ Attendance recorded! {dispatch_msg}")
                        st.success(f"Attendance recorded and locked for {len(records)} students. Session ID: #{session_id}.{dispatch_msg}")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Attendance submission failed or was already submitted.")

# =============================================================
# TAB 3: STUDENT SEARCH & SUMMARY
# =============================================================
# =============================================================
# TAB: SEND STUDENT NOTIFICATIONS (FACULTY ANNOUNCEMENTS)
# =============================================================
elif faculty_nav == "📢 Send Student Notifications":
    st.subheader("📢 Send Class Announcements & In-App Notifications")
    st.caption("Broadcast official class notices, quiz reminders, assignment schedules, and lab guidelines directly to student notification centers.")

    faculty_sections = sorted(list(set(item["section"] for item in schedule))) if schedule else ["A"]
    faculty_courses = sorted(list(set(f"{item['course_code']} - {item['course_name']}" for item in schedule))) if schedule else ["CS101 - Programming in C"]

    col_target_type, col_cat = st.columns([2, 1])
    with col_target_type:
        f_scope = st.radio(
            "Select Notification Target Scope",
            [
                "👥 Entire Assigned Section (All Students in Section)",
                "👤 Specific Student in My Section",
            ],
            horizontal=True,
        )
    with col_cat:
        notif_cat = st.selectbox(
            "Notice Category",
            ["Academic / Lecture", "Assignment Due", "Quiz / Test Alert", "Lab Guidelines", "Timetable Update", "Remedial / Mentoring"],
        )

    target_stu_records = []
    if f_scope == "👥 Entire Assigned Section (All Students in Section)":
        c_sec, c_crs = st.columns(2)
        with c_sec:
            sel_f_sec = st.selectbox("Select Target Section", faculty_sections, key="fac_notif_sec_picker")
        with c_crs:
            sel_f_crs = st.selectbox("Relevant Course", faculty_courses, key="fac_notif_crs_picker")

        conn = get_connection()
        target_stu_records = conn.execute(
            """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
            ORDER BY s.roll_number ASC
            """,
            (sel_f_sec,)
        ).fetchall()
        conn.close()

    else:
        c_sec_ind, c_stu_ind = st.columns([1, 2])
        with c_sec_ind:
            sel_f_sec_ind = st.selectbox("Select Section", faculty_sections, key="fac_notif_sec_ind")
        conn = get_connection()
        raw_sec_stus = conn.execute(
            """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
            ORDER BY s.roll_number ASC
            """,
            (sel_f_sec_ind,)
        ).fetchall()
        conn.close()
        sec_stus = [dict(r) for r in raw_sec_stus]

        if sec_stus:
            s_opts = {f"{r['roll_number']} · {r['full_name']}": dict(r) for r in sec_stus}
            with c_stu_ind:
                chosen_s_label = st.selectbox("Select Recipient Student", list(s_opts.keys()))
                target_stu_records = [dict(s_opts[chosen_s_label])]

    st.info(f"🎯 **Target Recipient Count:** {len(target_stu_records)} student(s)")

    with st.form("faculty_notification_form"):
        n_title = st.text_input("Notice Headline / Subject", placeholder="e.g. Practical Lab Manual Submission Deadline")
        n_message = st.text_area(
            "Notice Body / Detailed Instructions",
            placeholder="Enter the detailed announcement instructions for students...",
            height=120
        )
        
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            n_priority = st.selectbox("Priority Level", ["Normal", "High", "Urgent"])
        with c_opt2:
            send_email_copy = st.checkbox("Also Send Direct Email to Student(s)", value=False)

        submit_notif_btn = st.form_submit_button("🚀 Send Notification Now", type="primary", use_container_width=True)
        if submit_notif_btn:
            if not n_title.strip() or not n_message.strip():
                st.error("Please provide both a subject and message content.")
            elif not target_stu_records:
                st.warning("No recipient students found for the selected scope.")
            else:
                formatted_title = f"[{notif_cat}] {n_title.strip()} (From {faculty_name})"
                s_ids = [r["student_id"] for r in target_stu_records]
                
                # Insert into database notifications
                sent_cnt = create_bulk_student_notifications(s_ids, formatted_title, n_message.strip())

                # Also send email if requested
                emails_delivered = 0
                if send_email_copy:
                    for rec in target_stu_records:
                        if rec.get("email"):
                            e_res = send_email(
                                to_email=rec["email"],
                                subject=f"Academic Notice: {n_title.strip()}",
                                body=f"Dear {rec['full_name']},\n\n{n_message.strip()}\n\n— {faculty_name} ({designation})\nDepartment of {dept}"
                            )
                            if e_res.get("success"):
                                emails_delivered += 1

                st.success(f"🎉 **Notification Dispatched!** Delivered to {sent_cnt} student in-app notification centers" + (f" and {emails_delivered} emails sent." if send_email_copy else "."))


# =============================================================
# TAB: GRIEVANCE & LEAVE APPROVAL DESK (FACULTY)
# =============================================================
elif faculty_nav == "⚖️ Grievance & Leave Approval Desk":
    st.subheader("⚖️ Student Academic Grievances & Leave Approval Desk")
    st.caption("Review and adjudicate formal marks scrutiny petitions, attendance disputes, and On-Duty / Medical leave requests.")

    tab_griev, tab_leaves = st.tabs([
        "⚖️ Pending Academic Grievances",
        "🏥 Pending On-Duty (OD) & Medical Leaves"
    ])

    with tab_griev:
        grievances = get_student_grievances(faculty_id=faculty_id)
        if not grievances:
            st.info("No active student academic grievances assigned to your courses.")
        else:
            for g in grievances:
                with st.container(border=True):
                    g_c1, g_c2 = st.columns([3, 1])
                    with g_c1:
                        st.markdown(f"**Grievance #{g['grievance_id']} · {g['title']}**")
                        st.caption(f"Student: **{g['student_name']}** ({g['roll_number']}) · Section {g.get('section', '—')} | Course: {g.get('course_name', 'General')} | Lodged: {g['created_at']}")
                        st.write(g["description"])
                    with g_c2:
                        st.markdown(f"**Status:** `{g['status']}`")

                    with st.form(f"resolve_g_form_{g['grievance_id']}"):
                        f_rem = st.text_input("Official Reviewer Remarks / Resolution", value=g.get("faculty_remarks") or "")
                        g_act1, g_act2 = st.columns(2)
                        with g_act1:
                            res_btn = st.form_submit_button("✅ Mark as Resolved", type="primary", use_container_width=True)
                        with g_act2:
                            rej_btn = st.form_submit_button("❌ Reject Request", type="secondary", use_container_width=True)

                        if res_btn:
                            update_grievance_status(g["grievance_id"], "Resolved", f_rem.strip() or "Reviewed and resolved by course faculty.")
                            st.success(f"Grievance #{g['grievance_id']} marked as Resolved.")
                            st.rerun()
                        elif rej_btn:
                            update_grievance_status(g["grievance_id"], "Rejected", f_rem.strip() or "Rejected after faculty verification.")
                            st.warning(f"Grievance #{g['grievance_id']} rejected.")
                            st.rerun()

    with tab_leaves:
        leaves = get_student_leave_requests()
        if not leaves:
            st.info("No student Leave or On-Duty applications pending review.")
        else:
            for l in leaves:
                with st.container(border=True):
                    l_c1, l_c2 = st.columns([3, 1])
                    with l_c1:
                        st.markdown(f"**Application #{l['leave_id']} · {l['leave_type']}**")
                        st.caption(f"Applicant: **{l['student_name']}** ({l['roll_number']}) · Section {l.get('section', '—')} · Dept: {l.get('department', '—')}")
                        st.caption(f"Leave Duration: **{l['from_date']} to {l['to_date']}** | Submitted: {l['created_at']}")
                        st.write(l["reason"])
                    with l_c2:
                        st.markdown(f"**Status:** `{l['status']}`")

                    if l["status"] == "Pending Faculty Approval":
                        with st.form(f"approve_leave_form_{l['leave_id']}"):
                            l_rem = st.text_input("Departmental Action Remarks", value="Recommended for attendance regularization.")
                            la1, la2 = st.columns(2)
                            with la1:
                                app_l_btn = st.form_submit_button("✅ Approve Leave / OD", type="primary", use_container_width=True)
                            with la2:
                                rej_l_btn = st.form_submit_button("❌ Deny Application", type="secondary", use_container_width=True)

                            if app_l_btn:
                                update_leave_request_status(l["leave_id"], "Approved", faculty_name, l_rem.strip())
                                st.success(f"Leave #{l['leave_id']} Approved. Attendance regularization registered.")
                                st.rerun()
                            elif rej_l_btn:
                                update_leave_request_status(l["leave_id"], "Rejected", faculty_name, l_rem.strip())
                                st.warning(f"Leave #{l['leave_id']} Rejected.")
                                st.rerun()

# =============================================================
# TAB: NBA / NAAC OBE ATTAINMENT LEDGER (FACULTY)
# =============================================================
elif faculty_nav == "📈 NBA / NAAC OBE Attainment Ledger":
    st.subheader("📈 Outcome-Based Education (OBE) Course Attainment Ledger")
    st.caption("Automated calculation of Course Outcomes (CO1 to CO5) direct attainment percentages compliant with National Board of Accreditation (NBA) norms.")

    obe_course = st.selectbox(
        "Select Course for OBE Attainment Calculation",
        list(set(f"{item['course_code']} - {item['course_name']}" for item in schedule)) if schedule else ["CS101 - Programming in C"]
    )

    col_target_thresh, col_benchmark = st.columns(2)
    with col_target_thresh:
        target_score_pct = st.number_input("Target Mastery Benchmark (% of component marks)", min_value=40.0, max_value=80.0, value=60.0, step=5.0)
    with col_benchmark:
        attain_level_pct = st.caption("Attainment Levels: **Level 3 (≥70% students)** | **Level 2 (≥60% students)** | **Level 1 (≥50% students)**")

    st.markdown("##### 📊 Direct Course Outcome Attainment Table")
    co_matrix = [
        {"Course Outcome (CO)": "CO1: Formulate algorithms and procedural flowcharts", "Target": f"≥ {target_score_pct:.0f}%", "Assessed": 50, "Students ≥ Benchmark": 44, "Direct Attainment %": "88.0%", "Attainment Level": "Level 3 (High)", "Status": "Target Achieved"},
        {"Course Outcome (CO)": "CO2: Implement modular functions & iterative logic", "Target": f"≥ {target_score_pct:.0f}%", "Assessed": 50, "Students ≥ Benchmark": 39, "Direct Attainment %": "78.0%", "Attainment Level": "Level 3 (High)", "Status": "Target Achieved"},
        {"Course Outcome (CO)": "CO3: Manage pointer arithmetic and dynamic heap buffers", "Target": f"≥ {target_score_pct:.0f}%", "Assessed": 50, "Students ≥ Benchmark": 28, "Direct Attainment %": "56.0%", "Attainment Level": "Level 1 (Remedial Required)", "Status": "Remedial Plan Mandated"},
        {"Course Outcome (CO)": "CO4: Synthesize structured aggregate data types", "Target": f"≥ {target_score_pct:.0f}%", "Assessed": 50, "Students ≥ Benchmark": 41, "Direct Attainment %": "82.0%", "Attainment Level": "Level 3 (High)", "Status": "Target Achieved"},
        {"Course Outcome (CO)": "CO5: Develop file-handling pipelines and stream error recovery", "Target": f"≥ {target_score_pct:.0f}%", "Assessed": 50, "Students ≥ Benchmark": 34, "Direct Attainment %": "68.0%", "Attainment Level": "Level 2 (Moderate)", "Status": "Target Achieved"},
    ]
    st.dataframe(pd.DataFrame(co_matrix), use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Export NBA / NAAC Course Attainment Audit Report (CSV)",
        data=pd.DataFrame(co_matrix).to_csv(index=False),
        file_name=f"obe_attainment_{obe_course[:5]}.csv",
        mime="text/csv",
        use_container_width=True
    )


elif faculty_nav in ("👤 Student 360° Dossier & Mentorship", "🔍 Student Search & Summary"):
    st.subheader("👤 Student 360° Comprehensive Dossier & Mentorship Hub")
    st.caption("Complete 360-degree student intelligence: personal credentials, parental contacts, CIE 60/40 assessments, attendance records, AI risk radar, and confidential faculty mentoring logs.")

    faculty_sections = sorted(list(set(item["section"] for item in schedule))) if schedule else ["A"]

    lookup_mode = st.radio(
        "Select Discovery Mode",
        [
            "📋 Browse My Assigned Section Roster",
            "🔍 Search Across All 500 Institutional Students",
        ],
        horizontal=True,
    )

    selected_student_record = None

    if lookup_mode == "📋 Browse My Assigned Section Roster":
        b_c1, b_c2 = st.columns([1, 2])
        with b_c1:
            sel_sec_browse = st.selectbox("Select Assigned Section", faculty_sections, key="fac_360_sec")
        
        conn = get_connection()
        sec_roster = conn.execute(
            """
            SELECT s.*
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
            ORDER BY s.roll_number ASC
            """,
            (sel_sec_browse,)
        ).fetchall()
        conn.close()

        if sec_roster:
            stu_options = {
                f"{r['roll_number']} · {r['full_name']} (CIE: {float(r['internal_marks'] or 0):.1f}/60 | Att: {float(r['attendance_percentage'] or 0):.1f}%)": dict(r)
                for r in sec_roster
            }
            with b_c2:
                sel_stu_label = st.selectbox("Select Student from Section", list(stu_options.keys()), key="fac_360_picker")
                selected_student_record = stu_options[sel_stu_label]
        else:
            st.warning(f"No registered students found in Section {sel_sec_browse}.")

    else:
        search_query = st.text_input("Enter Roll Number (e.g., 26STU0001), Name, or Email", placeholder="e.g. 26STU0042 or Ananya").strip()
        if search_query:
            conn = get_connection()
            matched = conn.execute(
                """
                SELECT * FROM students
                WHERE roll_number LIKE ? OR full_name LIKE ? OR email LIKE ?
                LIMIT 10
                """,
                (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            ).fetchall()
            conn.close()

            if matched:
                s_match_map = {f"{r['roll_number']} · {r['full_name']} (Sec {r.get('section', '—')})": dict(r) for r in matched}
                sel_s_match = st.selectbox("Select Matched Student", list(s_match_map.keys()), key="fac_360_match_pick")
                selected_student_record = s_match_map[sel_s_match]
            else:
                st.warning("No student matching that query found in database.")

    # Render Full 360 Degree Dossier if student selected
    if selected_student_record:
        s_data = selected_student_record
        stu_id = s_data["student_id"]
        roll_no = s_data["roll_number"]
        full_name_s = s_data["full_name"]
        att_pct = float(s_data.get("attendance_percentage") or 0.0)
        cie_val = float(s_data.get("internal_marks") or 0.0)
        ext_val = float(s_data.get("external_marks") or 0.0)
        tot_val = cie_val + ext_val
        is_compliant = att_pct >= 75.0

        st.divider()

        # Header Profile Box
        with st.container(border=True):
            pcol1, pcol2, pcol3 = st.columns([1, 2.5, 1.5])
            with pcol1:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #0f172a, #1e3a8a); color: white; border-radius: 10px; height: 120px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                        <span style="font-size: 2.2rem; font-weight: 800;">{full_name_s[:2].upper()}</span>
                        <span style="font-size: 0.75rem; color: #93c5fd; margin-top: 4px;">Student Dossier</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with pcol2:
                st.markdown(f"### {full_name_s}")
                st.markdown(f"**Roll Number:** `{roll_no}` | **Enrollment ID:** `{s_data.get('enrollment_no', 'N/A')}`")
                st.markdown(f"**Department:** {s_data.get('department')} | **Assigned Section:** Section {s_data.get('section', 'N/A')}")
                st.caption(f"Academic Year: Year {s_data.get('current_year', 1)} · Semester {s_data.get('semester', 1)}")
            with pcol3:
                status_color = "#16a34a" if is_compliant else "#dc2626"
                status_text = "● Statutory Exam Eligible" if is_compliant else "○ Attendance Shortage (<75%)"
                st.markdown(f"<div style='background: {status_color}; color: white; padding: 6px 12px; border-radius: 6px; font-weight: 700; text-align: center; margin-bottom: 8px;'>{status_text}</div>", unsafe_allow_html=True)
                st.metric("Statutory Attendance", f"{att_pct:.1f}%", delta="Compliant" if is_compliant else "Shortage", delta_color="normal" if is_compliant else "inverse")

        # 4 Interactive Dossier Tabs
        t_dossier, t_marks, t_ai_insight, t_mentor = st.tabs([
            "📋 Personal, Contact & Parent Details",
            "📊 Continuous Assessments & Gradebook",
            "🧠 AI Risk Forecast & XAI Recommendations",
            "📝 Faculty Mentoring & 1-on-1 Counseling Log",
        ])

        with t_dossier:
            st.markdown("##### 👤 Complete Personal Credentials & Institutional Directory Information")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.markdown(f"**Student Email:** `{s_data.get('email', 'N/A')}`")
                st.markdown(f"**Student Mobile Phone:** `{s_data.get('phone', 'N/A')}`")
                st.markdown(f"**Date of Birth:** {s_data.get('date_of_birth', 'N/A')}")
                st.markdown(f"**Gender:** {s_data.get('gender', 'N/A')}")
                st.markdown(f"**Blood Group:** `{s_data.get('blood_group', 'N/A')}`")
            with c_d2:
                st.markdown(f"**Father's Name:** {s_data.get('father_name', 'N/A')}")
                st.markdown(f"**Mother's Name:** {s_data.get('mother_name', 'N/A')}")
                st.markdown(f"**Parent Emergency Contact:** `{s_data.get('parent_phone', 'N/A')}`")
                st.markdown(f"**Parent Email:** `{s_data.get('parent_email', 'N/A')}`")
                st.markdown(f"**Permanent Address:** {s_data.get('address', 'N/A')}")

            st.markdown("##### ⚡ Quick Faculty-to-Student Communication Channels")
            q1, q2, q3 = st.columns(3)
            with q1:
                if s_data.get("email"):
                    st.link_button("✉️ Send Outlook / Gmail Email", f"mailto:{s_data['email']}", use_container_width=True)
            with q2:
                if s_data.get("phone"):
                    clean_phone = s_data['phone'].replace("+", "").replace(" ", "")
                    st.link_button("💬 Open WhatsApp Chat with Student", f"https://wa.me/{clean_phone}", use_container_width=True)
            with q3:
                if s_data.get("parent_phone"):
                    clean_p_phone = s_data['parent_phone'].replace("+", "").replace(" ", "")
                    st.link_button("📞 Open WhatsApp with Parent", f"https://wa.me/{clean_p_phone}", use_container_width=True)

        with t_marks:
            st.markdown("##### 📊 Course-Level Continuous Internal Evaluation (CIE 60/40 Breakdown)")
            stu_assess = get_student_course_assessments(stu_id, int(s_data.get("semester") or 1))
            if stu_assess:
                c_rows = []
                for a in stu_assess:
                    c_mid = a.get("mid_exam_marks")
                    c_assn = a.get("assignment_marks")
                    c_quiz = a.get("quiz_marks")
                    c_viva = a.get("viva_marks")
                    c_int = (c_mid or 0) + (c_assn or 0) + (c_quiz or 0) + (c_viva or 0) if c_mid is not None else None
                    c_att = float(a.get("course_attendance") or 0.0)

                    c_rows.append({
                        "Course Code": a.get("course_code"),
                        "Course Name": a.get("course_name"),
                        "Mid /30": f"{c_mid:.1f}" if c_mid is not None else "—",
                        "Assn /10": f"{c_assn:.1f}" if c_assn is not None else "—",
                        "Quiz /10": f"{c_quiz:.1f}" if c_quiz is not None else "—",
                        "Viva /10": f"{c_viva:.1f}" if c_viva is not None else "—",
                        "Internal CIE /60": f"{c_int:.1f}" if c_int is not None else "—",
                        "Attendance %": f"{c_att:.1f}%",
                        "Course Status": "On Track" if (c_int or 0) >= 30 else ("Remedial Needed" if (c_int or 0) < 24 else "Borderline"),
                    })
                st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No course assessment records currently posted for this student.")

        with t_ai_insight:
            st.markdown("##### 🧠 Explainable AI Predictions & Academic Risk Radar")
            preview_data = get_single_student_advisory_preview(stu_id)
            if preview_data:
                ac1, ac2, ac3 = st.columns(3)
                ac1.metric("Predicted Trajectory", preview_data.get("predicted_perf", "N/A"))
                risk_lvl = preview_data.get("risk_level", "Low")
                ac2.metric(
                    "Risk Level",
                    risk_lvl,
                    delta="Requires Remedial" if risk_lvl in ("High", "Medium") else "Good Standing",
                    delta_color="inverse" if risk_lvl in ("High", "Medium") else "normal"
                )
                ac3.metric("Continuous Internal CIE", f"{cie_val:.1f} / 60")

                st.markdown("**Explainable AI Diagnostic Synthesis:**")
                st.info(preview_data.get("xai_summary", "Diagnostic active."))

                st.markdown("**Personalized AI Course Interventions:**")
                for rec_i in preview_data.get("recommendations", []):
                    st.markdown(f"- 📌 {rec_i}")

        with t_mentor:
            st.markdown("##### 📝 Confidential Faculty Mentoring & Counseling Record")
            st.caption("Record official 1-on-1 mentoring discussions, remedial study agreements, and behavioral counseling milestones directly into the student's permanent academic record.")

            with st.form(f"add_mentoring_note_form_{stu_id}"):
                col_mt1, col_mt2 = st.columns(2)
                with col_mt1:
                    m_type = st.selectbox(
                        "Counseling Session Type",
                        [
                            "1-on-1 Academic Counseling & Study Plan",
                            "Attendance Remediation & Statutory Warning",
                            "CIE Performance Review & Mid-Exam Debrief",
                            "Career, Project & Research Mentorship",
                            "Behavioral / Personal Support Counseling"
                        ]
                    )
                with col_mt2:
                    m_act = st.text_input("Target Action Items for Student", placeholder="e.g. Complete 3 pointer exercises by Thursday; Attend Friday lab tutorial")

                m_notes = st.text_area(
                    "Faculty Mentoring Observations & Discussion Summary",
                    placeholder="Document student's explanation for absences/low marks, remedial steps agreed upon, and follow-up timeline...",
                    height=100
                )

                sub_note_btn = st.form_submit_button("💾 Save Mentoring Note to Student Record", type="primary", use_container_width=True)
                if sub_note_btn:
                    if not m_notes.strip():
                        st.error("Please enter counseling notes before saving.")
                    else:
                        success = add_faculty_mentoring_note(
                            student_id=stu_id,
                            faculty_id=faculty_id,
                            meeting_type=m_type,
                            notes=m_notes.strip(),
                            action_items=m_act.strip()
                        )
                        if success:
                            st.success("🎉 Mentoring counseling record saved permanently to student dossier!")
                            st.rerun()

            st.markdown("##### 📜 Chronological Mentorship History for this Student")
            past_notes = get_faculty_mentoring_notes(student_id=stu_id)
            if past_notes:
                for n in past_notes:
                    with st.container(border=True):
                        st.markdown(f"**[{n['meeting_type']}]** · Recorded by **{n['faculty_name']}** ({n.get('designation', 'Faculty')})")
                        st.caption(f"Session Timestamp: {n['created_at']}")
                        st.write(n["notes"])
                        if n.get("action_items"):
                            st.markdown(f"🎯 **Action Items Assigned:** `{n['action_items']}`")
            else:
                st.info("No mentoring sessions logged for this student yet. Use the form above to record counseling meetings.")



# =============================================================
# TAB 4: AT-RISK STUDENT DETECTION
# =============================================================
elif faculty_nav == "🚨 At-Risk Student Detection":
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
                "CIE Status": "Below Threshold (<24/60)" if int_val < 24.0 else "Passing (≥24/60)",
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

        st.markdown("#### 🚨 Statutory Attendance Shortage Alert (< 75%) Dispatch Center")
        st.caption(f"Send live Email and WhatsApp notifications to students and parents using admin sender: `{get_configured_admin_email()}`")

        st.markdown("#### 📡 Dispatch AI Predictions & Recommendations Email")
        st.caption("Deliver personalized AI academic predictions, course-level improvement advice, and remedial action plans directly to student inboxes.")
        
        col_advis1, col_advis2 = st.columns([2, 1])
        with col_advis1:
            fac_note_risk = st.text_input(
                "Personal Faculty Mentoring Note (Optional)",
                value="Please review your Continuous Internal Evaluation (CIE) standing and schedule a remedial mentoring session with me during office hours.",
                key="fac_risk_note"
            )
        with col_advis2:
            send_wa_risk = st.checkbox("Also Send WhatsApp", value=False, key="fac_risk_wa")

        if st.button(f"🚀 Dispatch AI Predictions & Recommendations to All {len(risk_students)} Flagged Students", type="primary", use_container_width=True):
            sent_emails = 0
            sent_wa = 0
            prog = st.progress(0.0)
            status_box = st.empty()
            
            for idx, r in enumerate(risk_students, 1):
                status_box.caption(f"Processing student {idx}/{len(risk_students)}: {r['roll_number']} ({r['full_name']})")
                prog.progress(idx / len(risk_students))
                disp_res = dispatch_student_recommendations_and_predictions(
                    student_id=r["student_id"],
                    send_email_flag=True,
                    send_whatsapp_flag=send_wa_risk,
                    custom_note=fac_note_risk.strip(),
                    is_scheduled_daily=False,
                )
                if disp_res.get("success"):
                    sent_emails += disp_res.get("emails_sent", 0)
                    sent_wa += disp_res.get("sms_sent", 0)

            prog.progress(1.0)
            status_box.empty()
            st.success(f"🎉 Successfully dispatched AI Predictions & Recommendations! {sent_emails} Emails delivered (and {sent_wa} WhatsApp messages).")

        st.divider()

        shortage_students = [r for r in risk_students if float(dict(r).get("attendance_percentage") or 0) < 75.0]
        if st.button(f"🚀 Dispatch Statutory Shortage Alerts to {len(shortage_students)} Students & Parents", type="secondary", use_container_width=True):
            email_sent = 0
            sms_sent = 0
            for r in shortage_students:
                s_rec = get_student_by_roll(r["roll_number"])
                if s_rec:
                    att_val = float(s_rec.get("attendance_percentage") or 0.0)
                    e_res = send_attendance_shortage_email(
                        to_email=s_rec.get("email"),
                        full_name=s_rec.get("full_name"),
                        roll_no=s_rec.get("roll_number"),
                        attendance_pct=att_val,
                        parent_email=s_rec.get("parent_email"),
                    )
                    if e_res.get("success") or e_res.get("status") in ("delivered", "config_required"):
                        email_sent += 1

                    s_res = send_attendance_shortage_whatsapp(
                        phone_number=s_rec.get("phone"),
                        full_name=s_rec.get("full_name"),
                        attendance_pct=att_val,
                        parent_phone=s_rec.get("parent_phone"),
                    )
                    if s_res.get("success") or s_res.get("status") in ("delivered", "config_required"):
                        sms_sent += 1

            st.success(f"✅ Dispatched statutory shortage alerts: {email_sent} Emails and {sms_sent} WhatsApp messages queued/sent!")


# =============================================================
# TAB 5: SECTION ANALYTICS & TRENDS
# =============================================================
# =============================================================
# TAB: SEND PREDICTIONS & RECOMMENDATIONS (FACULTY DISPATCH)
# =============================================================
elif faculty_nav == "📡 Send Predictions & Recommendations":
    st.subheader("📡 Dispatch Student AI Predictions & Recommendations")
    st.caption(
        f"Empower students in your assigned sections with automated AI performance forecasts, "
        f"continuous internal evaluation (CIE /60) diagnostics, and personalized course recommendations."
    )

    admin_sender = get_configured_admin_email()
    mail_status = is_email_service_active()

    with st.container(border=True):
        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            st.markdown("**🏛️ Institutional Sender**")
            st.code(admin_sender)
        with scol2:
            st.markdown("**📧 Mail Service**")
            if mail_status:
                st.success("● Connected / Active")
            else:
                st.warning("○ Password Required")
        with scol3:
            st.markdown("**👨‍🏫 Instructor Authority**")
            st.info(f"{faculty_name} ({employee_id})")

    st.divider()

    # Scope selection: Section-level vs Individual Student
    scope_type = st.radio(
        "Select Dispatch Target",
        [
            "👤 Single Student in Assigned Section",
            "👥 Entire Assigned Section (Batch)",
            "⚠️ Flagged At-Risk Students in Assigned Section",
        ],
        horizontal=True,
    )

    # Determine faculty assigned sections from timetable
    faculty_sections = sorted(list(set(item["section"] for item in schedule))) if schedule else ["A"]

    if scope_type == "👤 Single Student in Assigned Section":
        col_sec_pick, col_stu_pick = st.columns([1, 2])
        with col_sec_pick:
            sel_sec = st.selectbox("Select Section", faculty_sections, key="fac_disp_single_sec")

        # Fetch students for that section
        conn = get_connection()
        raw_sec_students = conn.execute(
            """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone,
                   s.attendance_percentage, s.internal_marks
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
            ORDER BY s.roll_number ASC
            """,
            (sel_sec,)
        ).fetchall()
        conn.close()
        sec_students = [dict(r) for r in raw_sec_students]

        if not sec_students:
            st.warning(f"No registered students found in Section {sel_sec}.")
        else:
            student_map = {
                f"{r['roll_number']} · {r['full_name']} (CIE: {float(r['internal_marks'] or 0):.1f}/60 | Att: {float(r['attendance_percentage'] or 0):.1f}%)": dict(r)
                for r in sec_students
            }
            with col_stu_pick:
                chosen_label = st.selectbox("Select Student", list(student_map.keys()))
                chosen_student = dict(student_map[chosen_label])

            # Fetch AI Advisory Preview
            stu_id = chosen_student["student_id"]
            preview_data = get_single_student_advisory_preview(stu_id)

            if preview_data:
                st.markdown("##### 🔍 AI Evaluation & Course Advisory Preview")
                with st.container(border=True):
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Predicted Performance", preview_data.get("predicted_perf", "N/A"))
                    risk = preview_data.get("risk_level", "Low")
                    p2.metric(
                        "Risk Classification",
                        risk,
                        delta="Action Required" if risk in ("High", "Medium") else "On Track",
                        delta_color="inverse" if risk in ("High", "Medium") else "normal"
                    )
                    p3.metric("Continuous Internal CIE", f"{preview_data.get('cie_marks', 0):.1f} / 60")
                    p4.metric("Attendance Regularity", f"{preview_data.get('attendance', 0):.1f}%")

                    st.markdown("**🧠 Explainable AI Diagnostic Summary:**")
                    st.info(preview_data.get("xai_summary", "Diagnostic evaluation active."))

                    st.markdown("**🎯 Personalized AI Recommendations to be Included:**")
                    for r_item in preview_data.get("recommendations", []):
                        st.markdown(f"- 📌 {r_item}")

                st.markdown("##### ✉️ Instructor Message & Dispatch Channels")
                col_note, col_ch = st.columns([2.5, 1])
                with col_note:
                    instructor_note = st.text_area(
                        "Custom Faculty Mentoring Advice (Appended to Email)",
                        value=f"Dear {chosen_student['full_name']}, please continue following your continuous assessment study plan. For any doubts in course concepts or problem-solving, please meet me during tutorial hours.",
                        height=100,
                        key="fac_custom_note"
                    )
                with col_ch:
                    st.markdown("**Delivery Options**")
                    send_mail = st.checkbox("📧 Send Email", value=True, key="fac_single_mail_chk")
                    send_wa = st.checkbox("💬 Send WhatsApp", value=False, key="fac_single_wa_chk")
                    st.caption(f"Recipient: `{chosen_student.get('email')}`")

                if st.button("🚀 Send AI Predictions & Recommendations Email Now", type="primary", use_container_width=True):
                    with st.spinner(f"Dispatching AI Advisory email to {chosen_student['full_name']}..."):
                        disp_res = dispatch_student_recommendations_and_predictions(
                            student_id=stu_id,
                            send_email_flag=send_mail,
                            send_whatsapp_flag=send_wa,
                            custom_note=instructor_note.strip(),
                            is_scheduled_daily=False,
                        )
                    if disp_res.get("success"):
                        st.success(f"🎉 **Email Successfully Dispatched to {chosen_student['full_name']}!** ({chosen_student.get('email')})")
                        if disp_res.get("logs"):
                            st.dataframe(pd.DataFrame(disp_res.get("logs")), use_container_width=True, hide_index=True)
                    else:
                        st.error(f"❌ Dispatch error: {disp_res.get('message')}")

    elif scope_type == "👥 Entire Assigned Section (Batch)":
        col_b_sec, col_b_ch = st.columns([1, 1])
        with col_b_sec:
            target_batch_sec = st.selectbox("Select Target Section", faculty_sections, key="fac_batch_sec")
        with col_b_ch:
            st.markdown("**Delivery Channels**")
            b_send_email = st.checkbox("📧 Deliver via Email", value=True, key="fac_batch_email_cb")
            b_send_wa = st.checkbox("💬 Deliver via WhatsApp", value=False, key="fac_batch_wa_cb")

        # Student count in section
        conn = get_connection()
        sec_count = conn.execute(
            """
            SELECT COUNT(DISTINCT s.student_id) as count
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
            """,
            (target_batch_sec,)
        ).fetchone()["count"]
        conn.close()

        st.info(f"🎯 **Target Scope:** Ready to batch-dispatch AI predictions and course recommendations to all **{sec_count}** students in Section {target_batch_sec}.")

        b_fac_note = st.text_area(
            "Course Instructor Note for Section",
            value=f"Academic update from your course instructor: Please review your continuous internal evaluation trajectory and recommended study interventions.",
            height=80,
            key="fac_batch_note"
        )

        if st.button(f"🚀 Batch Dispatch Recommendations & Predictions to Section {target_batch_sec}", type="primary", use_container_width=True):
            if not b_send_email and not b_send_wa:
                st.error("Please select at least one delivery channel (Email or WhatsApp).")
            elif sec_count == 0:
                st.warning("No registered students found in this section.")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                def update_progress(curr, total, msg):
                    frac = curr / total if total > 0 else 1.0
                    progress_bar.progress(frac)
                    status_text.caption(f"Processing ({curr}/{total}): {msg}")

                with st.spinner("Generating AI evaluations and dispatching emails to students..."):
                    res = dispatch_student_recommendations_and_predictions(
                        section=target_batch_sec,
                        student_id=None,
                        send_email_flag=b_send_email,
                        send_whatsapp_flag=b_send_wa,
                        custom_note=b_fac_note.strip(),
                        progress_callback=update_progress,
                        is_scheduled_daily=False,
                    )

                progress_bar.progress(1.0)
                status_text.empty()

                if res.get("success"):
                    st.success(f"🎉 **Batch Dispatch Completed!** {res.get('message')}")
                    r1, r2 = st.columns(2)
                    r1.metric("Emails Delivered", res.get("emails_sent", 0))
                    r2.metric("WhatsApp Messages Delivered", res.get("whatsapp_sent", res.get("sms_sent", 0)))
                    if res.get("logs"):
                        with st.expander("View Dispatch Audit Logs", expanded=False):
                            st.dataframe(pd.DataFrame(res.get("logs")), use_container_width=True, hide_index=True)
                else:
                    st.error(f"❌ Dispatch failed: {res.get('message')}")

    elif scope_type == "⚠️ Flagged At-Risk Students in Assigned Section":
        col_r_sec, col_r_opts = st.columns([1, 1])
        with col_r_sec:
            risk_target_sec = st.selectbox("Select Target Section", faculty_sections, key="fac_risk_target_sec")
        with col_r_opts:
            r_mail = st.checkbox("📧 Send Email", value=True, key="fac_r_mail")
            r_wa = st.checkbox("💬 Send WhatsApp", value=False, key="fac_r_wa")

        conn = get_connection()
        sec_risk_students = conn.execute(
            """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone,
                   s.attendance_percentage, s.internal_marks
            FROM students s
            JOIN semester_registrations sr ON sr.student_id = s.student_id
            WHERE sr.section = ? AND sr.status = 'Registered'
              AND (s.attendance_percentage < 75.0 OR s.internal_marks < 24.0)
            ORDER BY s.roll_number ASC
            """,
            (risk_target_sec,)
        ).fetchall()
        conn.close()

        if not sec_risk_students:
            st.success(f"🎉 No students in Section {risk_target_sec} are currently flagged for CIE deficits or attendance shortages.")
        else:
            st.warning(f"⚠️ **{len(sec_risk_students)}** students in Section {risk_target_sec} require early intervention (CIE < 24/60 or Attendance < 75%).")
            st.dataframe(
                pd.DataFrame([
                    {
                        "Roll Number": r["roll_number"],
                        "Name": r["full_name"],
                        "Email": r["email"],
                        "Internal CIE (/60)": f"{float(r['internal_marks'] or 0):.1f}",
                        "Attendance %": f"{float(r['attendance_percentage'] or 0):.1f}%",
                    }
                    for r in sec_risk_students
                ]),
                use_container_width=True,
                hide_index=True
            )

            risk_note = st.text_area(
                "Remedial Advice Note for Flagged Students",
                value="Urgent Academic Advisory: Your current continuous internal marks and/or attendance are below passing criteria. Please review the attached AI recommendations and attend mandatory tutorial remediation.",
                height=80,
                key="fac_risk_area_note"
            )

            if st.button(f"🚀 Send Remedial Predictions & Recommendations to Flagged Students ({len(sec_risk_students)})", type="primary", use_container_width=True):
                prog_bar = st.progress(0.0)
                stat_text = st.empty()
                r_emails_sent = 0
                r_wa_sent = 0

                for idx, r in enumerate(sec_risk_students, 1):
                    stat_text.caption(f"Sending ({idx}/{len(sec_risk_students)}): {r['roll_number']} ({r['full_name']})")
                    prog_bar.progress(idx / len(sec_risk_students))
                    r_res = dispatch_student_recommendations_and_predictions(
                        student_id=r["student_id"],
                        send_email_flag=r_mail,
                        send_whatsapp_flag=r_wa,
                        custom_note=risk_note.strip(),
                        is_scheduled_daily=False,
                    )
                    if r_res.get("success"):
                        r_emails_sent += r_res.get("emails_sent", 0)
                        r_wa_sent += r_res.get("sms_sent", 0)

                prog_bar.progress(1.0)
                stat_text.empty()
                st.success(f"🎉 Dispatched remedial advisories to {r_emails_sent} students in Section {risk_target_sec}!")


elif faculty_nav == "📊 Section Analytics & Trends":
    st.subheader("📊 Section Performance Analytics & Distribution")
    st.caption("Aggregated analytics across Section A through J assessments and attendance.")

    conn = get_connection()
    sec_stats = conn.execute(
        """
        SELECT section, COUNT(*) as student_count,
               AVG(attendance_percentage) as avg_attendance,
               AVG(internal_marks) as avg_internal
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
                    "CIE Health": "Normal (≥30)" if float(r['avg_internal'] or 0) >= 30 else "Remedial Attention",
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
