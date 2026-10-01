"""Train course-level models from registered student assessments and attendance."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from database import get_connection, get_course_model_training_data


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


def prepare_training_data(records):
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
        lambda score: "Distinction" if score >= 75 else "Pass" if score >= 40 else "Fail"
    )
    frame["risk_label"] = frame.apply(
        lambda row: (
            "High" if row["course_attendance"] < 75 and row["total_score"] < 40
            else "Medium" if row["course_attendance"] < 75 or row["total_score"] < 50
            else "Low"
        ),
        axis=1,
    )
    return frame


def _fit_model(frame, target):
    class_counts = frame[target].value_counts()
    if len(class_counts) < 2:
        raise ValueError(f"At least two {target} classes are required for training.")
    stratify = frame[target] if class_counts.min() >= 2 and len(frame) >= 10 else None
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES],
        frame[target],
        test_size=0.2 if len(frame) >= 10 else 0.25,
        random_state=42,
        stratify=stratify,
    )
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2,
    )
    model.fit(x_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(x_test)) if len(x_test) else None
    return model, accuracy


def train_course_models(trained_by="Admin"):
    frame = prepare_training_data(get_course_model_training_data())
    if len(frame) < 20:
        raise ValueError(
            f"At least 20 complete course assessments with recorded attendance are required; found {len(frame)}."
        )
    performance_model, performance_accuracy = _fit_model(frame, "performance_label")
    risk_model, risk_accuracy = _fit_model(frame, "risk_label")
    joblib.dump(performance_model, PERFORMANCE_MODEL)
    joblib.dump(risk_model, RISK_MODEL)
    REPORT_FILE.write_text(
        "Registered Course Models\n"
        "========================\n"
        f"Training rows: {len(frame)}\n"
        f"Performance classes: {frame['performance_label'].value_counts().to_dict()}\n"
        f"Risk classes: {frame['risk_label'].value_counts().to_dict()}\n"
        f"Performance holdout accuracy: {performance_accuracy}\n"
        f"Risk holdout accuracy: {risk_accuracy}\n",
        encoding="utf-8",
    )
    connection = get_connection()
    try:
        connection.executemany(
            """
            INSERT INTO model_training_runs
                (model_name, sample_count, accuracy, trained_by)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("Course performance model", len(frame), performance_accuracy, trained_by),
                ("Course risk model", len(frame), risk_accuracy, trained_by),
            ]
        )
        connection.commit()
    finally:
        connection.close()
    return {
        "samples": len(frame),
        "performance_accuracy": performance_accuracy,
        "risk_accuracy": risk_accuracy,
        "performance_classes": frame["performance_label"].value_counts().to_dict(),
        "risk_classes": frame["risk_label"].value_counts().to_dict(),
        "trained_by": trained_by,
    }
