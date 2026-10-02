
"""
===========================================================
AI-Based Autonomous Academic Decision System

Prediction Module
===========================================================
"""

from pathlib import Path

import joblib
import pandas as pd
from models.train_registered_course_models import get_latest_model_evaluation

# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"

PREPROCESS_DIR = BASE_DIR / "preprocessing"

PERFORMANCE_MODEL = MODEL_DIR / "performance_model.pkl"

RISK_MODEL = MODEL_DIR / "risk_model.pkl"

SCALER_FILE = PREPROCESS_DIR / "scaler.pkl"

ENCODER_FILE = PREPROCESS_DIR / "label_encoders.pkl"


# ==========================================================
# LOAD MODELS
# ==========================================================

performance_model = joblib.load(PERFORMANCE_MODEL)

risk_model = joblib.load(RISK_MODEL)

scaler = joblib.load(SCALER_FILE)

label_encoders = joblib.load(ENCODER_FILE)


# ==========================================================
# FEATURE LIST
# ==========================================================

FEATURE_COLUMNS = [

    "cgpa",

    "attendance_percentage",

    "assignment_marks",

    "quiz_marks",

    "mid_exam_marks",

    "end_sem_marks",

    "lab_marks",

    "average_marks",

    "lms_login_frequency",

    "time_spent_learning",

    "course_completion_percentage",

    "classroom_participation",

    "communication_skills",

    "discipline_score",

    "performance_score",

    "engagement_score"

]


# ==========================================================
# PREPARE INPUT DATA
# ==========================================================

def prepare_input(student_data):
    """
    Convert dictionary into DataFrame
    and apply scaling.
    """

    dataframe = pd.DataFrame([dict(student_data)])
    mark_columns = [
        "assignment_marks",
        "quiz_marks",
        "mid_exam_marks",
        "end_sem_marks",
        "lab_marks",
    ]
    numeric_columns = [
        "cgpa",
        "attendance_percentage",
        *mark_columns,
        "lms_login_frequency",
        "time_spent_learning",
        "course_completion_percentage",
        "classroom_participation",
        "communication_skills",
        "discipline_score",
    ]
    for column in numeric_columns:
        if column not in dataframe:
            dataframe[column] = 0
        dataframe[column] = pd.to_numeric(
            dataframe[column], errors="coerce"
        ).fillna(0)

    if "average_marks" not in dataframe or pd.isna(dataframe.at[0, "average_marks"]):
        dataframe["average_marks"] = dataframe[mark_columns].mean(axis=1)
    if "performance_score" not in dataframe or pd.isna(dataframe.at[0, "performance_score"]):
        dataframe["performance_score"] = (
            dataframe["average_marks"] * 0.7
            + dataframe["attendance_percentage"] * 0.3
        )
    if "engagement_score" not in dataframe or pd.isna(dataframe.at[0, "engagement_score"]):
        dataframe["engagement_score"] = (
            dataframe["lms_login_frequency"] * 0.4
            + dataframe["time_spent_learning"] * 0.3
            + dataframe["classroom_participation"] * 3
        )
    dataframe["total_marks"] = dataframe[mark_columns].sum(axis=1)

    scaler_columns = [
        "cgpa",
        "attendance_percentage",
        "assignment_marks",
        "quiz_marks",
        "mid_exam_marks",
        "end_sem_marks",
        "lab_marks",
        "average_marks",
        "lms_login_frequency",
        "time_spent_learning",
        "course_completion_percentage",
        "classroom_participation",
        "communication_skills",
        "discipline_score",
        "total_marks",
        "performance_score",
        "engagement_score",
    ]
    scaled_data = scaler.transform(dataframe[scaler_columns])
    scaled_dataframe = pd.DataFrame(scaled_data, columns=scaler_columns)

    return scaled_dataframe[FEATURE_COLUMNS]
# ==========================================================
# PERFORMANCE PREDICTION
# ==========================================================

def predict_performance(student_data):
    """
    Predict student performance.
    """

    dataframe = prepare_input(student_data)

    prediction = performance_model.predict(dataframe)[0]

    prediction = label_encoders[
        "performance_label"
    ].inverse_transform([prediction])[0]

    return prediction


# ==========================================================
# RISK PREDICTION
# ==========================================================

def predict_risk(student_data):
    """
    Predict academic risk level.
    """

    dataframe = prepare_input(student_data)

    prediction = risk_model.predict(dataframe)[0]

    prediction = label_encoders[
        "risk_level"
    ].inverse_transform([prediction])[0]

    return prediction


# ==========================================================
# COMPLETE PREDICTION
# ==========================================================

