
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
# EXPLAINABLE AI (XAI): FEATURE ATTRIBUTION & CONTRIBUTION
# ==========================================================

def explain_student_academic_prediction(student_data, policies=None):
    """
    Compute explainable feature contributions indicating why a student
    was assigned a specific risk classification and performance projection.
    """
    policies = policies or {}
    att_thresh = float(policies.get("attendance_threshold", 75.0))
    crit_int = float(policies.get("critical_internal_threshold", 24.0))

    att = float(student_data.get("attendance_percentage") or 0.0)
    mid = float(student_data.get("mid_exam_marks") or 0.0)
    quiz = float(student_data.get("quiz_marks") or 0.0)
    assn = float(student_data.get("assignment_marks") or 0.0)
    lab = float(student_data.get("lab_marks") or 0.0)
    time_spent = float(student_data.get("time_spent_learning") or 0.0)
    lms_freq = float(student_data.get("lms_login_frequency") or 0.0)

    factors = []

    # 1. Attendance Regularity (Benchmark: 75%)
    if att < att_thresh:
        att_impact = -round((att_thresh - att) * 1.6 + 10, 1)
        att_reason = f"Attendance ({att:.1f}%) is below statutory {att_thresh:.0f}% minimum, triggering high condonation risk."
        att_dir = "Negative"
    else:
        att_impact = round(min((att - att_thresh) * 1.2 + 8, 35.0), 1)
        att_reason = f"Attendance ({att:.1f}%) meets statutory exam eligibility (≥ {att_thresh:.0f}%)."
        att_dir = "Positive"
    factors.append({
        "feature": "Attendance Regularity",
        "value": f"{att:.1f}%",
        "impact": att_impact,
        "direction": att_dir,
        "benchmark": f"≥ {att_thresh:.0f}%",
        "reason": att_reason,
    })

    # 2. Mid-Exam Examination (/30)
    if mid < 15.0:
        mid_impact = -round((15.0 - mid) * 2.2 + 12, 1)
        mid_reason = f"Mid Exam score ({mid:.1f}/30) is below passing threshold (15.0), depressing CIE trajectory."
        mid_dir = "Negative"
    elif mid >= 24.0:
        mid_impact = round((mid - 20.0) * 2.5 + 15, 1)
        mid_reason = f"High Mid-Term mastery ({mid:.1f}/30) strongly propels performance toward Distinction."
        mid_dir = "Positive"
    else:
        mid_impact = round((mid - 15.0) * 1.5, 1)
        mid_reason = f"Satisfactory Mid Exam score ({mid:.1f}/30); steady passing trend."
        mid_dir = "Positive" if mid_impact >= 0 else "Negative"
    factors.append({
        "feature": "Mid-Term Examination (/30)",
        "value": f"{mid:.1f} / 30",
        "impact": mid_impact,
        "direction": mid_dir,
        "benchmark": "≥ 15.0 / 30",
        "reason": mid_reason,
    })

    # 3. Continuous Formative Tasks (Quiz + Assignment /20)
    formative = quiz + assn
    if formative < 10.0:
        form_impact = -round((10.0 - formative) * 1.8 + 6, 1)
        form_reason = f"Formative score ({formative:.1f}/20) signals incomplete homework submissions and quiz gaps."
        form_dir = "Negative"
    else:
        form_impact = round(min((formative - 10.0) * 1.4 + 5, 20.0), 1)
        form_reason = f"Strong continuous assignment and quiz discipline ({formative:.1f}/20)."
        form_dir = "Positive"
    factors.append({
        "feature": "Quizzes & Assignments (/20)",
        "value": f"{formative:.1f} / 20",
        "impact": form_impact,
        "direction": form_dir,
        "benchmark": "≥ 12.0 / 20",
        "reason": form_reason,
    })

    # 4. Lab & Viva Fluency (/10)
    if lab < 5.0:
        lab_impact = -round((5.0 - lab) * 2.0 + 5, 1)
        lab_reason = f"Practical viva score ({lab:.1f}/10) requires remedial laboratory guidance."
        lab_dir = "Negative"
    else:
        lab_impact = round(min(lab * 1.2, 15.0), 1)
        lab_reason = f"Good laboratory experiment comprehension and viva demonstration ({lab:.1f}/10)."
        lab_dir = "Positive"
    factors.append({
        "feature": "Practical & Viva Fluency (/10)",
        "value": f"{lab:.1f} / 10",
        "impact": lab_impact,
        "direction": lab_dir,
        "benchmark": "≥ 5.0 / 10",
        "reason": lab_reason,
    })

    # 5. LMS Engagement & Study Hours
    if time_spent < 10.0 or lms_freq < 15:
        lms_impact = -8.0
        lms_reason = f"Low digital VLE activity ({time_spent:.1f} hrs/wk, {int(lms_freq)} logins) signals disengagement."
        lms_dir = "Negative"
    else:
        lms_impact = round(min(time_spent * 0.4 + lms_freq * 0.1, 15.0), 1)
        lms_reason = f"Consistent LMS courseware engagement ({time_spent:.1f} hrs/wk, {int(lms_freq)} logins)."
        lms_dir = "Positive"
    factors.append({
        "feature": "LMS & Study Engagement",
        "value": f"{time_spent:.1f}h/wk · {int(lms_freq)} logins",
        "impact": lms_impact,
        "direction": lms_dir,
        "benchmark": "≥ 12h/wk",
        "reason": lms_reason,
    })

    # Summary synthesis
    neg_factors = [f for f in factors if f["impact"] < 0]
    pos_factors = [f for f in factors if f["impact"] > 0]

    primary_risk = min(factors, key=lambda x: x["impact"])
    primary_strength = max(factors, key=lambda x: x["impact"])

    if neg_factors:
        narrative = (
            f"The primary driver elevating academic risk is {primary_risk['feature']} "
            f"({primary_risk['value']}, contributing {primary_risk['impact']} points). "
            f"Remediating this factor will directly improve the student's grade standing."
        )
    else:
        narrative = (
            f"Academic indicators demonstrate strong stability across all metrics. "
            f"The strongest performance anchor is {primary_strength['feature']} "
            f"({primary_strength['value']}, contributing +{primary_strength['impact']} points)."
        )

    return {
        "factors": factors,
        "primary_risk_driver": primary_risk["feature"] if primary_risk["impact"] < 0 else "None",
        "primary_strength": primary_strength["feature"],
        "executive_summary": narrative,
    }


