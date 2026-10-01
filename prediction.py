"""
===========================================================
AI-Based Autonomous Academic Decision System

Prediction Module
===========================================================
"""

from pathlib import Path

import joblib
import pandas as pd

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

    features = pd.DataFrame([{
        "assignment_marks": assessment["assignment_marks"],
        "quiz_marks": assessment["quiz_marks"],
        "mid_exam_marks": assessment["mid_exam_marks"],
        "viva_marks": assessment["viva_marks"],
        "external_marks": assessment["external_marks"],
        "course_attendance": assessment["course_attendance"],
    }])
    trained_performance_model = joblib.load(course_performance_model)
    trained_risk_model = joblib.load(course_risk_model)
    return {
        "performance_prediction": trained_performance_model.predict(features)[0],
        "risk_level": trained_risk_model.predict(features)[0],
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