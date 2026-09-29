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

    dataframe = pd.DataFrame([student_data])

    dataframe = dataframe[FEATURE_COLUMNS]

    dataframe[FEATURE_COLUMNS] = scaler.transform(
        dataframe[FEATURE_COLUMNS]
    )

    return dataframe
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

    performance = predict_performance(student_data)

    risk = predict_risk(student_data)

    return {

        "performance_prediction": performance,

        "risk_level": risk

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