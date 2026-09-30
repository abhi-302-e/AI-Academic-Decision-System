"""
===========================================================
AI-Based Autonomous Academic Decision System

Faculty Dashboard
===========================================================
"""

import sys
from pathlib import Path
from datetime import date

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))   # Use insert instead of append

import streamlit as st
import pandas as pd

from auth import require_faculty
from database import (
    get_all_students,
    get_student_by_roll,
    update_student_marks,
    create_student_notification,
    get_faculty_by_employee_id,
    update_faculty,
    get_teachable_course_options,
    request_faculty_teaching_assignment,
    get_faculty_timetable,
    get_session_attendance_roster,
    get_recorded_attendance_session,
    submit_session_attendance,
    SECTION_NAMES,
    ACADEMIC_DAYS,
    ACADEMIC_PERIODS,
)

from prediction import predict_student
from recommendation_engine import generate_recommendation
from email_service import send_email
from sms_service import send_academic_update_sms


# ==========================================================
# LOGIN CHECK
# ==========================================================

require_faculty()

faculty = st.session_state.user_data


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

# ==========================================================
# HEADER
# ==========================================================

st.title("👨‍🏫 Faculty Dashboard")

st.success(f"Welcome {faculty['full_name']}")


# ==========================================================
# STUDENT SEARCH
# ==========================================================

st.subheader("Search Student")

students = get_all_students()

roll_numbers = students["roll_number"].tolist()

selected_roll = st.selectbox(

    "Select Roll Number",

    roll_numbers

)

student = get_student_by_roll(

    selected_roll

)

# ==========================================================
# DISPLAY STUDENT DETAILS
# ==========================================================

if student:

    st.subheader("Student Information")

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Name:**", student["full_name"])
        st.write("**Roll Number:**", student["roll_number"])
        st.write("**Department:**", student["department"])
        st.write("**Semester:**", student["semester"])

    with col2:

        st.write("**Email:**", student["email"])
        st.write("**CGPA:**", student["cgpa"])
        st.write("**Attendance:**", f"{student['attendance_percentage']}%")


    st.divider()


# ==========================================================
# EDIT MARKS
# ==========================================================

    st.subheader("Update Student Marks")

    assignment = st.number_input(
        "Assignment Marks",
        0.0,
        100.0,
        float(student["assignment_marks"])
    )

    quiz = st.number_input(
        "Quiz Marks",
        0.0,
        100.0,
        float(student["quiz_marks"])
    )

    mid = st.number_input(
        "Mid Exam Marks",
        0.0,
        100.0,
        float(student["mid_exam_marks"])
    )

    end = st.number_input(
        "End Semester Marks",
        0.0,
        100.0,
        float(student["end_sem_marks"])
    )

    lab = st.number_input(
        "Lab Marks",
        0.0,
        100.0,
        float(student["lab_marks"])
    )

# ==========================================================
# AI PREDICTION
# ==========================================================

    prediction = predict_student(student)

    st.subheader("AI Prediction")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Performance",
            prediction["performance_prediction"]
        )

    with col2:

        st.metric(
            "Risk Level",
            prediction["risk_level"]
        )


# ==========================================================
# AI RECOMMENDATIONS
# ==========================================================

    st.subheader("Recommendations")

    result = generate_recommendation(student)

    for recommendation in result["recommendations"]:

        st.info(recommendation)


# ==========================================================
# SAVE BUTTON
# ==========================================================

