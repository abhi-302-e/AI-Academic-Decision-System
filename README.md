# AI-Based Autonomous Academic Decision System

**Domain:** Artificial Intelligence + Machine Learning + Data Analytics  
**Real-World Application:** Self-Learning ERP Intelligence  
**Theme:** AI Academic Governance  
**Faculty Guides:** Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri  
**Institution:** The ICFAI Foundation for Higher Education (IFHE), Faculty of Science & Technology (FST), Hyderabad  

---

## 📌 Executive Summary & Problem Statement

Educational institutions collect large volumes of academic data, including attendance logs, continuous internal assessments, laboratory sessions, assignment submissions, LMS clickstream activities, and student feedback. However, academic governance and intervention decisions are predominantly made manually or post-facto—often after end-semester examinations when it is too late to rescue failing students.

This project delivers an **AI-Based Autonomous Academic Decision System** directly integrated into an institutional ERP workflow. The system features:
1. **Realistic Academic Structure:** 500 Year 1 Semester 1 students realigned across 10 balanced sections (**Sections A through J**, capped at 50 students each) enrolled in an accredited 20-credit curriculum (8 courses).
2. **Strict ERP Semester Registration Enforcement:** Unregistered students cannot have internal marks, external marks, timetable sessions, or AI predictions.
3. **Institutional 60/40 Evaluation Model:** 60 Internal Continuous Evaluation marks (Mid 30, Assignment 10, Quiz 10, Viva 10) + 40 External End-Semester marks = 100 Total marks.
4. **Role-Based Governance Permissions:** Course faculty members are strictly authorized to enter marks and record session attendance only for their assigned courses and section rosters.
5. **Multi-Dataset Benchmarking:** Sourced and synthesized from 4 foundational benchmarks:
   - **Kaggle Student Performance Dataset**
   - **UCI Student Performance Dataset (Cortez & Silva)**
   - **Open University Learning Analytics Dataset (OULAD)**
   - **Synthetic Institutional ERP Dataset (4,000 course assessments)**
6. **Machine Learning Intelligence:** Dual Random Forest ensembles achieving **97.4% accuracy** on Student Performance Prediction (*Distinction / Pass / Fail*) and **99.0% accuracy** on Academic Risk Detection (*Low / Medium / High Risk*).
7. **Student ERP Portal:** Modeled after the **ICFAI Foundation for Higher Education** student portal, providing timetable matrix schedules, attendance ledgers with 75% UGC shortage warning calculators, 60/40 gradebook visualizers, and targeted interventions.

---

## 🏗️ End-to-End System Architecture

```text
+-----------------------------------------------------------------------------------+
|                        INSTITUTIONAL ERP DATABASE (SQLite)                        |
|  500 Enrolled Students · 10 Sections (A–J, 50/sec) · 8 Year 1 Sem 1 Courses       |
|  Timetable (630 weekly slots) · 4,000 Assessments · 2,400 Attendance Sessions     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       STRICT ERP REGISTRATION GATEKEEPER                          |
|  Verifies formal semester registration before granting access to:                 |
|  • Continuous Internal Evaluation (60)  • External End-Semester Marks (40)        |
|  • Timetable Sessions & Attendance      • AI Academic Predictions                 |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     DATA PREPROCESSING & FEATURE SYNTHESIS                        |
|  Synthesizes 4 Foundational Benchmark Datasets:                                   |
|  1. Kaggle: Parental education, study habits, continuous quiz persistence         |
|  2. UCI (Cortez & Silva): G1 (Mid-Term), G2 (CIE Internal), absences, failures    |
|  3. OULAD: VLE interactions, TMA/CMA assessment timeliness, engagement weights     |
|  4. Institutional ERP: 60/40 marks breakdown, 50-student rosters, faculty logs     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                  MACHINE LEARNING ENSEMBLES (Admin ML Center)                     |
|  • Model 1: Student Performance Classifier (Distinction / Pass / Fail) -> 97.4%   |
|  • Model 2: Academic Risk Detection Model (Low / Medium / High Risk)    -> 99.0%   |
|  Holdout Validation: Stratified 80/20 Train-Test Split                            |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           AUTONOMOUS DECISION ENGINE                              |
|  • Generates course-specific interventions and remedial tutorial referrals        |
|  • Flags statutory attendance shortages (< 75% UGC minimum threshold)             |
|  • Recommends advanced learning & honors opportunities for distinction students   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             ROLE-BASED USER INTERFACES                            |
|  🎓 Student Portal (Modeled after ICFAI Foundation for Higher Education ERP)       |
|  👨‍🏫 Faculty Workspace (60/40 CIE marks entry, 50-student attendance rosters)       |
|  🛡️ Admin Console (Multi-dataset ML training center, dataset explorer, audits)    |
|  📊 Phase 3 EDA Analytics & Institutional Governance Reports                      |
+-----------------------------------------------------------------------------------+
```

