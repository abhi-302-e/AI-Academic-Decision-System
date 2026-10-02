"""Train course-level models from registered student assessments and attendance."""

import json
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

from database import get_connection, get_course_model_training_data, get_academic_policies, update_academic_policies

MODEL_DIR = Path(__file__).resolve().parent
FEATURES = [
    "assignment_marks",
    "quiz_marks",
    "mid_exam_marks",
    "viva_marks",
    "external_marks",
    "course_attendance",
]
PERFORMANCE_MODEL = MODEL_DIR / "course_performance_model.pkl"
RISK_MODEL = MODEL_DIR / "course_risk_model.pkl"
REPORT_FILE = MODEL_DIR / "course_model_evaluation.txt"
EVALUATION_JSON = MODEL_DIR / "course_model_evaluation.json"


def prepare_training_data(records, attendance_threshold=75.0, critical_score=40.0):
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    frame = frame.dropna(subset=FEATURES).copy()
    frame["internal_total"] = (
        frame["assignment_marks"]
        + frame["quiz_marks"]
        + frame["mid_exam_marks"]
        + frame["viva_marks"]
    )
    frame["total_score"] = frame["internal_total"] + frame["external_marks"]
    frame["performance_label"] = frame["total_score"].map(
        lambda score: "Distinction" if score >= 75 else "Pass" if score >= critical_score else "Fail"
    )
    frame["risk_label"] = frame.apply(
        lambda row: (
            "High" if row["course_attendance"] < attendance_threshold and row["total_score"] < critical_score
            else "Medium" if row["course_attendance"] < attendance_threshold or row["total_score"] < 50
            else "Low"
        ),
        axis=1,
    )
    return frame


def _fit_model(frame, target, algorithm="Random Forest", n_estimators=200, max_depth=None, test_size=0.2, expected_labels=None):
    class_counts = frame[target].value_counts()
    if len(class_counts) < 2:
        raise ValueError(f"At least two {target} classes are required for training.")
    stratify = frame[target] if class_counts.min() >= 2 and len(frame) >= 10 else None
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES],
        frame[target],
        test_size=test_size if len(frame) >= 10 else 0.25,
        random_state=42,
        stratify=stratify,
    )

    if algorithm == "Decision Tree":
        model = DecisionTreeClassifier(
            max_depth=max_depth,
            random_state=42,
            class_weight="balanced",
        )
    elif algorithm == "Gradient Boosting":
        model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth or 3,
            random_state=42,
        )
    elif algorithm == "Logistic Regression":
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight="balanced",
        )
    else:  # Default: Random Forest
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            class_weight="balanced",
            min_samples_leaf=2,
        )

    model.fit(x_train, y_train)
    y_pred = model.predict(x_test) if len(x_test) else []
    accuracy = accuracy_score(y_test, y_pred) if len(x_test) else 0.0

    # Ensure consistent label ordering for confusion matrices
    if expected_labels:
        labels = [lbl for lbl in expected_labels if lbl in frame[target].unique()]
    else:
        labels = sorted(list(frame[target].unique()))

    if len(x_test):
        cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()
        clf_report = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
    else:
        cm = []
        clf_report = {}

    # Extract feature importances
    feature_importances = {}
    if hasattr(model, "feature_importances_"):
        for feat, imp in zip(FEATURES, model.feature_importances_):
            feature_importances[feat] = round(float(imp), 4)
    elif hasattr(model, "coef_"):
        # For Logistic Regression, average absolute coefficients across classes
        coef_mean = np.mean(np.abs(model.coef_), axis=0)
        coef_norm = coef_mean / np.sum(coef_mean) if np.sum(coef_mean) > 0 else coef_mean
        for feat, imp in zip(FEATURES, coef_norm):
            feature_importances[feat] = round(float(imp), 4)

    return model, accuracy, feature_importances, cm, labels, clf_report