if st.button("Save Changes"):

    update_student_marks(
        student["student_id"],
        assignment,
        quiz,
        mid,
        end,
        lab
    )

    updated_student = dict(student)
    updated_student.update({
        "assignment_marks": assignment,
        "quiz_marks": quiz,
        "mid_exam_marks": mid,
        "end_sem_marks": end,
        "lab_marks": lab,
        "attendance_percentage": attendance,
    })
    updated_student["average_marks"] = round(
        (assignment + quiz + mid + end + lab) / 5,
        2
    )
    updated_student["performance_score"] = round(
        updated_student["average_marks"] * 0.7 + attendance * 0.3,
        2
    )
    result = generate_recommendation(updated_student)
    notification_message = (
        f"Performance prediction: {result['performance_prediction']}\n"
        f"Academic risk: {result['risk_level']}\n\n"
        "Recommended actions:\n"
        + "\n".join(
            f"- {item}" for item in result["recommendations"]
        )
    )
    create_student_notification(
        student["student_id"],
        "New academic update",
        notification_message
    )

    email_sent = False
    try:
        send_email(
            student["email"],
            "New academic performance update",
            (
                f"Dear {student['full_name']},\n\n"
                "Your faculty member updated your academic record.\n\n"
                f"{notification_message}\n\n"
                "Sign in to the Student Dashboard to view your latest update."
            )
        )
        email_sent = True
    except Exception as error:
        pass

    sms_sent = False
    try:
        sms_sent = send_academic_update_sms(
            student.get("phone", ""),
            (
                f"Academic update for {student['full_name']}: "
                f"Performance {result['performance_prediction']}; "
                f"risk {result['risk_level']}. "
                + "Actions: " + "; ".join(result["recommendations"])
            )
        )
    except Exception:
        pass

    st.success("Student record updated and AI recommendations saved to the student's dashboard.")
    if email_sent:
        st.success("The student update was also sent to the student's email.")
    else:
        st.warning("Email delivery failed or is not configured; the dashboard notification was saved.")
    if sms_sent:
        st.success("The student update was also sent to the student's mobile number.")
    else:
        st.warning("SMS delivery failed or is not configured; the dashboard notification was saved.")


        # ==========================================================
        # TEACHING ASSIGNMENT REQUESTS
        # ==========================================================

        st.divider()
        st.subheader("Request a teaching slot")
        available_courses = get_teachable_course_options(faculty["department"])

        if not available_courses:
            st.info("No published courses are available for your department yet.")
        else:
            course_options = {
                (
                    f"{course['course_code']} · {course['course_name']} · "
                    f"Year {course['year']} Semester {course['semester']}"
                ): course
                for course in available_courses
            }
            with st.form("teaching_assignment_request"):
                selected_course_label = st.selectbox("Course", list(course_options))
                section = st.selectbox("Section", list(SECTION_NAMES))
                day = st.selectbox("Weekday", list(ACADEMIC_DAYS))
                period = st.selectbox(
                    "50-minute period",
                    list(ACADEMIC_PERIODS),
                    format_func=lambda slot: (
                        f"{slot} · {ACADEMIC_PERIODS[slot][0]}–{ACADEMIC_PERIODS[slot][1]}"
                    )
                )
                room = st.text_input("Room (optional)")
                request_slot = st.form_submit_button("Submit for Admin approval", type="primary")

            if request_slot:
                course = course_options[selected_course_label]
                request_id = request_faculty_teaching_assignment(
                    faculty["faculty_id"],
                    course["course_id"],
                    section,
                    day,
                    period,
                    room,
                )
                if request_id:
                    st.success("Teaching slot request submitted. It becomes active after Admin approval.")
                else:
                    st.error("Request conflicts with your schedule, the section schedule, or an existing request.")


        # ==========================================================
        # SESSION ATTENDANCE
        # ==========================================================

        st.subheader("Session attendance")
        teaching_schedule = get_faculty_timetable(faculty["faculty_id"])
        if not teaching_schedule:
            st.info("Approved teaching slots will appear here.")
        else:
            schedule_options = {
                (
                    f"{item['day']} {item['slot']} · {item['course_code']} · "
                    f"Section {item['section']}"
                ): item
                for item in teaching_schedule
            }
            selected_schedule_label = st.selectbox(
                "Scheduled class",
                list(schedule_options),
                key="attendance_schedule"
            )
            selected_schedule = schedule_options[selected_schedule_label]
            session_date = st.date_input("Class date", value=date.today())
            session_date_text = session_date.isoformat()

            existing_session = get_recorded_attendance_session(
                selected_schedule["timetable_id"],
                session_date_text
            )
            if session_date.strftime("%a") != selected_schedule["day"]:
                st.warning(f"Choose a {selected_schedule['day']} to match this scheduled class.")
            elif existing_session:
                st.success(f"Attendance was already submitted for this session on {session_date_text}.")
            else:
                roster = get_session_attendance_roster(
                    selected_schedule["timetable_id"],
                    faculty["faculty_id"]
                )
                if not roster:
                    st.info("No registered students are enrolled in this course and section yet.")
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
                        marked_roster = st.data_editor(
                            roster_frame,
                            use_container_width=True,
                            hide_index=True,
                            disabled=["Student ID", "Roll Number", "Student"],
                            column_config={
                                "Present": st.column_config.CheckboxColumn("Present")
                            },
                            key=f"attendance_{selected_schedule['timetable_id']}_{session_date_text}"
                        )
                        submit_attendance = st.form_submit_button(
                            "Submit attendance for this session",
                            type="primary"
                        )

                    if submit_attendance:
                        attendance_records = {
                            int(row["Student ID"]): bool(row["Present"])
                            for _, row in marked_roster.iterrows()
                        }
                        session_id = submit_session_attendance(
                            selected_schedule["timetable_id"],
                            faculty["faculty_id"],
                            session_date_text,
                            attendance_records
                        )
                        if session_id:
                            st.success("Attendance submitted. This scheduled session cannot be submitted again.")
                            st.rerun()
                        else:
                            st.error("Attendance could not be submitted. Confirm every student is marked and that this session has not already been submitted.")


# ==========================================================
# LOGOUT
# ==========================================================

st.divider()

if st.button("Logout"):

    st.session_state.clear()

    st.rerun()

