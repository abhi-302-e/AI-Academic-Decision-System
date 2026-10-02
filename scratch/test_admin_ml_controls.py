"""
Test script for verifying Admin ML Model Controls, Dynamic Training,
Policy Threshold Propagation, and Sandbox Simulation.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database import get_academic_policies, update_academic_policies
from models.train_registered_course_models import train_course_models
from prediction import predict_single_course_features, predict_student_comprehensive
from recommendation_engine import generate_course_level_recommendations


def main():
    print("=" * 60)
    print("TEST 1: ACADEMIC POLICIES RETRIEVAL & UPDATE")
    print("=" * 60)
    original_policies = get_academic_policies()
    print("Original Policies:", original_policies)
    assert "attendance_threshold" in original_policies
    assert "critical_internal_threshold" in original_policies
    assert "predictions_enabled" in original_policies
    print("✓ Academic Policies fetched successfully.")

    # Test update
    update_res = update_academic_policies({
        "attendance_threshold": 78.0,
        "critical_internal_threshold": 25.0,
        "predictions_enabled": 1,
    })
    updated_policies = get_academic_policies()
    assert updated_policies["attendance_threshold"] == 78.0
    assert updated_policies["critical_internal_threshold"] == 25.0
    print("✓ Academic Policies updated and persisted successfully.")

    print("\n" + "=" * 60)
    print("TEST 2: MULTI-ALGORITHM MODEL TRAINING (ADMIN CONTROL)")
    print("=" * 60)
    # Test Random Forest
    rf_res = train_course_models(
        algorithm="Random Forest",
        n_estimators=100,
        max_depth=10,
        test_size=0.2,
        attendance_threshold=78.0,
        critical_score=40.0,
        trained_by="Admin_Test"
    )
    print(f"Random Forest - Perf Acc: {rf_res['performance_accuracy']:.1%}, Risk Acc: {rf_res['risk_accuracy']:.1%}")
    assert rf_res["samples"] == 4000
    assert rf_res["performance_accuracy"] > 0.85
    assert rf_res["risk_accuracy"] > 0.85

    # Test Decision Tree
    dt_res = train_course_models(
        algorithm="Decision Tree",
        max_depth=8,
        test_size=0.2,
        attendance_threshold=78.0,
        critical_score=40.0,
        trained_by="Admin_Test"
    )
    print(f"Decision Tree - Perf Acc: {dt_res['performance_accuracy']:.1%}, Risk Acc: {dt_res['risk_accuracy']:.1%}")

    # Retrain back to Random Forest (default institutional standard)
    rf_final = train_course_models(
        algorithm="Random Forest",
        n_estimators=200,
        max_depth=None,
        test_size=0.2,
        attendance_threshold=75.0,
        critical_score=40.0,
        trained_by="Admin"
    )
    update_academic_policies({"attendance_threshold": 75.0, "critical_internal_threshold": 24.0})
    print(f"Final RF Ensemble - Perf Acc: {rf_final['performance_accuracy']:.1%}, Risk Acc: {rf_final['risk_accuracy']:.1%}")
    print("✓ Multi-Algorithm Training tested and working perfectly.")

    print("\n" + "=" * 60)
    print("TEST 3: LIVE SIMULATION SANDBOX PREDICTION")
    print("=" * 60)
    sample_features = {
        "assignment_marks": 8.0,
        "quiz_marks": 7.5,
        "mid_exam_marks": 22.0,
        "viva_marks": 8.5,
        "external_marks": 32.0,
        "course_attendance": 88.0,
    }
    pred_res = predict_single_course_features(sample_features)
    print("Simulated Student Features:", sample_features)
    print("Sandbox Prediction Result:", pred_res)
    assert pred_res is not None
    assert pred_res["performance_prediction"] in ("Distinction", "Pass", "Fail")
    assert pred_res["risk_level"] in ("Low", "Medium", "High")
    print("✓ Live Simulation Sandbox prediction works perfectly.")

    print("\n" + "=" * 60)
    print("TEST 4: DYNAMIC POLICY-BASED RECOMMENDATIONS")
    print("=" * 60)
    # Test student with low attendance and low internal
    at_risk_course = {
        "course_name": "Operating Systems",
        "course_attendance": 70.0,
        "mid_exam_marks": 11.0,
        "assignment_marks": 4.0,
        "quiz_marks": 4.0,
        "viva_marks": 4.0,
        "external_marks": 14.0,
        "performance_prediction": "Fail",
        "faculty_name": "Prof. Rao",
    }
    recs = generate_course_level_recommendations(at_risk_course)
    print(f"Generated {len(recs)} Recommendations for at-risk student:")
    for r in recs:
        print(f"  {r['icon']} [{r['category']} - {r['priority']}]: {r['text']}")
    # Verify statutory attendance alert was generated
    assert any("Attendance" in r["category"] for r in recs)
    assert any("CIE" in r["category"] for r in recs)
    print("✓ Recommendation Engine dynamically generated alerts per Admin policy.")

    print("\n" + "=" * 60)
    print("TEST 5: ADMIN PREDICTION GATE TOGGLE")
    print("=" * 60)
    # Disable predictions
    update_academic_policies({"predictions_enabled": 0})
    student_pred_paused = predict_student_comprehensive(1, 1)
    print("Paused Prediction Status:", student_pred_paused["status_message"])
    assert student_pred_paused["predictions_enabled"] is False

    # Re-enable predictions
    update_academic_policies({"predictions_enabled": 1})
    student_pred_live = predict_student_comprehensive(1, 1)
    print("Live Prediction Overall Performance:", student_pred_live["overall_performance"])
    assert student_pred_live["predictions_enabled"] is True
    print("✓ Admin Master Prediction Gate toggles predictions correctly.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    main()
