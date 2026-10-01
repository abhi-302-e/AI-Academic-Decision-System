"""Faculty teaching, course assessment, and session attendance workspace."""

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
    get_course_assessment_roster,
    get_course_attendance_percentage,
    get_faculty_timetable,
    get_recorded_attendance_session,
    get_session_attendance_roster,
    get_teachable_course_options,
    request_faculty_teaching_assignment,
    save_course_assessment,
    submit_session_attendance,
)
from email_service import send_email
from sms_service import send_academic_update_sms


require_faculty()
faculty = dict(st.session_state.user_data)
st.title("Faculty Dashboard")
st.success(f"Welcome {faculty['full_name']}")

st.subheader("Request a teaching assignment")
teachable_courses = get_teachable_course_options(faculty["department"])
if not teachable_courses:
    st.info("No published courses are available for your department yet.")
else:
    course_options = {
        f"{course['course_code']} · {course['course_name']} · Year {course['year']} Semester {course['semester']}": course
        for course in teachable_courses
    }
    with st.form("faculty_teaching_request"):
        course_label = st.selectbox("Course", list(course_options))
        course = course_options[course_label]
        section = st.selectbox("Section", list(SECTION_NAMES))
        day = st.selectbox("Weekday", list(ACADEMIC_DAYS))
        slot = st.selectbox(
            "50-minute period",
            list(ACADEMIC_PERIODS),
            format_func=lambda value: f"{value} · {ACADEMIC_PERIODS[value][0]}–{ACADEMIC_PERIODS[value][1]}",
        )
        room = st.text_input("Room (optional)")
        request_slot = st.form_submit_button("Submit for Admin approval")
    if request_slot:
        request_id = request_faculty_teaching_assignment(
            faculty["faculty_id"], course["course_id"], section, day, slot, room
        )
        if request_id:
            st.success("Teaching request submitted for Admin approval.")
        else:
            st.error("The request conflicts with a timetable slot or could not be saved.")

schedule = get_faculty_timetable(faculty["faculty_id"])
st.divider()
st.subheader("Course assessments")
if not schedule:
    st.info("Approved teaching timetable slots will appear here. Only assigned courses can be graded.")