---

## 📊 Dataset Benchmark Integration

| Dataset | Primary Contribution & Synthesized Features |
|---|---|
| **Kaggle Student Performance Dataset** | Parental education background, weekly study hours, past academic performance, formative quiz persistence patterns. |
| **UCI Student Performance Dataset (Cortez & Silva)** | $G_1$ (Mid-Term /30), $G_2$ (Continuous Internal Evaluation /60), $G_3$ (Final Summative /40), absenteeism tracking, previous course failure history. |
| **Open University Learning Analytics (OULAD)** | Clickstream VLE learning engagement, TMA (Tutor-Marked Assignments) and CMA (Computer-Marked Assessments) timeliness and submission completion rates. |
| **Synthetic Institutional ERP Dataset** | 4,000 real-world course assessments across Sections A–J (50 students/section), 60/40 assessment splits, faculty grading rosters, and 40,000 attendance records. |

---

## 📚 Accredited Curriculum: Year 1 Semester 1 (Batch 2026–27)

All 500 students belong to **Year 1, Semester 1** across CSE, AIML, and AIDS, enrolled in **8 accredited courses totaling 20.0 Credits**:

| Course Code | Course Title | Category | Credits | CIE Max | SEE Max | Total |
|---|---|---|---|---|---|---|
| **MA101** | Linear Algebra and Calculus | Foundation Core | 4.0 | 60 | 40 | 100 |
| **CS101** | Problem Solving and Programming through C | Core Theory | 3.0 | 60 | 40 | 100 |
| **PH101** | Engineering Physics | Basic Science | 3.0 | 60 | 40 | 100 |
| **EE101** | Basic Electrical & Electronics Engineering | Engineering Core | 3.0 | 60 | 40 | 100 |
| **EN101** | Professional Communication | Humanities | 2.0 | 60 | 40 | 100 |
| **CS102** | Computer Programming Laboratory | Practical / Lab | 1.5 | 60 | 40 | 100 |
| **PH102** | Engineering Physics Laboratory | Practical / Lab | 1.5 | 60 | 40 | 100 |
| **ME101** | Engineering Graphics and Design | Practical / Design | 2.0 | 60 | 40 | 100 |
| **TOTAL** | **8 Semester Courses** | **Full Cohort** | **20.0** | **480** | **320** | **800** |

---

## ⚖️ Continuous Internal Evaluation (CIE) 60/40 Scheme

Every course is graded on an institutional **100-mark framework**:
$$\text{Total Course Score (100)} = \text{Internal CIE (60)} + \text{External SEE (40)}$$

```text
+-----------------------------------------------------------------------------------+
|                        COURSE ASSESSMENT SCHEME (100 MARKS)                       |
+---------------------------------------------------+-------------------------------+
|           CONTINUOUS INTERNAL EVALUATION (60)     |  END-SEMESTER EXAMINATION (40)|
+-------------------+---------------+---------------+-------------------------------+
| Mid-Term Exam     | Assignments   | Quizzes       | Viva Voce /   | External Exam |
| (30 Marks)        | (10 Marks)    | (10 Marks)    | Practical     | (40 Marks)    |
|                   |               |               | (10 Marks)    |               |
+-------------------+---------------+---------------+---------------+---------------+
```

### Grade Point & Letter Grade Mapping
- **O (Outstanding):** $\ge 90$ Marks (Grade Point: 10)
- **A+ (Excellent):** $80 - 89$ Marks (Grade Point: 9)
- **A (Very Good):** $70 - 79$ Marks (Grade Point: 8)
- **B+ (Good):** $60 - 69$ Marks (Grade Point: 7)
- **B (Above Average):** $50 - 59$ Marks (Grade Point: 6)
- **C (Pass):** $40 - 49$ Marks (Grade Point: 5)
- **F (Fail):** $< 40$ Marks (Grade Point: 0 — Course Backlog)

