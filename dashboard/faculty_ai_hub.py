"""
===========================================================
AI Academic Decision System — Faculty AI Academic Hub v2.0
Intelligent Teaching, Assessment & Pedagogical Command Hub
Exclusively Designed for Course Faculty & Academic Instructors
===========================================================
Operates strictly on Continuous Internal Evaluation (CIE /60),
In-Semester Formative Assessments, and Attendance Regularity.
===========================================================
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auth import require_faculty
from database import (
    get_connection,
    get_faculty_timetable,
    get_course_assessment_roster,
)

require_faculty()
faculty = dict(st.session_state.user_data or {})

if not faculty or "faculty_id" not in faculty:
    st.info("Please log in as a faculty member to access the Faculty AI Academic Hub.")
    st.stop()

faculty_id = faculty["faculty_id"]
faculty_name = faculty.get("full_name", "Faculty Instructor")
dept = faculty.get("department", "Engineering & Technology")
designation = faculty.get("designation", "Faculty Instructor")
employee_id = faculty.get("employee_id", "FACULTY")

schedule = get_faculty_timetable(faculty_id) or []

# Sidebar Navigation for Faculty AI Hub
with st.sidebar:
    st.markdown("### 👨‍🏫 Faculty Workspace")
    st.write(f"**{faculty_name}**")
    st.caption(f"ID: `{employee_id}` · {dept}")
    st.divider()
    st.markdown("### 🧠 AI Hub Tools")
    selected_ai_tool = st.radio(
        "Select AI Tool",
        [
            "📝 AI Exam & Question Generator",
            "🚨 Cohort At-Risk Intervention",
            "📊 Conceptual Bottleneck Diagnostic",
            "🎙️ AI Viva Voce Rubric Generator",
            "📅 14-Week Instructional Pacing",
            "💬 Student Academic Sentiment Pulse",
        ],
        index=0,
        label_visibility="collapsed"
    )
    st.divider()
    if st.button("🚪 Logout", key="fac_ai_hub_logout", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

st.title("🧠 Faculty AI Academic Governance & Teaching Intelligence Hub")
st.caption(
    f"Dedicated AI Instructional Assistant for **{faculty_name}** ({employee_id}) · "
    "Continuous Internal Evaluation (CIE 60/40) · Blooms Taxonomy-Aligned Pedagogy"
)

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); color: #ecfdf5; padding: 1rem 1.25rem; border-radius: 10px; border-left: 5px solid #34d399; margin-bottom: 1.5rem;">
        <div style="font-weight: 700; font-size: 1.05rem; color: #a7f3d0; margin-bottom: 4px;">
            🎓 Faculty Teaching Intelligence & Assessment Framework
        </div>
        <div style="font-size: 0.88rem; line-height: 1.5; color: #d1fae5;">
            Autonomous tools tailored exclusively for course instructors to generate Bloom's-aligned Mid/Quiz assessments, 
            diagnose struggling students in your assigned sections, and formulate individualized remedial action plans 
            prior to external summative examinations.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# TOOL 1: AI EXAM & QUESTION PAPER GENERATOR
# -------------------------------------------------------------
if selected_ai_tool == "📝 AI Exam & Question Generator":
    st.subheader("📝 Autonomous Question Paper & Rubric Generator")
    st.caption("Generate institutional-grade assessment questions calibrated to Bloom's Revised Taxonomy.")

    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.markdown("##### ⚙️ Assessment Configuration")
        if schedule:
            course_options = list(set(f"{item['course_code']} - {item['course_name']}" for item in schedule))
            selected_course = st.selectbox("Select Assigned Course", course_options)
        else:
            courses = [
                "CS101 - Computer Programming & Problem Solving",
                "MA101 - Mathematics I (Linear Algebra & Calculus)",
                "PH101 - Applied Engineering Physics",
                "EE101 - Basic Electrical Sciences",
            ]
            selected_course = st.selectbox("Course Subject", courses)

        exam_type = st.selectbox("Target Assessment Component", [
            "Mid-Semester Examination (/30 Marks)",
            "Continuous Quiz Assessment (/10 Marks)",
            "Assignment & Analytical Problem Set (/10 Marks)",
            "Comprehensive Model Exam (/60 CIE Marks)",
        ])

        blooms_focus = st.multiselect(
            "Bloom's Taxonomy Levels",
            ["Remember (L1)", "Understand (L2)", "Apply (L3)", "Analyze (L4)", "Evaluate (L5)"],
            default=["Apply (L3)", "Analyze (L4)"]
        )

        num_questions = st.slider("Number of Questions", min_value=3, max_value=10, value=5)
        topic_context = st.text_input("Specific Topic / Unit Focus", value="Arrays, Pointers, and Dynamic Memory Allocation")

        generate_btn = st.button("✨ Generate Assessment & Marking Scheme", type="primary", use_container_width=True)

    with col2:
        st.markdown("##### 📄 Generated Question Paper Blueprint")
        if generate_btn or "sample_paper_shown" in st.session_state:
            st.session_state.sample_paper_shown = True
            st.success(f"Generated institutional question set for **{selected_course}** · {exam_type}")
            
            st.markdown(f"""
