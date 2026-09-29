"""
===========================================================
AI-Based Autonomous Academic Decision System

Preprocessing Module

File: preprocess.py
===========================================================
"""

from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler


# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"

INPUT_FILE = DATASET_DIR / "engineered_students.csv"

TRAIN_FILE = DATASET_DIR / "train.csv"

TEST_FILE = DATASET_DIR / "test.csv"

SCALER_FILE = BASE_DIR / "preprocessing" / "scaler.pkl"

ENCODER_FILE = BASE_DIR / "preprocessing" / "label_encoders.pkl"


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_dataset():

    dataframe = pd.read_csv(INPUT_FILE)

    print("Engineered dataset loaded.")

    return dataframe


# ==========================================================
# LABEL ENCODING
# ==========================================================

def encode_categorical_columns(dataframe):

    encoders = {}

    categorical_columns = [

        "gender",

        "department",

        "assignment_submission_status",

        "attendance_category",

        "performance_label",

        "risk_level"

    ]

    for column in categorical_columns:

        encoder = LabelEncoder()

        dataframe[column] = encoder.fit_transform(
            dataframe[column]
        )

        encoders[column] = encoder

    joblib.dump(
        encoders,
        ENCODER_FILE
    )

    print("Label encoders saved.")

    return dataframe

# ==========================================================
# FEATURE SCALING
# ==========================================================

def scale_features(dataframe):
    """
    Scale numerical features using StandardScaler.
    """

    scaler = StandardScaler()

    numerical_columns = [

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

        "engagement_score"

    ]

    dataframe[numerical_columns] = scaler.fit_transform(
        dataframe[numerical_columns]
    )

    joblib.dump(
        scaler,
        SCALER_FILE
    )

    print("Scaler saved successfully.")

    return dataframe


# ==========================================================
# TRAIN TEST SPLIT
# ==========================================================

def split_dataset(dataframe):
    """
    Split dataset into train and test sets.
    """

    train_data, test_data = train_test_split(

        dataframe,

        test_size=0.20,

        random_state=42,

        shuffle=True

    )

    train_data.to_csv(

        TRAIN_FILE,

        index=False

    )

    test_data.to_csv(

        TEST_FILE,

        index=False

    )

    print(f"Training Records : {len(train_data)}")

    print(f"Testing Records  : {len(test_data)}")


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def main():
    print("Main function started.")

    dataframe = load_dataset()

    dataframe = encode_categorical_columns(dataframe)

    dataframe = scale_features(dataframe)

    split_dataset(dataframe)

    print("=" * 50)
    print("Preprocessing Completed Successfully")
    print("=" * 50)


# ==========================================================
# PROGRAM ENTRY
# ==========================================================

if __name__ == "__main__":

    main()