---

## 🤖 Machine Learning Models & Holdout Evaluation

The machine learning subsystem features dual ensembles trained directly on complete verified institutional ERP assessments:

### 1. Student Performance Prediction Model
- **Target Variable:** Performance Trajectory (`Distinction`, `Pass`, `Fail`)
- **Algorithm:** Random Forest Classifier (100 estimators, max depth 12, stratified cross-validation)
- **Holdout Test Accuracy:** **97.4%**

### 2. At-Risk Student Detection Model
- **Target Variable:** Academic Risk Classification (`Low Risk`, `Medium Risk`, `High Risk`)
- **Algorithm:** Random Forest Classifier & Logistic Regression
- **Holdout Test Accuracy:** **99.0%**

### Top Predictor Feature Importances (Gini Weight)
1. **Internal CIE Total (/60):** 38.2% weight
2. **Mid-Term Examination Score (/30):** 24.1% weight
3. **Course Attendance Regularity (%):** 16.4% weight
4. **Continuous Assignment Timeliness (/10):** 9.1% weight
5. **Formative Quiz Consistency (/10):** 7.8% weight
6. **Viva Voce & Practical Lab Fluency (/10):** 4.4% weight

---

## 🏛️ Application Modules & Dashboards

### 1. Student Academic Portal (ICFAI IFHE Aesthetic)
*Modeled after the ICFAI Foundation for Higher Education student portal:*
- **Institutional Top Banner:** IFHE branding, student profile chip, roll number, department, section, and active registration badge.
- **Strict Registration Guard:** Unregistered students are prompted with a registration wizard; marks and AI predictions remain strictly locked until registration is completed.
- **Top Quick KPI Bar:** CGPA/SGPA, Attendance % with statutory standing, CIE Internal /60, External /40, Total /100, and AI Risk Radar.
- **7 Comprehensive Tabs:**
  1. `🏛️ Portal Overview`: Student profile card, academic milestone meters, UGC examination compliance, circulars, and Faculty Guides credit.
  2. `📚 Academic Curriculum`: Official registration certificate, 8 accredited courses (20 credits), and section capacity.
  3. `📊 CIE & External Gradebook (60/40)`: Complete course-by-course 60/40 breakdown with interactive component visualizers.
  4. `📅 Timetable & Attendance System`: Weekly section timetable (Mon–Sat, P1–P7) with period timings, room numbers, and faculty; plus course-wise attendance ledger with a **75% UGC shortage warning calculator**.
  5. `🧠 AI Academic Decision Engine`: Displays active model metrics, performance trajectory, risk classification, and course predictions.
  6. `🎯 Targeted Recommendations`: Course-specific interventions, remedial class alerts, VLE/LMS study hour advisories, and viva voce practice guidance.
  7. `🔔 Notifications`: Live alerts with unread counter and mark-as-read functionality.

### 2. Faculty Academic & Evaluation Workspace
- **Course Assessment:** Grade students in assigned timetable slots across Mid /30, Assignment /10, Quiz /10, Viva /10, External /40. Displays full 50-student section roster.
- **Session Attendance:** Mark daily classroom attendance with a 50-student checkbox roster, locking on submit to ensure audit compliance.
- **Student Search & Summary:** Search by Roll Number or Name to view continuous assessment standing and attendance history.
- **At-Risk Student Detection:** Early warning filter for students with attendance < 75% or internal score < 24/60 with automated bulk notification triggers.
- **Section Analytics:** Performance distribution across components, attendance rates, and section comparisons.
- **Teaching Requests:** Submit requests for accredited courses, sections, and 50-minute weekday slots for Admin approval.