def train_course_models(
    algorithm="Random Forest",
    n_estimators=200,
    max_depth=None,
    test_size=0.2,
    attendance_threshold=75.0,
    critical_score=40.0,
    critical_internal_threshold=24.0,
    trained_by="Admin"
):
    frame = prepare_training_data(
        get_course_model_training_data(),
        attendance_threshold=attendance_threshold,
        critical_score=critical_score,
    )
    if len(frame) < 20:
        raise ValueError(
            f"At least 20 complete course assessments with recorded attendance are required; found {len(frame)}."
        )

    perf_labels_order = ["Distinction", "Pass", "Fail"]
    risk_labels_order = ["Low", "Medium", "High"]

    performance_model, performance_accuracy, perf_importances, cm_perf, labels_perf, rep_perf = _fit_model(
        frame, "performance_label", algorithm=algorithm, n_estimators=n_estimators, max_depth=max_depth, test_size=test_size, expected_labels=perf_labels_order
    )
    risk_model, risk_accuracy, risk_importances, cm_risk, labels_risk, rep_risk = _fit_model(
        frame, "risk_label", algorithm=algorithm, n_estimators=n_estimators, max_depth=max_depth, test_size=test_size, expected_labels=risk_labels_order
    )

    joblib.dump(performance_model, PERFORMANCE_MODEL)
    joblib.dump(risk_model, RISK_MODEL)

    trained_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Serialize structured evaluation JSON for Admin & Student portals
    evaluation_payload = {
        "algorithm": algorithm,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "test_size": test_size,
        "attendance_threshold": float(attendance_threshold),
        "critical_score": float(critical_score),
        "critical_internal_threshold": float(critical_internal_threshold),
        "performance_accuracy": float(performance_accuracy),
        "risk_accuracy": float(risk_accuracy),
        "performance_confusion_matrix": {
            "matrix": cm_perf,
            "labels": labels_perf,
        },
        "risk_confusion_matrix": {
            "matrix": cm_risk,
            "labels": labels_risk,
        },
        "performance_report": rep_perf,
        "risk_report": rep_risk,
        "performance_feature_importances": perf_importances,
        "risk_feature_importances": risk_importances,
        "performance_classes": frame["performance_label"].value_counts().to_dict(),
        "risk_classes": frame["risk_label"].value_counts().to_dict(),
        "samples": len(frame),
        "trained_by": trained_by,
        "trained_at": trained_timestamp,
    }

    try:
        EVALUATION_JSON.write_text(json.dumps(evaluation_payload, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving evaluation JSON: {e}")

    REPORT_FILE.write_text(
        f"Registered Course Models ({algorithm})\n"
        "========================\n"
        f"Training rows: {len(frame)}\n"
        f"Algorithm: {algorithm}\n"
        f"Hyperparameters: n_estimators={n_estimators}, max_depth={max_depth}, test_size={test_size}\n"
        f"Policy Thresholds: attendance={attendance_threshold}%, critical_score={critical_score}, CIE_cutoff={critical_internal_threshold}\n"
        f"Performance classes: {frame['performance_label'].value_counts().to_dict()}\n"
        f"Risk classes: {frame['risk_label'].value_counts().to_dict()}\n"
        f"Performance holdout accuracy: {performance_accuracy:.4f}\n"
        f"Risk holdout accuracy: {risk_accuracy:.4f}\n"
        f"Performance Confusion Matrix ({labels_perf}): {cm_perf}\n"
        f"Risk Confusion Matrix ({labels_risk}): {cm_risk}\n",
        encoding="utf-8",
    )

    # Immediately synchronize academic policies in the database
    update_academic_policies({
        "active_ml_algorithm": algorithm,
        "attendance_threshold": float(attendance_threshold),
        "critical_internal_threshold": float(critical_internal_threshold),
    })

    connection = get_connection()
    try:
        connection.executemany(
            """
            INSERT INTO model_training_runs
                (model_name, sample_count, accuracy, trained_by)
            VALUES (?, ?, ?, ?)
            """,
            [
                (f"Performance model ({algorithm})", len(frame), performance_accuracy, trained_by),
                (f"Risk model ({algorithm})", len(frame), risk_accuracy, trained_by),
            ]
        )
        connection.commit()
    finally:
        connection.close()

    return evaluation_payload


def get_latest_model_evaluation():
    """Retrieve the latest model evaluation metrics and confusion matrices."""
    if EVALUATION_JSON.exists():
        try:
            return json.loads(EVALUATION_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