def predict_student(student_data):
    """
    Predict both performance and risk.
    """

    internal_marks = student_data.get("internal_marks")
    external_marks = student_data.get("external_marks")
    if internal_marks is not None and external_marks is not None:
        total_marks = float(internal_marks) + float(external_marks)
        attendance = float(student_data.get("attendance_percentage") or 0)
        if total_marks >= 75:
            performance = "Distinction"
        elif total_marks >= 40:
            performance = "Pass"
        else:
            performance = "Fail"

        if attendance < 75 and total_marks < 40:
            risk = "High"
        elif attendance < 75 or total_marks < 50:
            risk = "Medium"
        else:
            risk = "Low"

        return {
            "performance_prediction": performance,
            "risk_level": risk,
        }

    performance = predict_performance(student_data)

    risk = predict_risk(student_data)

    return {

        "performance_prediction": performance,

        "risk_level": risk

    }


def are_course_models_trained():
    course_performance_model = MODEL_DIR / "course_performance_model.pkl"
    course_risk_model = MODEL_DIR / "course_risk_model.pkl"
    return course_performance_model.exists() and course_risk_model.exists()


def predict_single_course_features(features_dict):
    """Predict performance and risk directly from feature values (used for live Admin simulation)."""
    course_performance_model = MODEL_DIR / "course_performance_model.pkl"
    course_risk_model = MODEL_DIR / "course_risk_model.pkl"
    if not course_performance_model.exists() or not course_risk_model.exists():
        return None

    features = pd.DataFrame([{
        "assignment_marks": float(features_dict.get("assignment_marks", 0.0)),
        "quiz_marks": float(features_dict.get("quiz_marks", 0.0)),
        "mid_exam_marks": float(features_dict.get("mid_exam_marks", 0.0)),
        "viva_marks": float(features_dict.get("viva_marks", 0.0)),
        "external_marks": float(features_dict.get("external_marks", 0.0)),
        "course_attendance": float(features_dict.get("course_attendance", 0.0)),
    }])
    trained_performance_model = joblib.load(course_performance_model)
    trained_risk_model = joblib.load(course_risk_model)
    return {
        "performance_prediction": trained_performance_model.predict(features)[0],
        "risk_level": trained_risk_model.predict(features)[0],
    }


def predict_registered_course(assessment):
    """Predict from a fully graded, registered course using Admin-trained models."""
    course_performance_model = MODEL_DIR / "course_performance_model.pkl"
    course_risk_model = MODEL_DIR / "course_risk_model.pkl"
    if (
        not course_performance_model.exists()
        or not course_risk_model.exists()
        or assessment.get("course_attendance") is None
    ):
        return None

    return predict_single_course_features({
        "assignment_marks": assessment.get("assignment_marks", 0.0),
        "quiz_marks": assessment.get("quiz_marks", 0.0),
        "mid_exam_marks": assessment.get("mid_exam_marks", 0.0),
        "viva_marks": assessment.get("viva_marks", 0.0),
        "external_marks": assessment.get("external_marks", 0.0),
        "course_attendance": assessment.get("course_attendance", 0.0),
    })