# ==========================================================
# WHAT-IF ACADEMIC GOAL SIMULATOR
# ==========================================================

def simulate_student_academic_outcomes(
    base_student_data,
    target_mid,
    target_attendance,
    target_quiz,
    target_assign,
    target_study_hours,
    policies=None,
):
    """
    Simulate academic performance and risk under hypothetical score/attendance conditions.
    """
    sim_data = dict(base_student_data)
    sim_data["mid_exam_marks"] = float(target_mid)
    sim_data["attendance_percentage"] = float(target_attendance)
    sim_data["quiz_marks"] = float(target_quiz)
    sim_data["assignment_marks"] = float(target_assign)
    sim_data["time_spent_learning"] = float(target_study_hours)

    mark_cols = ["assignment_marks", "quiz_marks", "mid_exam_marks", "end_sem_marks", "lab_marks"]
    sim_data["average_marks"] = sum(float(sim_data.get(c) or 0) for c in mark_cols) / len(mark_cols)
    sim_data["performance_score"] = (sim_data["average_marks"] * 0.7) + (sim_data["attendance_percentage"] * 0.3)
    sim_data["total_marks"] = sum(float(sim_data.get(c) or 0) for c in mark_cols)

    pred_res = predict_student(sim_data)
    att_cutoff = float((policies or {}).get("attendance_threshold", 75.0))
    is_eligible = float(target_attendance) >= att_cutoff

    return {
        "simulated_performance": pred_res.get("performance_prediction", "Pass"),
        "simulated_risk": pred_res.get("risk_level", "Medium"),
        "is_exam_eligible": is_eligible,
        "attendance_gap": round(max(0.0, att_cutoff - float(target_attendance)), 1),
        "target_internal_total": round(float(target_mid) + float(target_quiz) + float(target_assign) + float(sim_data.get("lab_marks") or 8.0), 1),
        "target_attendance": float(target_attendance),
        "target_mid": float(target_mid),
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