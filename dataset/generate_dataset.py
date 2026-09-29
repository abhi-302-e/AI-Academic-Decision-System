"""
===========================================================
AI-Based Autonomous Academic Decision System

Generate Synthetic Student Dataset
===========================================================
"""

import random
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker("en_IN")

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------

NUMBER_OF_STUDENTS = 300

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = BASE_DIR / "students.csv"

DEPARTMENTS = [
    "CSE",
    "CSE-AIML",
    "CSE-DS",
    "IT",
    "ECE",
    "EEE",
    "Mechanical",
    "Civil"
]

SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

GENDERS = [
    "Male",
    "Female"
]

PERFORMANCE = [
    "Fail",
    "Pass",
    "Distinction"
]

RISK_LEVEL = [
    "Low",
    "Medium",
    "High"
]

records = []

# --------------------------------------------------------
# DATA GENERATION
# --------------------------------------------------------

for i in range(1, NUMBER_OF_STUDENTS + 1):

    department = random.choice(DEPARTMENTS)

    semester = random.choice(SEMESTERS)

    attendance = random.randint(45, 100)

    assignment = random.randint(20, 100)

    quiz = random.randint(20, 100)

    mid = random.randint(20, 100)

    end = random.randint(20, 100)

    lab = random.randint(20, 100)

    average = round(
        (assignment + quiz + mid + end + lab) / 5,
        2
    )

    cgpa = round(random.uniform(5.0, 10.0), 2)

    login_frequency = random.randint(5, 120)

    learning_time = round(random.uniform(5, 70), 1)

    course_completion = random.randint(30, 100)

    communication = random.randint(1, 10)

    discipline = random.randint(5, 10)

    participation = random.randint(1, 10)

    # --------------------------------------------------------
    # PERFORMANCE LABEL
    # --------------------------------------------------------

    if average >= 75:
        performance = "Distinction"

    elif average >= 40:
        performance = "Pass"

    else:
        performance = "Fail"

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    if attendance < 75 and average < 40:
        risk = "High"

    elif attendance < 75 or average < 50:
        risk = "Medium"

    else:
        risk = "Low"

    # --------------------------------------------------------
    # ASSIGNMENT SUBMISSION STATUS
    # --------------------------------------------------------

    assignment_status = random.choice([
        "Completed",
        "Pending"
    ])

    # --------------------------------------------------------
    # STUDENT RECORD
    # --------------------------------------------------------

    records.append({

        "student_id": i,

        "roll_number": f"22CS{1000+i}",

        "full_name": fake.name(),

        "gender": random.choice(GENDERS),

        "department": department,

        "semester": semester,

        "email": fake.email(),

        "phone": fake.msisdn()[:10],

        "cgpa": cgpa,

        "attendance_percentage": attendance,

        "assignment_marks": assignment,

        "quiz_marks": quiz,

        "mid_exam_marks": mid,

        "end_sem_marks": end,

        "lab_marks": lab,

        "average_marks": average,

        "lms_login_frequency": login_frequency,

        "time_spent_learning": learning_time,

        "assignment_submission_status": assignment_status,

        "course_completion_percentage": course_completion,

        "classroom_participation": participation,

        "communication_skills": communication,

        "discipline_score": discipline,

        "performance_label": performance,

        "risk_level": risk

    })

# --------------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------------

students = pd.DataFrame(records)

# --------------------------------------------------------
# SAVE CSV
# --------------------------------------------------------

students.to_csv(
    OUTPUT_FILE,
    index=False
)

print("=" * 50)
print("Dataset Generated Successfully")
print(f"Total Records : {NUMBER_OF_STUDENTS}")
print(f"Saved To : {OUTPUT_FILE}")
print("=" * 50)