else:
    schedule_options = {
        f"{item['day']} {item['slot']} · {item['course_code']} · Section {item['section']}": item
        for item in schedule
    }
    schedule_label = st.selectbox("Assigned course session", list(schedule_options), key="assessment_schedule")
    selected_schedule = schedule_options[schedule_label]
    roster = get_course_assessment_roster(
        selected_schedule["timetable_id"],
        faculty["faculty_id"]
    )
    if not roster:
        st.info("No students are registered for this course and section. Marks cannot be entered before registration.")
    else:
        student_options = {
            f"{item['roll_number']} · {item['full_name']}": item
            for item in roster
        }
        student_label = st.selectbox("Registered student", list(student_options))
        selected_student = student_options[student_label]
        st.caption(
            f"{selected_schedule['course_code']} · Section {selected_schedule['section']} · "
            f"Semester {selected_schedule['semester']}"
        )
        with st.form("course_assessment_form"):
            assignment = st.number_input(
                "Assignment · /10", min_value=0.0, max_value=10.0,
                value=float(selected_student["assignment_marks"]) if selected_student["assignment_marks"] is not None else None,
                step=0.5,
            )
            quiz = st.number_input(
                "Quiz · /10", min_value=0.0, max_value=10.0,
                value=float(selected_student["quiz_marks"]) if selected_student["quiz_marks"] is not None else None,
                step=0.5,
            )
            mid_exam = st.number_input(
                "Mid exam · /30", min_value=0.0, max_value=30.0,
                value=float(selected_student["mid_exam_marks"]) if selected_student["mid_exam_marks"] is not None else None,
                step=0.5,
            )
            viva = st.number_input(
                "Viva voce · /10", min_value=0.0, max_value=10.0,
                value=float(selected_student["viva_marks"]) if selected_student["viva_marks"] is not None else None,
                step=0.5,
            )
            external = st.number_input(
                "External end-semester exam · /40", min_value=0.0, max_value=40.0,
                value=float(selected_student["external_marks"]) if selected_student["external_marks"] is not None else None,
                step=0.5,
            )
            save_assessment = st.form_submit_button("Save this course assessment", type="primary")

        if save_assessment:
            entered = (assignment, quiz, mid_exam, viva, external)
            if any(value is None for value in entered):
                st.error("Enter all five components before saving the course assessment.")
            else:
                success, message = save_course_assessment(
                    selected_schedule["timetable_id"],
                    faculty["faculty_id"],
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
                    overall_total = internal_total + external
                    course_attendance = get_course_attendance_percentage(
                        selected_student["student_id"],
                        selected_schedule["course_id"],
                        selected_schedule["section"],
                    )
                    if course_attendance is None:
                        update_message = (
                            f"{selected_schedule['course_name']} marks saved. "
                            f"Internal {internal_total}/60, External {external}/40. "
                            "Course risk prediction will be available after attendance is recorded and Admin trains the models."
                        )
                    else:
                        update_message = (
                            f"{selected_schedule['course_name']} marks saved. "
                            f"Internal {internal_total}/60, External {external}/40, "
                            f"course attendance {course_attendance:.1f}%."
                        )
                    create_student_notification(
                        selected_student["student_id"],
                        "Course assessment updated",
                        update_message,
                    )
                    recipient = None
                    try:
                        from database import get_student
                        recipient = get_student(selected_student["student_id"])
                    except Exception:
                        pass
                    if recipient and recipient["email"]:
                        try:
                            send_email(
                                recipient["email"],
                                "Course assessment updated",
                                update_message,
                            )
                        except Exception:
                            pass
                    if recipient and recipient["phone"]:
                        try:
                            send_academic_update_sms(recipient["phone"], update_message)
                        except Exception:
                            pass
                    st.success(message)
                    st.rerun()

st.divider()
st.subheader("Session attendance")
if not schedule:
    st.info("Approved teaching slots will appear here.")
else:
    schedule_options = {
        f"{item['day']} {item['slot']} · {item['course_code']} · Section {item['section']}": item
        for item in schedule
    }
    schedule_label = st.selectbox("Scheduled class", list(schedule_options), key="attendance_schedule")
    selected_schedule = schedule_options[schedule_label]
    session_date = st.date_input("Class date", value=date.today())
    date_text = session_date.isoformat()
    if session_date.strftime("%a") != selected_schedule["day"]:
        st.warning(f"Select a {selected_schedule['day']} to match the approved timetable slot.")
    elif get_recorded_attendance_session(selected_schedule["timetable_id"], date_text):
        st.success("Attendance has already been submitted for this course session and date.")
    else:
        roster = get_session_attendance_roster(selected_schedule["timetable_id"], faculty["faculty_id"])
        if not roster:
            st.info("No students are registered in this course and section.")
        else:
            with st.form("session_attendance_form"):
                roster_frame = pd.DataFrame([
                    {
                        "Student ID": item["student_id"],
                        "Roll Number": item["roll_number"],
                        "Student": item["full_name"],
                        "Present": True,
                    }
                    for item in roster
                ])
                marked = st.data_editor(
                    roster_frame,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["Student ID", "Roll Number", "Student"],
                    column_config={"Present": st.column_config.CheckboxColumn("Present")},
                    key=f"session_attendance_{selected_schedule['timetable_id']}_{date_text}",
                )
                submit_attendance = st.form_submit_button("Submit attendance once for this session", type="primary")
            if submit_attendance:
                records = {
                    int(row["Student ID"]): bool(row["Present"])
                    for _, row in marked.iterrows()
                }
                session_id = submit_session_attendance(
                    selected_schedule["timetable_id"], faculty["faculty_id"], date_text, records
                )
                if session_id:
                    st.success("Attendance submitted and locked for this session.")
                    st.rerun()
                else:
                    st.error("Attendance could not be submitted. Check the roster or whether it was already submitted.")

st.divider()
if st.button("Log out"):
    st.session_state.clear()
    st.rerun()
