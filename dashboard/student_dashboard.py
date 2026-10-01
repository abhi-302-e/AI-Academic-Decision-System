"""Student academic dashboard."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auth import require_student
from database import (
    get_courses_for_semester_structure,
    get_published_semester_structures,
    get_section_capacity,
    get_student_by_roll,
    get_student_notifications,
    get_student_registered_courses,
    get_student_registration_for_structure,
    mark_student_notifications_read,
    register_student_for_semester,
)
from prediction import predict_student
from recommendation_engine import generate_recommendation


require_student()
session_student = dict(st.session_state.user_data)
student = get_student_by_roll(session_student["roll_number"]) or session_student
st.session_state.user_data = student
st.session_state.user = student

attendance = float(student.get("attendance_percentage") or 0)
cgpa = student.get("cgpa")
internal_marks = student.get("internal_marks")
external_marks = student.get("external_marks")
prediction = predict_student(student)
recommendation_result = generate_recommendation(student)
notifications = get_student_notifications(student["student_id"])
unread_count = sum(not notification["is_read"] for notification in notifications)
current_year = int(student.get("current_year") or 1)
current_semester = int(student.get("semester") or 1)

header, logout_col = st.columns([5, 1], vertical_alignment="center")
with header:
    st.title(f"Welcome, {student['full_name']}")
    st.caption(
        f"{student['roll_number']}  ·  {student['department']}  ·  "
        f"Year {current_year}, Semester {current_semester}, "
        f"Section {student.get('section') or 'Unassigned'}"
    )
with logout_col:
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

metric_cols = st.columns(5)
metric_cols[0].metric("CGPA", f"{cgpa:.2f}" if cgpa is not None else "Not recorded")
metric_cols[1].metric("Attendance", f"{attendance:.1f}%" if attendance else "Not recorded")
metric_cols[2].metric("Internal", f"{internal_marks:.1f}/60" if internal_marks is not None else "Not recorded")
metric_cols[3].metric("External", f"{external_marks:.1f}/40" if external_marks is not None else "Not recorded")
metric_cols[4].metric("Risk", prediction["risk_level"])

overview_tab, courses_tab, results_tab, support_tab, notifications_tab = st.tabs([
    "Overview", "Courses", "Results", "Recommendations", f"Notifications ({unread_count})"
])

with overview_tab:
    overview_col, activity_col = st.columns([1.1, 1])
    with overview_col:
        st.subheader("Academic snapshot")
        st.write(f"**Current standing:** Year {current_year}, Semester {current_semester}")
        st.write(f"**Assigned section:** {student.get('section') or 'Not assigned'}")
        if internal_marks is not None and external_marks is not None:
            total_marks = round(float(internal_marks) + float(external_marks), 2)
            st.metric("Combined assessment", f"{total_marks:.1f}/100")
        else:
            st.info("Assessment totals will appear after faculty records your marks.")
    with activity_col:
        st.subheader("Latest updates")
        if notifications:
            for notification in notifications[:3]:
                with st.container(border=True):
                    st.markdown(f"**{notification['title']}**")
                    st.caption(notification["created_at"])
                    st.write(notification["message"])
        else:
            st.info("Faculty updates and academic recommendations will appear here.")

with courses_tab:
    st.subheader("Semester registration")
    structures = get_published_semester_structures(
        student["department"],
        current_year
    )
    if not structures:
        st.info(
            f"No published course structure is available for Year {current_year} "
            f"in {student['department']}. Contact the academic office."
        )
    else:
        structure_options = {
            f"Year {row['year']} · Semester {row['semester']} · {row['academic_batch']}": row
            for row in structures
        }
        structure_label = st.selectbox("Available semester", list(structure_options))
        selected_structure = structure_options[structure_label]
        structure_courses = get_courses_for_semester_structure(selected_structure["structure_id"])
        if not structure_courses:
            st.warning("This published semester has no active courses yet.")
        else:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Course code": course["course_code"],
                        "Course": course["course_name"],
                        "Credits": course["credits"],
                        "Type": course["course_type"],
                    }
                    for course in structure_courses
                ]),
                use_container_width=True,
                hide_index=True,
            )
            registration = get_student_registration_for_structure(
                student["student_id"], selected_structure["structure_id"]
            )
            if registration:
                st.success(f"Registered in Section {registration['section']}.")
            else:
                capacity = get_section_capacity(selected_structure["structure_id"])
                assigned = next(
                    (row for row in capacity if row["section"] == student.get("section")),
                    None,
                )
                if assigned is None:
                    st.error("No A–J section is assigned to your profile. Contact the academic office.")
                elif assigned["available"] <= 0:
                    st.error(f"Section {assigned['section']} is full. Contact the academic office.")
                else:
                    st.caption(f"Section {assigned['section']} · {assigned['available']} seats available (75 maximum).")
                    st.info("Semester payment is simulated. No payment details are collected and no charge is made.")
                    payment_acknowledged = st.checkbox(
                        "I understand this is a simulated payment step",
                        key=f"demo_payment_ack_{selected_structure['structure_id']}"
                    )
                    if st.button("Register for semester", type="primary", disabled=not payment_acknowledged):
                        registration_id = register_student_for_semester(
                            student["student_id"],
                            selected_structure["structure_id"],
                            selected_structure["academic_batch"],
                            selected_structure["semester"],
                            [course["course_id"] for course in structure_courses],
                            student["section"],
                        )
                        if registration_id:
                            st.success("Semester registration complete.")
                            st.rerun()
                        else:
                            st.error("Registration failed. Refresh or contact the academic office.")

    st.subheader("Registered courses")
    registered_courses = get_student_registered_courses(student["student_id"], current_semester)
    if registered_courses:
        st.dataframe(
            pd.DataFrame([
                {
                    "Academic year": course["academic_year"],
                    "Semester": course["semester"],
                    "Course code": course["course_code"],
                    "Course": course["course_name"],
                    "Credits": course["credits"],
                    "Type": course["course_type"],
                }
                for course in registered_courses
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"No registered courses for Semester {current_semester} yet.")

with results_tab:
    st.subheader("Assessment results")
    assessment_rows = [
        {"Assessment": "Assignment", "Score": student.get("assignment_marks"), "Maximum": 100},
        {"Assessment": "Quiz", "Score": student.get("quiz_marks"), "Maximum": 100},
        {"Assessment": "Mid exam", "Score": student.get("mid_exam_marks"), "Maximum": 100},
        {"Assessment": "Internal total", "Score": internal_marks, "Maximum": 60},
        {"Assessment": "End-semester exam", "Score": student.get("end_sem_marks"), "Maximum": 100},
        {"Assessment": "External total", "Score": external_marks, "Maximum": 40},
    ]
    if internal_marks is not None and external_marks is not None:
        assessment_rows.append({
            "Assessment": "Combined total",
            "Score": round(float(internal_marks) + float(external_marks), 2),
            "Maximum": 100,
        })
    st.dataframe(pd.DataFrame(assessment_rows), use_container_width=True, hide_index=True)
    st.caption("External total is recorded out of 40; the raw end-semester component is shown out of 100.")
    st.subheader("Attendance")
    if attendance:
        st.progress(min(max(attendance / 100, 0.0), 1.0), text=f"{attendance:.1f}% recorded attendance")
    else:
        st.info("Attendance has not been recorded yet.")

with support_tab:
    st.subheader("AI recommendations")
    st.metric("Predicted performance", prediction["performance_prediction"])
    st.metric("Academic risk", prediction["risk_level"])
    for item in recommendation_result["recommendations"]:
        st.info(item)

with notifications_tab:
    st.subheader("Notifications")
    if notifications:
        st.caption(f"{unread_count} unread")
        for notification in notifications:
            with st.container(border=True):
                st.markdown(f"**{notification['title']}**")
                st.caption(notification["created_at"])
                st.write(notification["message"])
        if unread_count and st.button("Mark all as read"):
            mark_student_notifications_read(student["student_id"])
            st.rerun()
    else:
        st.info("No notifications yet.")
