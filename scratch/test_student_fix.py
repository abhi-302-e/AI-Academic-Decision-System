import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database import (
    get_student_by_roll,
    get_student_semester_registration,
    get_student_registered_courses,
    get_student_course_assessments,
    get_student_timetable,
    get_latest_model_training_run,
    get_academic_policies,
    get_student_notifications,
)
from prediction import predict_student_comprehensive
from recommendation_engine import generate_course_level_recommendations

for roll in ["26STU0004", "26STU0001", "26STU0002"]:
    print(f"=== Testing Roll: {roll} ===")
    student = get_student_by_roll(roll)
    assert student is not None, f"Student {roll} not found"
    student = dict(student)
    student_id = student["student_id"]
    current_year = int(student.get("current_year") or 1)
    current_semester = int(student.get("semester") or 1)
    
    raw_reg = get_student_semester_registration(student_id, current_semester)
    semester_reg = dict(raw_reg) if raw_reg else None
    print(f"Registration: {semester_reg.get('status') if semester_reg else 'None'}")
    
    registered_courses = [dict(c) for c in (get_student_registered_courses(student_id, current_semester) or [])]
    course_assessments = [dict(a) for a in (get_student_course_assessments(student_id, current_semester) or [])]
    student_timetable = [dict(t) for t in (get_student_timetable(student_id, current_semester) or [])]
    latest_model_run = get_latest_model_training_run()
    academic_policies = get_academic_policies()
    predictions_enabled = bool(academic_policies.get("predictions_enabled", 1))
    
    comprehensive_pred = predict_student_comprehensive(student_id, current_semester)
    total_credits = sum(float(c.get("credits") or 0) for c in registered_courses) if registered_courses else 20.0
    print(f"Total credits: {total_credits}, Registered courses count: {len(registered_courses)}")
    print(f"Overall perf: {comprehensive_pred.get('overall_performance')}, Overall risk: {comprehensive_pred.get('overall_risk')}")
    print(f"Course assessments count: {len(course_assessments)}")
    print(f"Timetable count: {len(student_timetable)}")
    
    # Test recommendations
    for ca in course_assessments:
        recs = generate_course_level_recommendations(ca, policies=academic_policies)
        assert isinstance(recs, list)
    print(f"SUCCESS: All checks passed for {roll}\n")

print("ALL STUDENTS VERIFIED FLAWLESSLY!")