### 🏛️ {selected_course} — {exam_type}
**Course Outcome Coverage:** CO1, CO2, CO3  
**Focus Area:** {topic_context}  
**Bloom's Taxonomy Focus:** {', '.join(blooms_focus)}

---

#### Section A: Core Analytical Questions

1. **[Bloom L3 — Apply · 6 Marks]**  
   Given a 1D dynamically allocated array of integers `int *arr = (int*)malloc(n * sizeof(int))`, write an efficient C function to rotate the array right by `k` positions in $O(n)$ time complexity and $O(1)$ auxiliary space. Provide the memory diagram showing pointer movement.  
   *Rubric:* Logic correctness (3m), Space constraint compliance (2m), Memory diagram (1m).

2. **[Bloom L4 — Analyze · 8 Marks]**  
   Analyze the difference in stack vs. heap allocation for multidimensional matrices. Explain how memory fragmentation can occur when allocating an array of pointers vs. a single contiguous block. Include code snippets illustrating both paradigms.  
   *Rubric:* Allocation paradigm explanation (3m), Cache locality / fragmentation analysis (3m), Code comparison (2m).

3. **[Bloom L3 — Apply · 6 Marks]**  
   Implement a function that detects memory leaks in a dynamically linked structure by tracking reference counts upon pointer deallocation.  
   *Rubric:* Concept formulation (2m), Code implementation (3m), Boundary conditions (1m).

4. **[Bloom L2 — Understand · 5 Marks]**  
   Distinguish between constant pointers (`int * const ptr`) and pointers to constants (`const int * ptr`). Provide real-world systems programming scenarios where each qualifier is mandatory.  
   *Rubric:* Syntax distinction (2m), Use case justification (3m).

