"""
===========================================================
AI-Based Autonomous Academic Decision System

Data Cleaning Module

File: clean_data.py
===========================================================
"""

from pathlib import Path
import pandas as pd

# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"

INPUT_FILE = DATASET_DIR / "students.csv"

OUTPUT_FILE = DATASET_DIR / "clean_students.csv"


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_dataset():
    """
    Load the student dataset.
    """

    try:

        dataframe = pd.read_csv(INPUT_FILE)

        print(f"Dataset Loaded Successfully.")

        print(f"Total Records : {len(dataframe)}")

        return dataframe

    except FileNotFoundError:

        print("students.csv not found.")

        return None


# ==========================================================
# MISSING VALUES
# ==========================================================

def handle_missing_values(dataframe):
    """
    Fill missing values.
    """

    numeric_columns = dataframe.select_dtypes(
        include=["int64", "float64"]
    ).columns

    dataframe[numeric_columns] = dataframe[numeric_columns].fillna(
        dataframe[numeric_columns].mean()
    )

    categorical_columns = dataframe.select_dtypes(
        include=["object"]
    ).columns

    dataframe[categorical_columns] = dataframe[categorical_columns].fillna(
        "Unknown"
    )

    print("Missing values handled.")

    return dataframe


# ==========================================================
# REMOVE DUPLICATES
# ==========================================================

def remove_duplicates(dataframe):
    """
    Remove duplicate rows.
    """

    before = len(dataframe)

    dataframe = dataframe.drop_duplicates()

    after = len(dataframe)

    print(f"Duplicates Removed : {before-after}")

    return dataframe

# ==========================================================
# DATA VALIDATION
# ==========================================================

def validate_data(dataframe):
    """
    Validate numeric columns.
    """

    # CGPA should be between 0 and 10
    dataframe["cgpa"] = dataframe["cgpa"].clip(0, 10)

    # Attendance should be between 0 and 100
    dataframe["attendance_percentage"] = dataframe[
        "attendance_percentage"
    ].clip(0, 100)

    # Marks columns
    mark_columns = [
        "assignment_marks",
        "quiz_marks",
        "mid_exam_marks",
        "end_sem_marks",
        "lab_marks",
        "average_marks"
    ]

    for column in mark_columns:

        dataframe[column] = dataframe[column].clip(0, 100)

    # Course completion percentage
    dataframe["course_completion_percentage"] = dataframe[
        "course_completion_percentage"
    ].clip(0, 100)

    # Semester should be between 1 and 8
    dataframe["semester"] = dataframe["semester"].clip(1, 8)

    print("Data validation completed.")

    return dataframe


# ==========================================================
# SAVE DATASET
# ==========================================================

def save_dataset(dataframe):
    """
    Save cleaned dataset.
    """

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Clean dataset saved at:\n{OUTPUT_FILE}")


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def main():
    print("Main function started.")

    dataframe = load_dataset()

    if dataframe is None:
        return

    dataframe = handle_missing_values(dataframe)

    dataframe = remove_duplicates(dataframe)

    dataframe = validate_data(dataframe)

    save_dataset(dataframe)

    print("=" * 50)
    print("Data Cleaning Completed Successfully")
    print("=" * 50)


# ==========================================================
# PROGRAM ENTRY
# ==========================================================

if __name__ == "__main__":

    main()