### 3. Admin AI Control, ML Training & Academic Governance Suite
The Administrator possesses complete executive control over the machine learning models and academic intervention policies via a 4-tab control center:
- **Tab 1: Train & Retrain ML Models:**
  - **Algorithm Flexibility:** Admin can select between `Random Forest` (bagging ensemble), `Decision Tree` (transparent rule splits), `Gradient Boosting` (sequential boosting), and `Logistic Regression` (linear baseline).
  - **Configurable Hyperparameters:** Adjust number of estimators (50–300 trees), maximum tree depth (unconstrained or capped), and validation holdout split (80/20, 85/15, 75/25, 70/30).
  - **Model Evaluation:** Real-time holdout accuracy metrics (97.4% performance, 99.0% risk), feature importance graphs (attendance, mid-term, assignment, quiz, viva, external), and historical run logs.
- **Tab 2: Recommendation & Risk Policy Controls:**
  - **Master AI Deployment Gate:** Master toggle to enable/pause real-time AI predictions on student and faculty portals.
  - **Institutional Thresholds:** Admin-adjustable sliders for Statutory Attendance Debarment Minimum (60–90%), Continuous Internal Evaluation (CIE) Cutoff (15–35/60), Mid-Term Remedial Cutoff (8–22/30), Formative Assignment Cutoff (3–8/10), Quiz Cutoff (3–8/10), Viva Voce Cutoff (3–8/10), and First Class with Distinction CGPA Minimum (7.0–9.5).
  - **Immediate Propagation:** Changes persist to SQLite `academic_policies` and dynamically recalculate student advisories, remedial flags, and model training labels.
- **Tab 3: Live Simulation & Testing Sandbox:**
  - Interactive simulator enabling the Admin to test any hypothetical student grade combination (Mid /30, Assignment /10, Quiz /10, Viva /10, External /40, Attendance %).
  - Real-time display of predicted performance class (*Distinction / Pass / Fail*), academic risk tier (*Low / Medium / High Risk*), and dynamically generated institutional recommendations and intervention plans.
- **Tab 4: Institutional Dataset Explorer:**
  - Interactive audit of all 4,000 course assessments across Sections A through J.
  - Multi-column filtering by section, course code, risk tier, and performance outcome with summary metrics and one-click CSV export.

### 4. Course & Timetable Management Console (2 Semesters per Academic Year)
- **Annual Academic Structure:** Strictly enforces **2 Semesters per Academic Year** (Semester 1 = Odd / Autumn, Semester 2 = Even / Spring; Year 1: Sem 1 & 2, Year 2: Sem 3 & 4, Year 3: Sem 5 & 6, Year 4: Sem 7 & 8).
- **Course Catalog Control:**
  - Initialize, lock, or unlock semester structures.
  - Add new courses (Course Code, Catalog Code, Title, Credits, Theory/Lab).
  - Edit existing courses (modify course details, credits, or syllabus title).
  - Remove / delete courses from accredited structures.
- **Section Timetable Schedule Control:**
  - Full scheduling authority across all 10 sections (**Sections A through J**).
  - Add new timetable periods: Section, Day (Mon–Sat), Period (P1–P7 with standard timings), Course, Faculty Instructor, Room/Lab.
  - Edit / reschedule existing timetable periods (change room, faculty, or timing).
  - Remove / cancel scheduled timetable slots.
  - Optional bulk Excel timetable workbook upload & ingestion.

### 5. Phase 3 Exploratory Data Analysis (EDA) & Reports
- **Attendance Analytics:** Distribution histograms and 75% statutory compliance breakdown.
- **Department & Section Breakdown:** Comparative metrics across CSE, AIML, AIDS, and Sections A through J.
- **Subject-Wise Analysis:** Performance comparisons across all 8 Year 1 Sem 1 courses.
- **Correlation Engine:** Pearson correlation matrix ($r = +0.81$) demonstrating strong positive correlation between attendance regularity and exam scores.
- **Institutional Reports:** Downloadable dossiers for student performance, at-risk cohorts, section summaries, and course audits.



---

## 🗂️ Project Directory Structure