def predict_student_comprehensive(student_id, semester=1):
    """
    Generate comprehensive course-wise and overall prediction for registered student
    using Admin-trained ML models and Admin academic policies.
    """
    from database import (
        get_student_semester_registration,
        get_student_course_assessments,
        get_latest_model_training_run,
        get_academic_policies,
    )

    policies = get_academic_policies()
    if not policies.get("predictions_enabled", 1):
        return {
            "registered": True,
            "trained": True,
            "predictions_enabled": False,
            "status_message": "AI predictions & risk advisories are temporarily paused by Academic Administration for model recalibration.",
            "overall_performance": "Paused by Admin",
            "overall_risk": "Paused",
            "course_predictions": [],
            "training_run": None,
            "policies": policies,
        }

    raw_reg = get_student_semester_registration(student_id, semester)
    reg = dict(raw_reg) if raw_reg else None
    if not reg or reg.get("status") != "Registered":
        return {
            "registered": False,
            "trained": False,
            "predictions_enabled": True,
            "status_message": "Student is not registered for this semester. Semester registration required before academic evaluation.",
            "overall_performance": "Not Registered",
            "overall_risk": "N/A",
            "course_predictions": [],
            "training_run": None,
            "policies": policies,
        }

    training_run = get_latest_model_training_run()
    if not are_course_models_trained():
        return {
            "registered": True,
            "trained": False,
            "predictions_enabled": True,
            "status_message": "Awaiting Admin ML Training. The Administrator has not trained the predictive model on registered academic data yet.",
            "overall_performance": "Awaiting Model",
            "overall_risk": "Awaiting Model",
            "course_predictions": [],
            "training_run": training_run,
            "policies": policies,
        }

    assessments = get_student_course_assessments(student_id, semester)
    if not assessments:
        return {
            "registered": True,
            "trained": True,
            "predictions_enabled": True,
            "status_message": "Enrolled in courses. Awaiting assessment grading by assigned course faculty.",
            "overall_performance": "Pending Grades",
            "overall_risk": "Pending Grades",
            "course_predictions": [],
            "training_run": training_run,
            "policies": policies,
        }


    course_results = []
    performance_votes = []
    risk_votes = []

    for a in assessments:
        pred = predict_registered_course(a)
        if pred:
            internal_total = a.get("internal_total")
            if internal_total is None and a.get("assignment_marks") is not None:
                internal_total = round(
                    float(a.get("assignment_marks") or 0)
                    + float(a.get("quiz_marks") or 0)
                    + float(a.get("mid_exam_marks") or 0)
                    + float(a.get("viva_marks") or 0),
                    2
                )
            overall_total = a.get("overall_total")
            if overall_total is None and internal_total is not None and a.get("external_marks") is not None:
                overall_total = round(internal_total + float(a.get("external_marks") or 0), 2)

            course_results.append({
                "course_code": a.get("course_code"),
                "course_name": a.get("course_name"),
                "credits": a.get("credits"),
                "performance_prediction": pred["performance_prediction"],
                "risk_level": pred["risk_level"],
                "mid_exam_marks": a.get("mid_exam_marks"),
                "assignment_marks": a.get("assignment_marks"),
                "quiz_marks": a.get("quiz_marks"),
                "viva_marks": a.get("viva_marks"),
                "internal_total": internal_total,
                "external_marks": a.get("external_marks"),
                "overall_total": overall_total,
                "course_attendance": a.get("course_attendance"),
                "faculty_name": a.get("faculty_name"),
            })
            performance_votes.append(pred["performance_prediction"])
            risk_votes.append(pred["risk_level"])

    att_thresh = float(policies.get("attendance_threshold", 75.0))
    crit_int_thresh = float(policies.get("critical_internal_threshold", 24.0))

    has_att_shortage = any(float(c.get("course_attendance") or 0.0) < att_thresh for c in course_results)
    avg_internal_val = (
        sum(float(c.get("internal_total") or 0.0) for c in course_results) / len(course_results)
        if course_results else None
    )

    if "High" in risk_votes or (has_att_shortage and "Fail" in performance_votes):
        overall_risk = "High"
    elif "Medium" in risk_votes or has_att_shortage or (avg_internal_val is not None and avg_internal_val < crit_int_thresh):
        overall_risk = "Medium"
    elif risk_votes:
        overall_risk = "Low"
    else:
        overall_risk = "Low"

    if "Fail" in performance_votes:
        fail_count = performance_votes.count("Fail")
        if fail_count >= 2:
            overall_perf = "Fail"
        else:
            overall_perf = "Pass"
    elif "Pass" in performance_votes:
        overall_perf = "Pass"
    elif performance_votes:
        overall_perf = "Distinction"
    else:
        overall_perf = "Pending"

    return {
        "registered": True,
        "trained": True,
        "predictions_enabled": True,
        "status_message": "Evaluated successfully from registered courses and real-time attendance.",
        "overall_performance": overall_perf,
        "overall_risk": overall_risk,
        "course_predictions": course_results,
        "training_run": training_run,
        "model_evaluation": get_latest_model_evaluation(),
        "policies": policies,
    }



# ==========================================================
# SAMPLE TEST
# ==========================================================

if __name__ == "__main__":

    sample_student = {

        "cgpa": 8.5,

        "attendance_percentage": 88,

        "assignment_marks": 82,

        "quiz_marks": 80,

        "mid_exam_marks": 84,

        "end_sem_marks": 86,

        "lab_marks": 90,

        "average_marks": 84.4,

        "lms_login_frequency": 65,

        "time_spent_learning": 42,

        "course_completion_percentage": 90,

        "classroom_participation": 8,

        "communication_skills": 9,

        "discipline_score": 10,

        "performance_score": 85.48,

        "engagement_score": 162.6

    }

    result = predict_student(sample_student)

    print("=" * 50)

    print("Prediction Result")

    print("=" * 50)

    print(f"Performance : {result['performance_prediction']}")

    print(f"Risk Level : {result['risk_level']}")

    print("=" * 50)