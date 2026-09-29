"""
===========================================================
AI-Based Autonomous Academic Decision System

Feature Engineering Module

File: feature_engineering.py
===========================================================
"""

from pathlib import Path
import pandas as pd

# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"

INPUT_FILE = DATASET_DIR / "clean_students.csv"

OUTPUT_FILE = DATASET_DIR / "engineered_students.csv"


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_dataset():

    try:

        dataframe = pd.read_csv(INPUT_FILE)

        print("Clean dataset loaded successfully.")

        return dataframe

    except FileNotFoundError:

        print("clean_students.csv not found.")

        return None


# ==========================================================
# TOTAL MARKS
# ==========================================================

def create_total_marks(dataframe):

    dataframe["total_marks"] = (

        dataframe["assignment_marks"]

        + dataframe["quiz_marks"]

        + dataframe["mid_exam_marks"]

        + dataframe["end_sem_marks"]

        + dataframe["lab_marks"]

    )

    return dataframe


# ==========================================================
# PERFORMANCE SCORE
# ==========================================================

def create_performance_score(dataframe):

    dataframe["performance_score"] = (

        dataframe["average_marks"] * 0.70

        +

        dataframe["attendance_percentage"] * 0.30

    ).round(2)

    return dataframe

# ==========================================================
# ATTENDANCE CATEGORY
# ==========================================================

def create_attendance_category(dataframe):
    """
    Categorize attendance.
    """

    def category(attendance):

        if attendance >= 90:
            return "Excellent"

        elif attendance >= 75:
            return "Good"

        elif attendance >= 60:
            return "Average"

        else:
            return "Poor"

    dataframe["attendance_category"] = dataframe[
        "attendance_percentage"
    ].apply(category)

    return dataframe


# ==========================================================
# ENGAGEMENT SCORE
# ==========================================================

def create_engagement_score(dataframe):
    """
    Create engagement score.
    """

    dataframe["engagement_score"] = (

        dataframe["lms_login_frequency"] * 0.4

        +

        dataframe["time_spent_learning"] * 0.3

        +

        dataframe["classroom_participation"] * 3

    ).round(2)

    return dataframe


# ==========================================================
# SAVE DATASET
# ==========================================================

def save_dataset(dataframe):

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Engineered dataset saved at:\n{OUTPUT_FILE}")


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def main():
    print("Main function started.")

    dataframe = load_dataset()

    if dataframe is None:
        return

    dataframe = create_total_marks(dataframe)

    dataframe = create_performance_score(dataframe)

    dataframe = create_attendance_category(dataframe)

    dataframe = create_engagement_score(dataframe)

    save_dataset(dataframe)

    print("=" * 50)
    print("Feature Engineering Completed Successfully")
    print("=" * 50)


# ==========================================================
# PROGRAM ENTRY
# ==========================================================

if __name__ == "__main__":

    main()

