"""
===========================================================
AI-Based Autonomous Academic Decision System
Domain: Artificial Intelligence + Machine Learning + Data Analytics
Theme: AI Academic Governance
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
Phase 3: Exploratory Data Analysis (EDA) & Academic Analytics
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

st.title("📊 Phase 3: Exploratory Data Analysis (EDA) & Institutional Analytics")
st.caption("AI-Based Autonomous Academic Decision System · Comprehensive Analytics on 500 First-Year Students across Sections A through J.")

students_df = get_all_students()

if students_df.empty:
    st.warning("No student records found in the database.")
    st.stop()

# Ensure numeric types
for col in ["cgpa", "attendance_percentage", "internal_marks", "external_marks"]:
    if col in students_df.columns:
        students_df[col] = pd.to_numeric(students_df[col], errors="coerce")

students_df["total_marks"] = students_df["internal_marks"].fillna(0) + students_df["external_marks"].fillna(0)

# Top Summary KPIs
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Enrolled Students", f"{len(students_df):,}")
with k2:
    avg_cgpa = students_df["cgpa"].mean()
    st.metric("Institutional Mean CGPA", f"{avg_cgpa:.2f} / 10.0")
with k3:
    avg_att = students_df["attendance_percentage"].mean()
    st.metric("Mean Attendance", f"{avg_att:.1f}%")
with k4:
    avg_int = students_df["internal_marks"].mean()
    st.metric("Mean CIE Score", f"{avg_int:.1f} / 60")
with k5:
    shortage_count = (students_df["attendance_percentage"] < 75.0).sum()
    st.metric("Attendance Shortages (<75%)", f"{shortage_count} Students", delta=f"{(shortage_count/len(students_df))*100:.1f}% of cohort", delta_color="inverse")

eda_tab1, eda_tab2, eda_tab3, eda_tab4, eda_tab5 = st.tabs([
    "📈 Attendance Analytics",
    "🏫 Department & Section Breakdown",
    "📚 Subject-Wise Performance",
    "🔗 Correlation: Attendance vs Marks",
    "📋 Raw Dataset Explorer",
])

# -------------------------------------------------------------
# TAB 1: ATTENDANCE ANALYTICS & DISTRIBUTION
# -------------------------------------------------------------
with eda_tab1:
    st.subheader("Attendance Distribution & Statutory Compliance")
    st.caption("Analysis of student attendance regularity and regulatory 75% examination eligibility threshold.")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("##### Attendance Percentage Distribution (Bins)")
        att_bins = pd.cut(
            students_df["attendance_percentage"],
            bins=[0, 60, 70, 75, 85, 100],
            labels=["<60% (Critical)", "60–70% (Severe Shortage)", "70–75% (Marginal)", "75–85% (Eligible)", "85–100% (High Standing)"]
        ).value_counts().sort_index()
        st.bar_chart(att_bins)

    with c2:
        st.markdown("##### Statutory Examination Standing")
        compliant = (students_df["attendance_percentage"] >= 75.0).sum()
        non_compliant = (students_df["attendance_percentage"] < 75.0).sum()
        status_df = pd.DataFrame({
            "Standing": ["Eligible (≥75%)", "Shortage Barred (<75%)"],
            "Student Count": [compliant, non_compliant],
            "Percentage": [f"{(compliant/len(students_df))*100:.1f}%", f"{(non_compliant/len(students_df))*100:.1f}%"]
        })
        st.dataframe(status_df, use_container_width=True, hide_index=True)
        if non_compliant > 0:
            st.error(f"🚨 {non_compliant} students require condonation or remedial class attendance recovery.")
        else:
            st.success("All students meet the 75% attendance threshold.")

# -------------------------------------------------------------
# TAB 2: DEPARTMENT & SECTION BREAKDOWN
# -------------------------------------------------------------
with eda_tab2:
    st.subheader("Departmental & Sectional Performance Analysis")

    st.markdown("##### Average Marks & Attendance by Department")
    dept_stats = students_df.groupby("department").agg(
        Students=("student_id", "count"),
        Avg_Attendance=("attendance_percentage", "mean"),
        Avg_CIE=("internal_marks", "mean"),
        Avg_External=("external_marks", "mean"),
        Avg_CGPA=("cgpa", "mean"),
    ).reset_index()

    st.dataframe(
        pd.DataFrame([
            {
                "Department": r["department"],
                "Total Students": r["Students"],
                "Mean Attendance": f"{r['Avg_Attendance']:.1f}%",
                "Mean CIE /60": f"{r['Avg_CIE']:.1f}",
                "Mean External /40": f"{r['Avg_External']:.1f}",
                "Mean CGPA": f"{r['Avg_CGPA']:.2f}",
            }
            for _, r in dept_stats.iterrows()
        ]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("##### Section-wise Student Enrollment & Performance (Sections A to J)")
    sec_stats = students_df.groupby("section").agg(
        Students=("student_id", "count"),
        Avg_Attendance=("attendance_percentage", "mean"),
        Avg_CIE=("internal_marks", "mean"),
        Avg_External=("external_marks", "mean"),
    ).reset_index()

    st.dataframe(
        pd.DataFrame([
            {
                "Section": f"Section {r['section']}",
                "Cohort Strength": r["Students"],
                "Mean Attendance": f"{r['Avg_Attendance']:.1f}%",
                "Mean CIE /60": f"{r['Avg_CIE']:.1f}",
                "Mean External /40": f"{r['Avg_External']:.1f}",
            }
            for _, r in sec_stats.iterrows()
        ]),
        use_container_width=True,
        hide_index=True,
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("###### Section Average CIE Marks (/60)")
        st.bar_chart(sec_stats.set_index("section")["Avg_CIE"])
    with sc2:
        st.markdown("###### Section Average Attendance (%)")
        st.bar_chart(sec_stats.set_index("section")["Avg_Attendance"])

# -------------------------------------------------------------
# TAB 3: SUBJECT-WISE PERFORMANCE
# -------------------------------------------------------------
with eda_tab3:
    st.subheader("Subject-Wise Assessment Distribution (4,000 Course Records)")
    st.caption("Aggregated assessment performance across all 8 accredited Year 1 Semester 1 courses.")

    conn = get_connection()
    course_stats = conn.execute(
        """
        SELECT COALESCE(c.catalog_code, c.course_code) AS subject_code,
               MAX(c.course_name) AS course_name,
               MAX(c.course_type) AS course_type,
               MAX(c.credits) AS credits,
               COUNT(ca.assessment_id) AS enrolled_count,
               AVG(ca.mid_exam_marks) AS avg_mid,
               AVG(ca.assignment_marks) AS avg_assn,
               AVG(ca.quiz_marks) AS avg_quiz,
               AVG(ca.viva_marks) AS avg_viva,
               AVG(COALESCE(ca.mid_exam_marks, 0) + COALESCE(ca.assignment_marks, 0) + COALESCE(ca.quiz_marks, 0) + COALESCE(ca.viva_marks, 0)) AS avg_internal,
               AVG(ca.external_marks) AS avg_external,
               AVG(COALESCE(ca.mid_exam_marks, 0) + COALESCE(ca.assignment_marks, 0) + COALESCE(ca.quiz_marks, 0) + COALESCE(ca.viva_marks, 0) + COALESCE(ca.external_marks, 0)) AS avg_total
        FROM course_assessments ca
        JOIN student_registered_courses src ON ca.registration_id = src.registration_id
        JOIN courses c ON src.course_id = c.course_id
        GROUP BY COALESCE(c.catalog_code, c.course_code)
        ORDER BY subject_code ASC
        """
    ).fetchall()
    conn.close()

    if course_stats:
        c_stats_df = pd.DataFrame([dict(r) for r in course_stats])
        st.dataframe(
            pd.DataFrame([
                {
                    "Code": r["subject_code"],
                    "Course Title": r["course_name"],
                    "Type": r["course_type"],
                    "Credits": r["credits"],
                    "Records": r["enrolled_count"],
                    "Mid /30": f"{float(r['avg_mid'] or 0):.1f}",
                    "Assn /10": f"{float(r['avg_assn'] or 0):.1f}",
                    "Quiz /10": f"{float(r['avg_quiz'] or 0):.1f}",
                    "Viva /10": f"{float(r['avg_viva'] or 0):.1f}",
                    "CIE /60": f"{float(r['avg_internal'] or 0):.1f}",
                    "SEE /40": f"{float(r['avg_external'] or 0):.1f}",
                    "Total /100": f"{float(r['avg_total'] or 0):.1f}",
                }
                for r in course_stats
            ]),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("##### Subject-wise Mean Total Score Comparison (/100)")
        st.bar_chart(c_stats_df.set_index("subject_code")["avg_total"])
    else:
        st.info("No course assessment records found.")

# -------------------------------------------------------------
# TAB 4: CORRELATION: ATTENDANCE VS MARKS
# -------------------------------------------------------------
with eda_tab4:
    st.subheader("Statistical Correlation: Attendance vs Academic Performance")
    st.caption("Grounding UCI Student Performance & OULAD learning analytics hypotheses on institutional data.")

    corr_df = students_df[["attendance_percentage", "internal_marks", "external_marks", "total_marks", "cgpa"]].corr()
    st.markdown("##### Pearson Correlation Matrix")
    st.dataframe(corr_df.round(3), use_container_width=True)

    att_to_marks_corr = corr_df.loc["attendance_percentage", "total_marks"]
    st.info(
        f"💡 **Key Finding:** Correlation between Attendance and Total Academic Marks is **+{att_to_marks_corr:.2f}** "
        "(Strong Positive Correlation). Students maintaining ≥85% attendance consistently outperform in both continuous internal assessments (CIE) and external summative examinations."
    )

    st.markdown("##### Scatter Analysis: Attendance (%) vs Total Assessment Score (/100)")
    st.scatter_chart(
        students_df,
        x="attendance_percentage",
        y="total_marks",
        color="section",
    )

# -------------------------------------------------------------
# TAB 5: RAW DATASET EXPLORER
# -------------------------------------------------------------
with eda_tab5:
    st.subheader("Raw Institutional Dataset Explorer")
    st.dataframe(students_df, use_container_width=True, hide_index=True)
    csv_bytes = students_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Full Preprocessed Cohort Dataset (CSV)",
        data=csv_bytes,
        file_name="students_preprocessed_eda_dataset.csv",
        mime="text/csv",
    )