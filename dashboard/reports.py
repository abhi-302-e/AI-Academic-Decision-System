"""
===========================================================
AI-Based Autonomous Academic Decision System
Domain: Artificial Intelligence + Machine Learning + Data Analytics
Theme: AI Academic Governance
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
Institutional Reports & Governance Summaries
===========================================================
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auth import require_admin
from database import get_all_students, get_connection

require_admin()

st.title("📄 Institutional Academic Reports & Governance Dossiers")
st.caption("AI-Based Autonomous Academic Decision System · Comprehensive Reports for Deans, Academic Heads & Faculty Mentors.")

students_df = get_all_students()

if students_df.empty:
    st.warning("No student records available for reporting.")
    st.stop()

# Ensure types
for col in ["cgpa", "attendance_percentage", "internal_marks", "external_marks"]:
    if col in students_df.columns:
        students_df[col] = pd.to_numeric(students_df[col], errors="coerce")

students_df["total_marks"] = students_df["internal_marks"].fillna(0) + students_df["external_marks"].fillna(0)

rep_type = st.selectbox(
    "Select Report Type to Generate",
    [
        "1. Comprehensive Institutional Student Performance Report",
        "2. Early Warning & At-Risk Intervention Report",
        "3. Section-Wise Evaluation Summary (Sections A to J)",
        "4. Course-Level CIE 60/40 Assessment Audit",
    ]
)

if rep_type.startswith("1."):
    st.subheader("📋 Comprehensive Student Performance Report (500 Students)")
    st.caption("Complete academic profiles across Year 1 Semester 1.")

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        sel_dept = st.selectbox("Filter Department", ["All Departments"] + sorted(list(students_df["department"].unique())))
    with f_col2:
        sel_sec = st.selectbox("Filter Section", ["All Sections"] + sorted(list(students_df["section"].dropna().unique())))

    filtered_df = students_df.copy()
    if sel_dept != "All Departments":
        filtered_df = filtered_df[filtered_df["department"] == sel_dept]
    if sel_sec != "All Sections":
        filtered_df = filtered_df[filtered_df["section"] == sel_sec]

    st.dataframe(
        pd.DataFrame([
            {
                "Roll Number": r["roll_number"],
                "Full Name": r["full_name"],
                "Department": r["department"],
                "Section": f"Section {r['section']}",
                "Attendance %": f"{float(r['attendance_percentage'] or 0):.1f}%",
                "Internal /60": f"{float(r['internal_marks'] or 0):.1f}",
                "External /40": f"{float(r['external_marks'] or 0):.1f}",
                "Total /100": f"{float(r['total_marks'] or 0):.1f}",
                "CGPA": f"{float(r['cgpa'] or 0):.2f}",
            }
            for _, r in filtered_df.iterrows()
        ]),
        use_container_width=True,
        hide_index=True,
    )

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Student Performance Report (CSV)",
        data=csv_data,
        file_name="student_performance_report.csv",
        mime="text/csv",
    )

elif rep_type.startswith("2."):
    st.subheader("🚨 Early Warning & At-Risk Intervention Dossier")
    st.caption("Identifies students falling below the 75% attendance threshold or scoring under 24/60 in internal evaluations.")

    at_risk = students_df[
        (students_df["attendance_percentage"] < 75.0) | (students_df["internal_marks"] < 24.0)
    ].sort_values(by=["attendance_percentage", "internal_marks"])

    st.metric("Total Cohort Flagged for Academic Intervention", f"{len(at_risk)} Students", delta=f"{(len(at_risk)/len(students_df))*100:.1f}% of cohort", delta_color="inverse")

    st.dataframe(
        pd.DataFrame([
            {
                "Roll Number": r["roll_number"],
                "Full Name": r["full_name"],
                "Department": r["department"],
                "Section": f"Section {r['section']}",
                "Attendance %": f"{float(r['attendance_percentage'] or 0):.1f}%",
                "Internal /60": f"{float(r['internal_marks'] or 0):.1f}",
                "Total /100": f"{float(r['total_marks'] or 0):.1f}",
                "CGPA": f"{float(r['cgpa'] or 0):.2f}",
                "Intervention Type": "Remedial Tutorials & Attendance Counseling" if r["attendance_percentage"] < 75 else "Academic Mentorship",
            }
            for _, r in at_risk.iterrows()
        ]),
        use_container_width=True,
        hide_index=True,
    )

    csv_risk = at_risk.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download At-Risk Student Dossier (CSV)",
        data=csv_risk,
        file_name="at_risk_student_dossier.csv",
        mime="text/csv",
    )

elif rep_type.startswith("3."):
    st.subheader("🏫 Section-Wise Comparative Report (Sections A to J)")
    st.caption("50 students per section across 10 sections.")

    sec_summary = students_df.groupby("section").agg(
        Total_Students=("student_id", "count"),
        Avg_Attendance=("attendance_percentage", "mean"),
        Avg_Internal=("internal_marks", "mean"),
        Avg_External=("external_marks", "mean"),
        Avg_CGPA=("cgpa", "mean"),
        Shortage_Students=("attendance_percentage", lambda s: (s < 75.0).sum()),
    ).reset_index()

    st.dataframe(
        pd.DataFrame([
            {
                "Section": f"Section {r['section']}",
                "Capacity / Strength": f"{r['Total_Students']} / 50",
                "Mean Attendance": f"{r['Avg_Attendance']:.1f}%",
                "Mean CIE /60": f"{r['Avg_Internal']:.1f}",
                "Mean External /40": f"{r['Avg_External']:.1f}",
                "Mean CGPA": f"{r['Avg_CGPA']:.2f}",
                "Exam Shortages (<75%)": r["Shortage_Students"],
            }
            for _, r in sec_summary.iterrows()
        ]),
        use_container_width=True,
        hide_index=True,
    )

    csv_sec = sec_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Section-Wise Report (CSV)",
        data=csv_sec,
        file_name="section_wise_academic_report.csv",
        mime="text/csv",
    )

elif rep_type.startswith("4."):
    st.subheader("📚 Course-Level CIE 60/40 Assessment Audit")
    st.caption("Audit log across all 4,000 course assessments.")

    conn = get_connection()
    audit_data = conn.execute(
        """
        SELECT ca.assessment_id, s.roll_number, s.full_name, s.section,
               COALESCE(c.catalog_code, c.course_code) AS course_code, c.course_name,
               ca.mid_exam_marks, ca.assignment_marks, ca.quiz_marks, ca.viva_marks,
               (COALESCE(ca.mid_exam_marks, 0) + COALESCE(ca.assignment_marks, 0) + COALESCE(ca.quiz_marks, 0) + COALESCE(ca.viva_marks, 0)) AS internal_total,
               ca.external_marks,
               (COALESCE(ca.mid_exam_marks, 0) + COALESCE(ca.assignment_marks, 0) + COALESCE(ca.quiz_marks, 0) + COALESCE(ca.viva_marks, 0) + COALESCE(ca.external_marks, 0)) AS overall_total
        FROM course_assessments ca
        JOIN student_registered_courses src ON ca.registration_id = src.registration_id
        JOIN students s ON src.student_id = s.student_id
        JOIN courses c ON src.course_id = c.course_id
        ORDER BY s.roll_number ASC, c.course_code ASC
        LIMIT 500
        """
    ).fetchall()
    conn.close()

    if audit_data:
        st.dataframe(
            pd.DataFrame([
                {
                    "Roll": r["roll_number"],
                    "Student": r["full_name"],
                    "Section": f"Section {r['section']}",
                    "Course": r["course_code"],
                    "Mid /30": f"{r['mid_exam_marks']:.1f}" if r["mid_exam_marks"] is not None else "—",
                    "Assn /10": f"{r['assignment_marks']:.1f}" if r["assignment_marks"] is not None else "—",
                    "Quiz /10": f"{r['quiz_marks']:.1f}" if r["quiz_marks"] is not None else "—",
                    "Viva /10": f"{r['viva_marks']:.1f}" if r["viva_marks"] is not None else "—",
                    "CIE /60": f"{r['internal_total']:.1f}" if r["internal_total"] is not None else "—",
                    "SEE /40": f"{r['external_marks']:.1f}" if r["external_marks"] is not None else "—",
                    "Total /100": f"{r['overall_total']:.1f}" if r["overall_total"] is not None else "—",
                }
                for r in audit_data
            ]),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Displaying top 500 audit entries. Full 4,000 records available in database.")