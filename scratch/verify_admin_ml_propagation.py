import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from models.train_registered_course_models import train_course_models, get_latest_model_evaluation
from prediction import predict_student_comprehensive
from recommendation_engine import generate_course_level_recommendations
from database import get_student_course_assessments, get_academic_policies, update_academic_policies

def test_pipeline():
    print("=== Step 1: Initial Training with Standard 75% Attendance & 40 Passing Cutoff ===")
    res1 = train_course_models(
        algorithm="Random Forest",
        n_estimators=100,
        attendance_threshold=75.0,
        critical_score=40.0,
        critical_internal_threshold=24.0,
        trained_by="Admin_Test"
    )
    eval1 = get_latest_model_evaluation()
    print(f"Algorithm: {eval1.get('algorithm')}")
    print(f"Attendance Cutoff: {eval1.get('attendance_threshold')}%")
    print(f"Perf Accuracy: {eval1.get('performance_accuracy'):.3f}")
    print(f"Risk Accuracy: {eval1.get('risk_accuracy'):.3f}")
    print(f"Performance Confusion Matrix:\n{eval1.get('performance_confusion_matrix')}")
    print(f"Risk Confusion Matrix:\n{eval1.get('risk_confusion_matrix')}")

    # Check Student 1 predictions
    pred1 = predict_student_comprehensive(1, semester=1)
    print(f"\nStudent 1 Initial -> Overall Perf: {pred1.get('overall_performance')}, Overall Risk: {pred1.get('overall_risk')}")
    ca1 = get_student_course_assessments(1, semester=1)
    if ca1:
        recs1 = generate_course_level_recommendations(dict(ca1[0]), policies=get_academic_policies())
        print(f"Student 1 Course 0 Recs count: {len(recs1)}")
        for r in recs1:
            print(f"  - [{r.get('category')} / {r.get('priority')}]: {r.get('text')}")

    print("\n=== Step 2: Admin Retrains with Stricter Criteria: 85% Attendance & 50 Passing Cutoff & Gradient Boosting ===")
    update_academic_policies({
        "attendance_threshold": 85.0,
        "critical_internal_threshold": 28.0,
        "active_ml_algorithm": "Gradient Boosting",
    })
    res2 = train_course_models(
        algorithm="Gradient Boosting",
        n_estimators=100,
        attendance_threshold=85.0,
        critical_score=50.0,
        critical_internal_threshold=28.0,
        trained_by="Admin_Strict"
    )
    eval2 = get_latest_model_evaluation()
    print(f"Updated Algorithm: {eval2.get('algorithm')}")
    print(f"Updated Attendance Cutoff: {eval2.get('attendance_threshold')}%")
    print(f"Updated Perf Accuracy: {eval2.get('performance_accuracy'):.3f}")
    print(f"Updated Risk Accuracy: {eval2.get('risk_accuracy'):.3f}")
    print(f"Updated Performance Confusion Matrix:\n{eval2.get('performance_confusion_matrix')}")
    print(f"Updated Risk Confusion Matrix:\n{eval2.get('risk_confusion_matrix')}")

    pred2 = predict_student_comprehensive(1, semester=1)
    print(f"\nStudent 1 After Admin Retrain -> Overall Perf: {pred2.get('overall_performance')}, Overall Risk: {pred2.get('overall_risk')}")
    if ca1:
        recs2 = generate_course_level_recommendations(dict(ca1[0]), policies=get_academic_policies())
        print(f"Student 1 Course 0 Recs count (under 85% cutoff): {len(recs2)}")
        for r in recs2:
            print(f"  - [{r.get('category')} / {r.get('priority')}]: {r.get('text')}")

    print("\n=== Step 3: Reverting back to Standard 75% Attendance & Random Forest ===")
    update_academic_policies({
        "attendance_threshold": 75.0,
        "critical_internal_threshold": 24.0,
        "active_ml_algorithm": "Random Forest",
    })
    train_course_models(
        algorithm="Random Forest",
        n_estimators=200,
        attendance_threshold=75.0,
        critical_score=40.0,
        critical_internal_threshold=24.0,
        trained_by="Admin"
    )
    print("Reverted cleanly to standard baseline!")

if __name__ == "__main__":
    test_pipeline()