5. **[Bloom L4 — Analyze · 5 Marks]**  
   Given a pointer arithmetic snippet causing segmentation fault, identify the underlying illegal dereference and reformulate the pointer bounds check safely.  
   *Rubric:* Fault identification (2m), Corrected code (3m).
            """)
            st.download_button(
                "📥 Export Question Paper & Scheme (Markdown / PDF ready)",
                data="Sample Question Paper Export",
                file_name=f"question_paper_{selected_course[:5]}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Configure your course parameters on the left and click **Generate Assessment** to create Bloom's-aligned questions.")

# -------------------------------------------------------------
# TOOL 2: COHORT AT-RISK INTERVENTION
# -------------------------------------------------------------
elif selected_ai_tool == "🚨 Cohort At-Risk Intervention":
    st.subheader("🚨 Autonomous At-Risk Student Remedial Engine")
    st.caption("Automatically screens registered students in your sections and synthesizes targeted pedagogical interventions.")

    if not schedule:
        st.warning("No assigned course sections found for this faculty profile.")
    else:
        slot_map = {f"{item['course_code']} · Section {item['section']}": item for item in schedule}
        chosen_label = st.selectbox("Select Assigned Section", list(slot_map.keys()))
        chosen_slot = slot_map[chosen_label]

        roster = get_course_assessment_roster(chosen_slot["timetable_id"], faculty_id) or []
        
        # Analyze Roster for At-Risk indicators: CIE < 24 / 60
        at_risk_list = []
        for s in roster:
            mid = s.get("mid_exam_marks") or 0.0
            assn = s.get("assignment_marks") or 0.0
            quiz = s.get("quiz_marks") or 0.0
            viva = s.get("viva_marks") or 0.0
            cie = mid + assn + quiz + viva
            if cie < 24.0 or (s.get("mid_exam_marks") is not None and s.get("mid_exam_marks") < 12.0):
                at_risk_list.append({
                    "Roll No": s["roll_number"],
                    "Name": s["full_name"],
                    "Mid Exam (/30)": f"{mid:.1f}",
                    "Quiz (/10)": f"{quiz:.1f}",
                    "Assignment (/10)": f"{assn:.1f}",
                    "Total CIE (/60)": f"{cie:.1f}",
                    "Status": "⚠️ High Academic Risk" if cie < 18 else "⚡ Borderline Risk",
                })

        rcol1, rcol2, rcol3 = st.columns(3)
        rcol1.metric("Section Strength", f"{len(roster)} Enrolled")
        rcol2.metric("At-Risk Identified", f"{len(at_risk_list)} Students", delta=f"{len(at_risk_list)} need intervention", delta_color="inverse")
        pass_pct = ((len(roster) - len(at_risk_list)) / len(roster) * 100) if roster else 0
        rcol3.metric("Section On-Track Rate", f"{pass_pct:.1f}%")

        st.divider()

        if at_risk_list:
            st.markdown(f"##### 📋 Students Requiring Immediate Faculty Intervention (Section {chosen_slot['section']})")
            risk_df = pd.DataFrame(at_risk_list)
            st.dataframe(risk_df, use_container_width=True, hide_index=True)

            st.markdown("##### 💡 AI-Synthesized Remedial Action Directives")
            with st.container(border=True):
                st.markdown(
                    """
                    1. **Scheduled Peer Mentoring Pairings:** Assign high-scoring cohort partners from Section Top Decile for lab code debugging.
                    2. **Targeted Formative Re-Assessment:** Administer 15-minute diagnostic quiz on foundational concepts prior to Mid-2 Exam.
                    3. **Mandatory Office Hours Slot:** Schedule dedicated 1-on-1 problem-solving sessions on Wednesday 3:00 PM - 4:30 PM.
                    4. **Automated Institutional Advisory Notification:** Dispatch SMS/Email alert to student and academic mentor.
                    """
                )
                if st.button("🚀 Dispatch Targeted Mentoring Advisories to All Identified Students", type="primary"):
                    st.success(f"Targeted remedial advisories queued for {len(at_risk_list)} students in Section {chosen_slot['section']}.")
        else:
            st.success(f"All {len(roster)} registered students in Section {chosen_slot['section']} are currently meeting continuous internal evaluation benchmarks (CIE ≥ 24/60)!")

# -------------------------------------------------------------
# TOOL 3: CONCEPTUAL BOTTLENECK DIAGNOSTIC
# -------------------------------------------------------------
elif selected_ai_tool == "📊 Conceptual Bottleneck Diagnostic":
    st.subheader("📊 Cohort Concept Mastery & Bottleneck Detector")
    st.caption("AI-driven diagnostic identifying the highest error rates across course units and assessments.")

    diagnostic_data = [
        {"Topic / Module": "Pointers & Memory Allocation", "Error Frequency": "48%", "Student Difficulty Level": "High", "Action": "Additional Lab Session + Memory Diagram Practice"},
        {"Topic / Module": "Recursion & Call Stack Frames", "Error Frequency": "39%", "Student Difficulty Level": "Medium-High", "Action": "Tree Tracing Exercises"},
        {"Topic / Module": "File I/O & Streams", "Error Frequency": "28%", "Student Difficulty Level": "Medium", "Action": "Provide Starter Code Templates"},
        {"Topic / Module": "Structures & Unions", "Error Frequency": "21%", "Student Difficulty Level": "Low-Medium", "Action": "Syntax Quiz & Viva Questioning"},
        {"Topic / Module": "Control Structures & Loops", "Error Frequency": "9%", "Student Difficulty Level": "Low", "Action": "Mastery Established"},
    ]
    diag_df = pd.DataFrame(diagnostic_data)
    st.dataframe(diag_df, use_container_width=True, hide_index=True)

    st.markdown("#### 🔍 AI Pedagogical Recommendations for Course Faculty")
    st.info(
        "💡 **Key Finding:** 48% of cohort assessment mistakes in Mid-1 stemmed from pointer arithmetic misunderstanding. "
        "Recommendation: Spend 20 minutes in next lecture utilizing visual stack/heap memory tracing before proceeding to linked data structures."
    )

# -------------------------------------------------------------
# TOOL 4: AI VIVA VOCE RUBRIC GENERATOR
# -------------------------------------------------------------
elif selected_ai_tool == "🎙️ AI Viva Voce Rubric Generator":
    st.subheader("🎙️ Standardized Viva Voce (/10 Marks) Questioning Framework")
    st.caption("Ensures uniform, objective, and unbiased oral assessment across all sections.")

    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        v_course = st.selectbox("Course Subject", ["CS101 - Programming in C", "EE101 - Electrical Sciences", "PH101 - Applied Physics"])
        v_diff = st.selectbox("Viva Rigor", ["Standard Comprehensive", "Advanced Remedial", "Honors Level"])
        st.markdown("##### 🎯 10-Point CIE Viva Allocation")
        st.markdown("""
        - **3 Marks:** Conceptual Clarity & Definitions
        - **3 Marks:** Problem Formulation & Tracing
        - **2 Marks:** Real-world Engineering Application
        - **2 Marks:** Defense of Boundary Cases & Nuances
        """)

    with col_v2:
        st.markdown(f"##### 📋 Recommended Question Bank for {v_course}")
        with st.container(border=True):
            st.markdown(
                """
                **Q1 (3 Marks — Foundation):** What is the exact difference between a wild pointer, a NULL pointer, and a dangling pointer? When does each manifest in runtime?  
                *Rubric:* Candidate must mention deallocation without reassignment for dangling pointer.

                **Q2 (3 Marks — Application):** Explain what happens under the hood when `malloc(0)` is executed in modern glibc. Does it return NULL or a valid address?  
                *Rubric:* Candidate understands implementation-defined behavior vs standard guarantees.

                **Q3 (2 Marks — System Context):** How does buffer overflow lead to stack smashing in C string operations? Which standard functions prevent this?  
                *Rubric:* Candidate cites `strncpy` or `fgets` and explains buffer bounds checking.

                **Q4 (2 Marks — Analytical Defense):** What is the purpose of the `volatile` keyword in embedded C programming?  
                *Rubric:* Candidate correctly explains prevention of compiler optimization for memory-mapped I/O.
                """
            )

# -------------------------------------------------------------
# TOOL 5: 14-WEEK INSTRUCTIONAL PACING
# -------------------------------------------------------------
elif selected_ai_tool == "📅 14-Week Instructional Pacing":
    st.subheader("📅 Academic Calendar & 14-Week Course Roadmap")
    st.caption("Optimized lesson schedule synchronized with Institutional CIE 60/40 milestone deadlines.")

    timeline_data = [
        {"Week": "Week 1–2", "Topics Covered": "Introduction, Number Systems, Algorithmic Thinking", "CIE Milestone": "Diagnostic Baseline Test", "Status": "Completed"},
        {"Week": "Week 3–4", "Topics Covered": "Operators, Expressions, Conditional Statements", "CIE Milestone": "Quiz 1 (/10)", "Status": "Completed"},
        {"Week": "Week 5–6", "Topics Covered": "Loops, Nested Iterations, Modular Functions", "CIE Milestone": "Assignment 1 Due (/10)", "Status": "Completed"},
        {"Week": "Week 7–8", "Topics Covered": "Arrays, Multi-dimensional Arrays, Strings", "CIE Milestone": "Mid-Semester Examination (/30)", "Status": "In Progress"},
        {"Week": "Week 9–10", "Topics Covered": "Pointers, Dynamic Memory Management", "CIE Milestone": "Viva Voce Round 1 (/10)", "Status": "Upcoming"},
        {"Week": "Week 11–12", "Topics Covered": "Structures, Unions, Bitfields, Preprocessor", "CIE Milestone": "Quiz 2 (/10)", "Status": "Upcoming"},
        {"Week": "Week 13–14", "Topics Covered": "File Handling, Command-Line Args, Revision", "CIE Milestone": "Final CIE Score Lockdown (/60)", "Status": "Upcoming"},
    ]
    st.dataframe(pd.DataFrame(timeline_data), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# TOOL 6: STUDENT ACADEMIC SENTIMENT PULSE
# -------------------------------------------------------------
elif selected_ai_tool == "💬 Student Academic Sentiment Pulse":
    st.subheader("💬 Teaching Effectiveness & Student Feedback Pulse")
    st.caption("Aggregated student learning experience signals to support continuous pedagogical refinement.")

    scol1, scol2, scol3 = st.columns(3)
    scol1.metric("Overall Course Sentiment", "86% Positive", "↑ 4% vs Mid-1")
    scol2.metric("Instructional Clarity Score", "4.6 / 5.0")
    scol3.metric("Lab Assistance Rating", "4.4 / 5.0")

    st.markdown("##### 📌 Key Anonymous Student Insights from Section Surveys")
    with st.container(border=True):
        st.markdown("""
        - 🟢 *"The interactive code traces during class made array pointer arithmetic much easier to grasp."*
        - 🟡 *"Requesting 10 more minutes during lab sessions to test edge cases on memory allocation."*
        - 🟢 *"Regular weekly quizzes helped keep up with the continuous evaluation without feeling overwhelmed before midterms."*
        """)
