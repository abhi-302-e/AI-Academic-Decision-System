"""
===========================================================
AI-Based Autonomous Academic Decision System

Student Performance Prediction Model

Algorithms:
1. Decision Tree
2. Random Forest
===========================================================
"""

from pathlib import Path
import joblib
import pandas as pd

from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"

TRAIN_FILE = DATASET_DIR / "train.csv"

TEST_FILE = DATASET_DIR / "test.csv"

MODEL_FILE = BASE_DIR / "models" / "performance_model.pkl"

REPORT_FILE = BASE_DIR / "models" / "model_evaluation.txt"


# ==========================================================
# LOAD DATA
# ==========================================================

train_df = pd.read_csv(TRAIN_FILE)

test_df = pd.read_csv(TEST_FILE)
print("Train File:", TRAIN_FILE)
print("Test File:", TEST_FILE)
print("Train Columns:", train_df.columns.tolist())


# ==========================================================
# FEATURES
# ==========================================================

FEATURES = [

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

TARGET = "performance_label"


X_train = train_df[FEATURES]

y_train = train_df[TARGET]

X_test = test_df[FEATURES]

y_test = test_df[TARGET]

# ==========================================================
# DECISION TREE MODEL
# ==========================================================

decision_tree = DecisionTreeClassifier(

    random_state=42

)

decision_tree.fit(

    X_train,

    y_train

)

dt_predictions = decision_tree.predict(

    X_test

)

dt_accuracy = accuracy_score(

    y_test,

    dt_predictions

)


# ==========================================================
# RANDOM FOREST MODEL
# ==========================================================

random_forest = RandomForestClassifier(

    n_estimators=100,

    random_state=42

)

random_forest.fit(

    X_train,

    y_train

)

rf_predictions = random_forest.predict(

    X_test

)

rf_accuracy = accuracy_score(

    y_test,

    rf_predictions

)


# ==========================================================
# BEST MODEL
# ==========================================================

if rf_accuracy >= dt_accuracy:

    best_model = random_forest

    predictions = rf_predictions

    model_name = "Random Forest"

    accuracy = rf_accuracy

else:

    best_model = decision_tree

    predictions = dt_predictions

    model_name = "Decision Tree"

    accuracy = dt_accuracy


# ==========================================================
# SAVE MODEL
# ==========================================================

joblib.dump(

    best_model,

    MODEL_FILE

)

print(f"Best Model Saved : {model_name}")


# ==========================================================
# EVALUATION
# ==========================================================

precision = precision_score(

    y_test,

    predictions,

    average="weighted"

)

recall = recall_score(

    y_test,

    predictions,

    average="weighted"

)

f1 = f1_score(

    y_test,

    predictions,

    average="weighted"

)

conf_matrix = confusion_matrix(

    y_test,

    predictions

)

report = classification_report(

    y_test,

    predictions

)


# ==========================================================
# SAVE REPORT
# ==========================================================

with open(REPORT_FILE, "w") as file:

    file.write("AI Academic Decision System\n")

    file.write("=" * 50 + "\n\n")

    file.write(f"Best Model : {model_name}\n\n")

    file.write(f"Accuracy : {accuracy:.4f}\n")

    file.write(f"Precision : {precision:.4f}\n")

    file.write(f"Recall : {recall:.4f}\n")

    file.write(f"F1 Score : {f1:.4f}\n\n")

    file.write("Confusion Matrix\n")

    file.write(str(conf_matrix))

    file.write("\n\n")

    file.write("Classification Report\n\n")

    file.write(report)


# ==========================================================
# OUTPUT
# ==========================================================

print("=" * 50)

print("Performance Model Training Completed")

print(f"Best Model : {model_name}")

print(f"Accuracy : {accuracy:.4f}")

print(f"Precision : {precision:.4f}")

print(f"Recall : {recall:.4f}")

print(f"F1 Score : {f1:.4f}")

print("=" * 50)

