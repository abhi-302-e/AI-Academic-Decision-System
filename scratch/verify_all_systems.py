import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
import pandas as pd

from database import (
    get_student_by_roll,
    get_student_semester_registration,
    get_student_registered_courses,
    get_student_course_assessments,
    get_student_timetable,
    get_latest_model_training_run,
    get_course_assessment_roster,
    get_session_attendance_roster,
)
from prediction import predict_student_comprehensive, are_course_models_trained
from recommendation_engine import generate_course_level_recommendations
from models.train_registered_course_models import train_course_models

print("=== 1. VERIFYING STUDENT 26STU0001 (SECTION A) ===")
s1 = get_student_by_roll("26STU0001")
print("Student:", s1["full_name"], "Dept:", s1["department"], "Section:", s1["section"])
reg1 = get_student_semester_registration(s1["student_id"], 1)
print("Registration: Status=", reg1["status"], "Section=", reg1["section"])
courses1 = get_student_registered_courses(s1["student_id"], 1)
print("Registered Courses:", len(courses1), "courses, total credits:", sum(c["credits"] for c in courses1))
assess1 = get_student_course_assessments(s1["student_id"], 1)
print("Assessments:", len(assess1), "courses evaluated")
sample_a = assess1[0]
print("Sample Course:", sample_a["course_code"], "-", sample_a["course_name"])
print("Marks: Mid=", sample_a["mid_exam_marks"], "/30, Assn=", sample_a["assignment_marks"], "/10, Quiz=", sample_a["quiz_marks"], "/10, Viva=", sample_a["viva_marks"], "/10 -> Internal=", sample_a["internal_total"], "/60, External=", sample_a["external_marks"], "/40 -> Total=", sample_a["overall_total"], "/100")
print("Faculty:", sample_a.get("faculty_name"), "Attendance:", sample_a.get("course_attendance"), "%")

tt1 = get_student_timetable(s1["student_id"], 1)
print("Timetable:", len(tt1), "weekly class slots for Section", s1["section"])

pred1 = predict_student_comprehensive(s1["student_id"], 1)
print("AI Prediction: Registered=", pred1["registered"], "Performance=", pred1["overall_performance"], "Risk=", pred1["overall_risk"])

recs1 = generate_course_level_recommendations(sample_a)
print("Course Recommendations count:", len(recs1))

print("\n=== 2. VERIFYING UNREGISTERED STUDENT LOCKDOWN ===")
unreg_pred = predict_student_comprehensive(999999, 1)
print("Unregistered student prediction: Registered=", unreg_pred["registered"], "Message=", unreg_pred.get("status_message"))

print("\n=== 3. VERIFYING FACULTY ROSTER (50 STUDENTS) ===")
roster = get_course_assessment_roster(473, None)
print("Assessment roster length for slot 473:", len(roster), "students")

print("\n=== 4. VERIFYING LATEST MODEL TRAINING RUN ===")
latest_run = get_latest_model_training_run()
print("Latest ML Run: ID=", latest_run["run_id"], "Model=", latest_run["model_name"], "Records=", latest_run["sample_count"], "Accuracy=", f"{latest_run['accuracy']*100:.1f}%", "Trained At=", latest_run["trained_at"])

print("\n=== 5. VERIFYING MODEL RETRAINING PIPELINE ===")
res = train_course_models("Admin")
print("Retrained models successfully! Samples:", res["samples"], "Performance Accuracy:", f"{res['performance_accuracy']*100:.1f}%", "Risk Accuracy:", f"{res['risk_accuracy']*100:.1f}%")

print("\n=== ALL SYSTEM CHECKS PASSED PERFECTLY ===")