```text
AcademicDecisionSystem/
│
├── dataset/
│   ├── student.db                   # Primary SQLite database (500 students, 4,000 assessments)
│   ├── student_performance.csv      # Baseline preprocessed student dataset
│   └── *.xlsx                       # Master course curriculum & timetable workbooks
│
├── preprocessing/
│   ├── clean_data.py                # Dataset cleaning & missing value imputation
│   ├── feature_engineering.py       # Behavioral & assessment feature synthesis
│   └── parse_academic_workbooks.py  # Excel timetable & catalog ingest engine
│
├── models/
│   ├── train_registered_course_models.py # Multi-dataset Random Forest trainer
│   ├── course_performance_model.pkl      # Serialized Performance model
│   └── course_risk_model.pkl             # Serialized Risk detection model
│
├── dashboard/
│   ├── student_dashboard.py         # ICFAI IFHE Student Portal (60/40, timetable, AI)
│   ├── faculty_dashboard.py         # Faculty grading, 50-student attendance roster
│   ├── admin_dashboard.py           # Multi-dataset ML training center & explorer
│   ├── analytics.py                 # Phase 3 Exploratory Data Analysis (EDA)
│   ├── reports.py                   # Institutional academic dossiers & reports
│   ├── course_management.py         # Curriculum & timetable publishing
│   ├── student_approvals.py         # Student admission & registration approvals
│   └── login.py                     # Authentication portal
│
├── assets/
│   ├── style.css                    # IFHE institutional CSS & responsive styling
│   ├── logo.png                     # University emblem / institutional branding
│   └── reference_video.mp4          # Reference recording of student portal
│
├── prediction.py                    # Multi-dataset inference engine & registration guard
├── recommendation_engine.py         # Dynamic academic intervention engine
├── database.py                      # Core SQLite database access layer & queries
├── auth.py                          # Role-based authentication & session guards
├── email_service.py                 # Automated academic email notifications
├── sms_service.py                   # Automated SMS alert dispatch
├── app.py                           # Application entry point & navigation router
├── requirements.txt                 # Python dependencies
└── README.md                        # Comprehensive system documentation
```

---

## 📅 Project Phases & 12-Week Implementation Plan

| Week | Phase | Key Activities & Milestones | Status |
|---|---|---|---|
| **1** | Problem Study | Literature review, educational analytics benchmarks, ERP workflows | Completed |
| **2** | Dataset Collection | Kaggle, UCI, OULAD synthesis + 500-student synthetic ERP generation | Completed |
| **3** | Data Cleaning | Imputation, normalization, foreign key integrity across Sections A–J | Completed |
| **4** | Exploratory Data Analysis | Distribution histograms, section averages, Pearson correlation ($r = +0.81$) | Completed |
| **5** | Performance Modeling | Random Forest Classifier (Pass / Fail / Distinction) -> 97.4% Accuracy | Completed |
| **6** | At-Risk Detection | Risk Classification (Low / Medium / High Risk) -> 99.0% Accuracy | Completed |
| **7** | Decision Engine | Rule-based & ML intervention logic, 75% attendance shortage warnings | Completed |
| **8** | Recommendation Generation | Course-level remediation, faculty mentor advisory plans | Completed |
| **9** | Dashboard Development | ICFAI IFHE Student Portal, Faculty 60/40 grading, Admin console | Completed |
| **10** | Database Integration | Real-time session attendance, 630 timetable slots, registration guard | Completed |
| **11** | Testing & Validation | End-to-end verification, holdout accuracy audits, edge case testing | Completed |
| **12** | Presentation & Documentation | Final code audit, institutional dossiers, and README documentation | Completed |

---

## 🚀 Installation & Local Execution

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Virtual Environment tool (`venv`)

### 1. Setup Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Launch Streamlit Application
```powershell
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🔑 Default Login Credentials

| Role | Username / Identifier | Password | Access & Features |
|---|---|---|---|
| **Student (Section A)** | `26STU0001` | `Password@123` | ICFAI ERP Portal, 60/40 Gradebook, Timetable, AI Radar |
| **Student (Section B)** | `26STU0051` | `Password@123` | Section B Timetable, Gradebook, AI Predictions |
| **Student (Section C)** | `26STU0101` | `Password@123` | Section C Timetable, Gradebook, AI Predictions |
| **Faculty Member** | `SCHED001` | `Faculty@123` | 60/40 Marks Entry, 50-Student Attendance Roster |
| **Administrator** | `admin` | `Admin@123` | Multi-Dataset ML Training Center, Dataset Explorer, Approvals |

---

## 🌐 Live Demo

👉 [Open AI Academic Decision System](https://ai-academic-decision-system.streamlit.app/)


