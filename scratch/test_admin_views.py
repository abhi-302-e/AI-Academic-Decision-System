import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database import (
    get_all_students,
    get_all_faculty,
    get_student_by_roll,
    get_faculty_by_employee_id,
    get_student_registered_courses,
    get_student_course_assessments,
    get_student_timetable,
    get_faculty_timetable,
)
from prediction import predict_student_comprehensive
from recommendation_engine import generate_course_level_recommendations

print("--- Testing View Students Data Pipeline ---")
students_df = get_all_students()
assert not students_df.empty, "Students DataFrame is empty"
print(f"Total students fetched: {len(students_df)}")
sample_student = students_df.iloc[0]
roll = sample_student["roll_number"]
print(f"Testing student detail lookup for: {roll} ({sample_student['full_name']})")

s_rec = get_student_by_roll(roll)
assert s_rec is not None, f"Could not find student {roll}"
assert isinstance(s_rec, dict), "Student record should be a dict"
print(f"Student record keys: {len(s_rec)} fields found")

stu_id = s_rec["student_id"]
sem = s_rec.get("semester") or 1
courses = get_student_registered_courses(stu_id, sem)
assessments = get_student_course_assessments(stu_id, sem)
tt = get_student_timetable(stu_id, sem)
pred = predict_student_comprehensive(stu_id, sem)
print(f"Registered courses: {len(courses)}, Assessments: {len(assessments)}, Timetable: {len(tt)}")
print(f"Prediction: {pred.get('overall_performance')}, Risk: {pred.get('overall_risk')}")

print("\n--- Testing View Faculty Details Data Pipeline ---")
faculty_list = get_all_faculty()
assert len(faculty_list) > 0, "Faculty list is empty"
assert isinstance(faculty_list[0], dict), "Faculty items should be dicts"
print(f"Total faculty members fetched: {len(faculty_list)}")

sample_fac = faculty_list[0]
emp_id = sample_fac["employee_id"]
print(f"Testing faculty detail lookup for: {emp_id} ({sample_fac['full_name']})")

f_rec = get_faculty_by_employee_id(emp_id)
assert f_rec is not None, f"Could not find faculty {emp_id}"
assert isinstance(f_rec, dict), "Faculty record should be a dict"

f_tt = get_faculty_timetable(f_rec["faculty_id"], f_rec["full_name"])
print(f"Faculty timetable slots: {len(f_tt)}")
if f_tt:
    print(f"Sample slot: {f_tt[0]['day']} {f_tt[0]['slot']} - {f_tt[0]['course_code']} ({f_tt[0]['section']})")

print("\nALL ADMIN VIEW PIPELINES PASSED WITH ZERO ERRORS!")
