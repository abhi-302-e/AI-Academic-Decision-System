"""
===========================================================
AI-Based Autonomous Academic Decision System
Database Module

File: database.py
Author: Your Team
Description:
    Handles database connection and initialization.
===========================================================
"""

from pathlib import Path
import sqlite3
from tkinter import Menu
import bcrypt
import pandas as pd
import streamlit as st
import openpyxl
from datetime import datetime


# ==========================================================
# IMPORT COURSES FROM EXCEL
# ==========================================================



def import_courses_from_excel(file_path):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    for row in sheet.iter_rows(min_row=2, values_only=True):

        try:

            course_code = row[0]
            course_name = row[1]
            department = row[2]
            year = row[3]
            semester = row[4]
            credits = row[5]

            cursor.execute("""
                INSERT OR IGNORE INTO courses
                (
                    course_code,
                    course_name,
                    department,
                    year,
                    semester,
                    credits
                )
                VALUES (?,?,?,?,?,?)
            """,
            (
                course_code,
                course_name,
                department,
                year,
                semester,
                credits
            ))

        except:
            pass

    conn.commit()
    conn.close()

    print("Courses Imported Successfully")

# ==========================================================
# IMPORT TIMETABLE FROM EXCEL
# ==========================================================

def import_timetable_from_excel(file_path):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    for row in sheet.iter_rows(min_row=2, values_only=True):

        try:

            department = row[0]
            year = row[1]
            semester = row[2]
            section = row[3]
            day = row[4]
            slot = row[5]
            start_time = row[6]
            end_time = row[7]
            course_code = row[8]
            course_name = row[9]
            faculty_name = row[10]
            room_number = row[11]

            cursor.execute("""
            INSERT INTO timetable(
                department,
                year,
                semester,
                section,
                day,
                slot,
                start_time,
                end_time,
                course_code,
                course_name,
                faculty_name,
                room_number
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                department,
                year,
                semester,
                section,
                day,
                slot,
                start_time,
                end_time,
                course_code,
                course_name,
                faculty_name,
                room_number
            ))

        except:
            pass

    conn.commit()
    conn.close()

    print("Timetable Imported Successfully")



# ==========================================================
# EMAIL VERIFICATION / OTP
# ==========================================================

from datetime import datetime, timedelta


def create_email_verification(student_id, email, otp, expiry_minutes=10):
    """
    Store an email verification OTP for a student.
    """

    connection = get_connection()
    cursor = connection.cursor()

    expires_at = datetime.now() + timedelta(
        minutes=expiry_minutes
    )

    cursor.execute(
        """
        INSERT INTO email_verifications
        (
            student_id,
            email,
            otp,
            expires_at,
            verified
        )
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            student_id,
            email,
            otp,
            expires_at
        )
    )

    connection.commit()

    verification_id = cursor.lastrowid

    connection.close()

    return verification_id


def verify_email_otp(student_id, email, otp):
    """
    Verify the latest OTP sent to the student's email.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM email_verifications
        WHERE student_id = ?
        AND email = ?
        AND verified = 0
        ORDER BY verification_id DESC
        LIMIT 1
        """,
        (
            student_id,
            email
        )
    )

    verification = cursor.fetchone()

    if verification is None:
        connection.close()
        return False

    expires_at = verification["expires_at"]

    # SQLite may return the timestamp as text
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(
                expires_at
            )
        except ValueError:
            connection.close()
            return False

    if datetime.now() > expires_at:
        connection.close()
        return False

    if str(verification["otp"]) != str(otp).strip():
        connection.close()
        return False

    cursor.execute(
        """
        UPDATE email_verifications
        SET verified = 1
        WHERE verification_id = ?
        """,
        (
            verification["verification_id"],
        )
    )

    cursor.execute(
    """
    UPDATE students
    SET
        email_verified = 1,
        account_status = 'Pending Approval'
    WHERE student_id = ?
    """,
    (student_id,)
)
    connection.commit()

    connection.close()

    return True

# =======================================================
# IMPORT COURSES FROM CSV
# =======================================================

def import_courses_from_csv():

    csv_path = Path(__file__).resolve().parent / "dataset" / "courses.csv"

    if not csv_path.exists():
        print("Error: courses.csv not found.")
        return False

    connection = get_connection()
    cursor = connection.cursor()

    try:

        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():

            cursor.execute("""
                INSERT OR IGNORE INTO courses(
                    course_code,
                    course_name,
                    department,
                    year,
                    semester,
                    credits,
                    course_type,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["course_code"],
                row["course_name"],
                row["department"],
                int(row["year"]),
                int(row["semester"]),
                int(row["credits"]),
                row["course_type"],
                row["status"]
            ))

        connection.commit()

        print("Courses imported successfully.")
        print(f"Total course records: {len(df)}")

        return True

    except Exception as error:

        print(f"Course Import Error: {error}")
        return False

    finally:

        connection.close()

# ==========================================================
# SEMESTER COURSE STRUCTURE OPERATIONS
# ==========================================================

def create_semester_structure(
    department,
    year,
    semester,
    academic_batch
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO semester_course_structure(
                department,
                year,
                semester,
                academic_batch
            )
            VALUES (?, ?, ?, ?)
        """, (
            department,
            year,
            semester,
            academic_batch
        ))

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        return None

    finally:

        connection.close()

def get_semester_structure(
    department,
    year,
    semester,
    academic_batch
):
    connection = get_connection()

    cursor = connection.cursor()

    # ------------------------------------------------------
    # 1. FIRST CHECK EXACT ACADEMIC BATCH
    # ------------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM semester_course_structure
        WHERE department = ?
        AND year = ?
        AND semester = ?
        AND academic_batch = ?
        LIMIT 1
    """, (
        department,
        year,
        semester,
        academic_batch
    ))

    structure = cursor.fetchone()


    # ------------------------------------------------------
    # 2. IF NOT FOUND, USE PUBLISHED STRUCTURE
    # ------------------------------------------------------

    if structure is None:

        cursor.execute("""
            SELECT *
            FROM semester_course_structure
            WHERE department = ?
            AND year = ?
            AND semester = ?
            AND is_locked = 1
            ORDER BY structure_id ASC
            LIMIT 1
        """, (
            department,
            year,
            semester
        ))

        structure = cursor.fetchone()


    connection.close()

    return structure

def lock_semester_structure(structure_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE semester_course_structure
        SET is_locked=1
        WHERE structure_id=?
    """, (structure_id,))

    cursor.execute("""
        UPDATE courses
        SET is_locked=1
        WHERE structure_id=?
    """, (structure_id,))

    connection.commit()

    connection.close()

    return True

# ===========================================================
# DATABASE CONFIGURATION
# ===========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "dataset"

DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "student.db"


# ===========================================================
# DATABASE CONNECTION
# ===========================================================

def get_connection():
    """
    Returns SQLite database connection.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ===========================================================
# PASSWORD HASHING
# ===========================================================

def hash_password(password: str) -> str:
    """
    Encrypt user password using bcrypt.
    """

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password.encode(),
        salt
    )

    return hashed_password.decode()


# ===========================================================
# DATABASE INITIALIZATION
# ===========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # =======================================================
    # ADMIN TABLE
    # =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS admin(

        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        full_name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL

    )

    """)
# =======================================================
# FACULTY TABLE
# =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS faculty(

    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,

    qualification TEXT,

    experience INTEGER,

    designation TEXT,

    status TEXT DEFAULT 'Active',

    employee_id TEXT UNIQUE NOT NULL,

    full_name TEXT NOT NULL,

    department TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    phone TEXT,

    password TEXT NOT NULL

        )

    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments(

        department_id INTEGER PRIMARY KEY AUTOINCREMENT,

        department_code TEXT UNIQUE,

        department_name TEXT,

        hod_name TEXT

        )
    """)


# =======================================================
# COURSES TABLE
# =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS courses(

    course_id INTEGER PRIMARY KEY AUTOINCREMENT,

    course_code TEXT UNIQUE NOT NULL,

    course_name TEXT NOT NULL,

    department TEXT NOT NULL,

    year INTEGER NOT NULL,

    semester INTEGER NOT NULL,

    credits INTEGER DEFAULT 3,

    course_type TEXT DEFAULT 'Theory',

    status TEXT DEFAULT 'Active'

)
""")
# ==========================================================
# COURSE STRUCTURE LINK
# ==========================================================

    cursor.execute("PRAGMA table_info(courses)")

    course_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "structure_id" not in course_columns:
        cursor.execute("""
            ALTER TABLE courses
            ADD COLUMN structure_id INTEGER
        """)

    if "is_locked" not in course_columns:
        cursor.execute("""
            ALTER TABLE courses
            ADD COLUMN is_locked INTEGER DEFAULT 0
        """)
# ==========================================================
# SEMESTER COURSE STRUCTURE
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS semester_course_structure(

    structure_id INTEGER PRIMARY KEY AUTOINCREMENT,

    department TEXT NOT NULL,

    year INTEGER NOT NULL,

    semester INTEGER NOT NULL,

    academic_batch TEXT,

    is_locked INTEGER DEFAULT 0,

    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(department, year, semester, academic_batch)

)
""")
    
# ==========================================================
# TIMETABLE TABLE
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS timetable (

    timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,

    department TEXT,

    year INTEGER,

    semester INTEGER,

    section TEXT,

    day TEXT,

    slot TEXT,

    start_time TEXT,

    end_time TEXT,

    course_code TEXT,

    course_name TEXT,

    faculty_name TEXT,

    room_number TEXT

)
""")
    # ==========================================================
    # FACULTY COURSE MAPPING
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty_course_mapping (

    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,

    faculty_id INTEGER,

    course_id INTEGER,

    semester INTEGER,

    FOREIGN KEY(faculty_id) REFERENCES faculty(faculty_id),

    FOREIGN KEY(course_id) REFERENCES courses(course_id)

)
""")
    # ==========================================================
    # FACULTY SECTION MAPPING
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty_section_mapping (

    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,

    faculty_id INTEGER,

    section TEXT,

    year INTEGER,

    semester INTEGER,

    department TEXT,

    FOREIGN KEY(faculty_id) REFERENCES faculty(faculty_id)

)
""")
    cursor.execute("""

CREATE TABLE IF NOT EXISTS sections(

section_id INTEGER PRIMARY KEY AUTOINCREMENT,

department TEXT,

year INTEGER,

semester INTEGER,

section_name TEXT,

room_number TEXT

)

""")
    # =======================================================
    # STUDENT TABLE
    # =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS students(

    student_id INTEGER PRIMARY KEY AUTOINCREMENT,

    roll_number TEXT UNIQUE NOT NULL,

    full_name TEXT NOT NULL,

    gender TEXT,

    admission_year INTEGER,

    current_year INTEGER,

    section TEXT,

    department TEXT NOT NULL,

    semester INTEGER,

    email TEXT UNIQUE NOT NULL,

    phone TEXT,

    password TEXT NOT NULL,

    cgpa REAL DEFAULT 0,

    status TEXT DEFAULT 'Active',

    attendance_percentage REAL DEFAULT 0,

    lms_login_frequency INTEGER DEFAULT 0,

    time_spent_learning REAL DEFAULT 0,

    communication_skills INTEGER DEFAULT 0,

    discipline_score INTEGER DEFAULT 0,

    assignment_marks REAL DEFAULT 0,

    quiz_marks REAL DEFAULT 0,

    mid_exam_marks REAL DEFAULT 0,

    end_sem_marks REAL DEFAULT 0,

    lab_marks REAL DEFAULT 0

)

""")

    # ==========================================================
# FEE PAYMENT
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS fee_payments(
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    amount REAL NOT NULL,
    payment_mode TEXT NOT NULL,
    transaction_id TEXT UNIQUE NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status TEXT DEFAULT 'Paid',
    FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
        """)


# ==========================================================
# SEMESTER REGISTRATION
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS semester_registrations(
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    structure_id INTEGER,
    academic_year TEXT,
    semester INTEGER,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Registered',
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(structure_id) REFERENCES semester_course_structure(structure_id)
)
""")


# ==========================================================
# STUDENT REGISTERED COURSES
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS student_registered_courses(
    registration_course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id INTEGER,
    student_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY(registration_id)
        REFERENCES semester_registrations(registration_id),
    FOREIGN KEY(student_id)
        REFERENCES students(student_id),
    FOREIGN KEY(course_id)
        REFERENCES courses(course_id),
    UNIQUE(registration_id, course_id)
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects(
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT UNIQUE,
    subject_name TEXT,
    department TEXT,
    semester INTEGER
)
""")

# ==========================================================
# STUDENT COURSE MAPPING
# ==========================================================

    cursor.execute("""
CREATE TABLE IF NOT EXISTS student_course_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER,

    course_id INTEGER,

    semester INTEGER,

    FOREIGN KEY(student_id) REFERENCES students(student_id),

    FOREIGN KEY(course_id) REFERENCES courses(course_id)

)
""")
# ==========================================================
# GENERATE STUDENT ENROLLMENT NUMBER
# ==========================================================

def generate_enrollment_number(admission_year):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    year_code = str(admission_year)[-2:]

    cursor.execute("""
        SELECT COUNT(*)
        FROM students
        WHERE admission_year = ?
    """, (admission_year,))

    count = cursor.fetchone()[0] + 1

    enrollment_number = f"{year_code}STU{count:04d}"

    conn.close()

    return enrollment_number

# ==========================================================
# GENERATE SECTION
# ==========================================================

def generate_section(student_count):

    sections = [
        "A","B","C","D","E","F",
        "G","H","I","J","K","L"
    ]

    students_per_section = 100

    index = (student_count - 1) // students_per_section

    if index >= len(sections):
        index = len(sections) - 1

    return sections[index]

# ==========================================================
# CALCULATE CURRENT YEAR
# ==========================================================

def calculate_current_year(admission_year):

    current_year = datetime.now().year

    year = current_year - admission_year + 1

    if year < 1:
        year = 1

    elif year > 4:
        year = 4

    return year

# ==========================================================
# CALCULATE SEMESTER
# ==========================================================

def calculate_semester(current_year):

    if current_year == 1:
        return 1

    elif current_year == 2:
        return 3

    elif current_year == 3:
        return 5

    return 7
# ==========================================================
# GET FACULTY BY EMPLOYEE ID
# ==========================================================

def get_faculty_by_employee_id(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM faculty WHERE employee_id=?",
        (employee_id,)
    )

    faculty = cursor.fetchone()

    connection.close()

    return faculty


# ==========================================================
# FEE PAYMENT OPERATIONS
# ==========================================================

def save_fee_payment(
    student_id,
    amount,
    payment_mode,
    transaction_id,
    payment_status="Paid"
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO fee_payments(
                student_id,
                amount,
                payment_mode,
                transaction_id,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_id,
            amount,
            payment_mode,
            transaction_id,
            payment_status
        ))

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        connection.rollback()
        return None

    finally:
        connection.close()


def get_student_payments(student_id):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM fee_payments
        WHERE student_id = ?
        ORDER BY payment_date DESC
    """, (student_id,))

    payments = cursor.fetchall()

    connection.close()

    return payments


# ==========================================================
# SEMESTER REGISTRATION OPERATIONS
# ==========================================================

def register_student_for_semester(
    student_id,
    structure_id,
    academic_year,
    semester,
    course_ids
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Create semester registration
        cursor.execute("""
            INSERT INTO semester_registrations(
                student_id,
                structure_id,
                academic_year,
                semester,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_id,
            structure_id,
            academic_year,
            semester,
            "Registered"
        ))

        registration_id = cursor.lastrowid

        # Register all fixed courses
        for course_id in course_ids:
            cursor.execute("""
                INSERT INTO student_registered_courses(
                    registration_id,
                    student_id,
                    course_id
                )
                VALUES (?, ?, ?)
            """, (
                registration_id,
                student_id,
                course_id
            ))

        connection.commit()

        return registration_id

    except sqlite3.IntegrityError:
        connection.rollback()
        return None

    finally:
        connection.close()


def get_student_semester_registration(
    student_id,
    semester
):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM semester_registrations
        WHERE student_id = ?
        AND semester = ?
        ORDER BY registration_date DESC
        LIMIT 1
    """, (
        student_id,
        semester
    ))

    registration = cursor.fetchone()

    connection.close()

    return registration



# ==========================================================
# UPDATE FACULTY
# ==========================================================

def update_faculty(
    faculty_id,
    full_name,
    department,
    email,
    phone
):

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE faculty
        SET
            full_name=?,
            department=?,
            email=?,
            phone=?
        WHERE faculty_id=?
    """, (
        full_name,
        department,
        email,
        phone,
        faculty_id
    ))

    connection.commit()
    connection.close()

# ==========================================================
# UPDATE FACULTY UI
# ==========================================================

menu = st.session_state.get("menu", globals().get("menu", ""))

if menu == "Update Faculty":

    st.subheader("Update Faculty")

    employee_id = st.text_input("Enter Employee ID")

    if st.button("Search Faculty"):

        faculty = get_faculty_by_employee_id(employee_id)

        if faculty:

            st.session_state.faculty = faculty

        else:

            st.error("Faculty Not Found")

    if "faculty" in st.session_state:

        faculty = st.session_state.faculty

        full_name = st.text_input(
            "Full Name",
            value=faculty["full_name"]
        )

        department = st.text_input(
            "Department",
            value=faculty["department"]
        )

        email = st.text_input(
            "Email",
            value=faculty["email"]
        )

        phone = st.text_input(
            "Phone",
            value=faculty["phone"]
        )

        if st.button("Update Faculty"):

            update_faculty(
                faculty["faculty_id"],
                full_name,
                department,
                email,
                phone
            )

            st.success("Faculty Updated Successfully")

    connection = get_connection()
    cursor = connection.cursor()

    # =======================================================
    # MARKS TABLE
    # =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS marks (

    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,

    subject_id INTEGER,

    FOREIGN KEY(subject_id)
    REFERENCES subjects(subject_id),

    assignment_marks REAL DEFAULT 0,

    quiz_marks REAL DEFAULT 0,

    mid_exam_marks REAL DEFAULT 0,

    end_sem_marks REAL DEFAULT 0,

    lab_marks REAL DEFAULT 0,

    average_marks REAL DEFAULT 0,

    FOREIGN KEY(student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    UNIQUE(student_id, subject_name)

);

    """)

    # =======================================================
    # ATTENDANCE TABLE
    # =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS attendance(

        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id INTEGER UNIQUE,

        total_classes INTEGER,

        attended_classes INTEGER,

        attendance_percentage REAL,

        is_locked INTEGER DEFAULT 0,

        FOREIGN KEY(student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE

    )

    """)

    # =======================================================
    # RECOMMENDATION TABLE
    # =======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS recommendations(

        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id INTEGER,

        performance_prediction TEXT,

        risk_level TEXT,

        recommendation TEXT,

        generated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE

    )

    """)
    

    # =======================================================
    # CREATE DEFAULT ADMIN
    # =======================================================

    cursor.execute(

        "SELECT * FROM admin WHERE username=?",

        ("admin",)

    )

    admin = cursor.fetchone()

    if admin is None:

        cursor.execute("""

        INSERT INTO admin(

            username,

            password,

            full_name,

            email

        )

        VALUES(?,?,?,?)

        """, (

            "admin",

            hash_password("admin123"),

            "System Administrator",

            "admin@college.edu"

        ))

    connection = get_connection()

    print("Database Initialized Successfully.")


# ===========================================================
# MAIN
# ===========================================================

if __name__ == "__main__":

    initialize_database()
    import_courses_from_csv()

# ==========================================================
# GENERATE STUDENT ENROLLMENT NUMBER
# ==========================================================

def generate_enrollment_number(admission_year):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    year_code = str(admission_year)[-2:]

    cursor.execute("""
        SELECT COUNT(*)
        FROM students
        WHERE admission_year = ?
    """, (admission_year,))

    count = cursor.fetchone()[0] + 1

    enrollment_number = f"{year_code}STU{count:04d}"

    conn.close()

    return enrollment_number


# ==========================================================
# UPGRADE STUDENT REGISTRATION SYSTEM
# ==========================================================

def upgrade_student_registration_system():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ------------------------------------------------------
        # CHECK EXISTING STUDENT COLUMNS
        # ------------------------------------------------------

        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]

        new_columns = {

            "date_of_birth":
                "TEXT",

            "father_name":
                "TEXT",

            "mother_name":
                "TEXT",

            "address":
                "TEXT",

            "admission_session":
                "TEXT",

            "email_verified":
                "INTEGER DEFAULT 0",

            "account_status":
                "TEXT DEFAULT 'Pending'",

            "created_at":
                "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        for column, definition in new_columns.items():

            if column not in columns:

                cursor.execute(
                    f"""
                    ALTER TABLE students
                    ADD COLUMN {column} {definition}
                    """
                )

                print(
                    f"Added student column: {column}"
                )

        # ------------------------------------------------------
        # EMAIL VERIFICATION TABLE
        # ------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications(

            verification_id
                INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id
                INTEGER NOT NULL,

            email
                TEXT NOT NULL,

            otp
                TEXT NOT NULL,

            expires_at
                TIMESTAMP NOT NULL,

            verified
                INTEGER DEFAULT 0,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES students(student_id)
                ON DELETE CASCADE
        )
        """)

        # ------------------------------------------------------
        # ENSURE ENROLLMENT NUMBER COLUMN EXISTS
        # ------------------------------------------------------

        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]

        if "enrollment_no" not in columns:

            cursor.execute("""
            ALTER TABLE students
            ADD COLUMN enrollment_no TEXT
            """)

            print(
                "Added column: enrollment_no"
            )

        # ------------------------------------------------------
        # CREATE UNIQUE INDEX FOR ENROLLMENT NUMBER
        # ------------------------------------------------------

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_students_enrollment_no
        ON students(enrollment_no)
        WHERE enrollment_no IS NOT NULL
        """)

        # ------------------------------------------------------
        # EXISTING STUDENTS
        # ------------------------------------------------------
        #
        # Existing students should remain usable.
        # Therefore mark them as Active if they already
        # have an account.
        # ------------------------------------------------------

        cursor.execute("""
        UPDATE students
        SET account_status = 'Active'
        WHERE account_status IS NULL
        """)

        connection.commit()

        print(
            "Student registration system upgrade completed."
        )

    except Exception as error:

        connection.rollback()

        print(
            f"Student registration upgrade error: {error}"
        )

    finally:

        connection.close()


# ==========================================================
# MAIN DATABASE UPGRADE
# ==========================================================

if __name__ == "__main__":

    initialize_database()

    upgrade_student_registration_system()
# ===========================================================
# STUDENT CRUD OPERATIONS
# ===========================================================
def add_student(
    roll_number,
    full_name,
    gender,
    department,
    semester,
    email,
    phone,
    password,
    cgpa=0.0,
    attendance_percentage=0.0,
    lms_login_frequency=0,
    time_spent_learning=0.0,
    communication_skills=0,
    discipline_score=0,
    admission_year=None,
    current_year=None,
    section=None
):
    """
    Add a new student to the database.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ------------------------------------------------------
        # ADMISSION YEAR
        # ------------------------------------------------------

        if admission_year is None:
            from datetime import datetime
            admission_year = datetime.now().year

        # ------------------------------------------------------
        # CURRENT YEAR
        # ------------------------------------------------------

        if current_year is None:

            from datetime import datetime

            current_calendar_year = datetime.now().year

            current_year = (
                current_calendar_year
                - admission_year
                + 1
            )

            if current_year < 1:
                current_year = 1

            if current_year > 4:
                current_year = 4
            # ------------------------------------------------------
            # AUTOMATIC SEMESTER
            # ------------------------------------------------------

            if current_year == 1:
                semester = 1

            elif current_year == 2:
                semester = 3

            elif current_year == 3:
                semester = 5

            elif current_year == 4:
                semester = 7

            else:
                semester = 1

        # ------------------------------------------------------
        # ENROLLMENT NUMBER
        # Example: 26STU0001
        # ------------------------------------------------------

        enrollment_no = generate_enrollment_number(
            admission_year
        )
        # Use enrollment number as roll number
        roll_number = enrollment_no
        # ------------------------------------------------------
        # SECTION
        # ------------------------------------------------------

        if section is None:

            cursor.execute("""
                SELECT COUNT(*)
                FROM students
                WHERE admission_year = ?
                AND department = ?
                AND current_year = ?
            """, (
                admission_year,
                department,
                current_year
            ))

            student_count = cursor.fetchone()[0] + 1

            sections = [
                "A", "B", "C", "D",
                "E", "F", "G", "H",
                "I", "J", "K", "L"
            ]

            section_index = (
                (student_count - 1) // 50
            )

            if section_index >= len(sections):
                section_index = len(sections) - 1

            section = sections[section_index]

        # ------------------------------------------------------
        # INSERT STUDENT
        # ------------------------------------------------------

        cursor.execute("""
        INSERT INTO students(

            roll_number,
            enrollment_no,
            full_name,
            gender,
            department,
            admission_year,
            current_year,
            semester,
            section,
            email,
            phone,
            password,
            cgpa,
            attendance_percentage,
            lms_login_frequency,
            time_spent_learning,
            communication_skills,
            discipline_score,
            status

        )

        VALUES(
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )

        """, (

            roll_number,
            enrollment_no,
            full_name,
            gender,
            department,
            admission_year,
            current_year,
            semester,
            section,
            email,
            phone,
            hash_password(password),
            cgpa,
            attendance_percentage,
            lms_login_frequency,
            time_spent_learning,
            communication_skills,
            discipline_score,
            "Active"

        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError as error:

        print(f"Database Error : {error}")

        return False

    except Exception as error:

        print(f"Error : {error}")

        return False

    finally:

        connection.close()


# ==========================================================
# NEW STUDENT ACCOUNT CREATION
# ==========================================================

def create_new_student_account(
    full_name,
    date_of_birth,
    gender,
    father_name,
    mother_name,
    address,
    department,
    admission_year,
    admission_session,
    email,
    phone,
    password
):
    """
    Create a new student account for first-time registration.

    This function:
    - Generates the permanent Enrollment Number
    - Creates the student profile
    - Does NOT register a semester
    - Does NOT assign courses
    - Does NOT process fees
    - Starts the account as Pending Verification
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ------------------------------------------------------
        # CHECK EXISTING EMAIL
        # ------------------------------------------------------

        cursor.execute(
            """
            SELECT student_id
            FROM students
            WHERE email = ?
            LIMIT 1
            """,
            (email.strip(),)
        )

        existing_student = cursor.fetchone()

        if existing_student:
            return None

        # ------------------------------------------------------
        # PERMANENT ENROLLMENT NUMBER
        # ------------------------------------------------------

        enrollment_no = generate_enrollment_number(
            admission_year
        )

        # Enrollment number is also used as roll number
        roll_number = enrollment_no

        # ------------------------------------------------------
        # DEFAULT VALUES
        # ------------------------------------------------------

        current_year = 1
        semester = 0
        section = None

        # ------------------------------------------------------
        # CREATE STUDENT
        # ------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO students
            (
                roll_number,
                enrollment_no,
                full_name,
                date_of_birth,
                gender,
                father_name,
                mother_name,
                address,
                department,
                admission_year,
                current_year,
                semester,
                section,
                email,
                phone,
                password,
                email_verified,
                account_status,
                status,
                admission_session,
                cgpa,
                attendance_percentage,
                lms_login_frequency,
                time_spent_learning,
                communication_skills,
                discipline_score
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                roll_number,
                enrollment_no,
                full_name.strip(),
                date_of_birth,
                gender,
                father_name.strip(),
                mother_name.strip(),
                address.strip(),
                department,
                admission_year,
                current_year,
                semester,
                section,
                email.strip(),
                phone.strip(),
                hash_password(password),
                0,
                "Pending Verification",
                "Active",
                admission_session,
                0.0,
                0.0,
                0,
                0.0,
                0,
                0
            )
        )

        connection.commit()

        student_id = cursor.lastrowid

        return {
            "student_id": student_id,
            "enrollment_no": enrollment_no
        }

    except sqlite3.IntegrityError as error:

        connection.rollback()

        print(
            f"Student Account Database Error: {error}"
        )

        return None

    except Exception as error:

        connection.rollback()

        print(
            f"Student Account Error: {error}"
        )

        return None

    finally:

        connection.close()

def upgrade_student_table():
    """
    Add new student registration fields to an existing database.
    Existing student data is preserved.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]

        new_columns = {
            "enrollment_no": "TEXT",
            "admission_year": "INTEGER",
            "current_year": "INTEGER",
            "section": "TEXT",
            "status": "TEXT DEFAULT 'Active'"
        }

        for column, data_type in new_columns.items():

            if column not in columns:

                cursor.execute(
                    f"ALTER TABLE students ADD COLUMN {column} {data_type}"
                )

                print(f"Added column: {column}")

        connection.commit()

        print("Student table upgrade completed.")

    except Exception as error:

        print(f"Student table upgrade error: {error}")

    finally:

        connection.close()

if __name__ == "__main__":
    upgrade_student_table()

# ==========================================================
# DELETE STUDENT
# ==========================================================

def delete_student(student_id):

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE student_id=?",
        (student_id,)
    )

    connection.commit()
    connection.close()


# ==========================================================
# DELETE FACULTY
# ==========================================================

def delete_faculty(faculty_id):

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM faculty WHERE faculty_id=?",
        (faculty_id,)
    )

    connection.commit()
    connection.close()


# -----------------------------------------------------------

def get_student(student_id):
    """
    Return student using Student ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM students WHERE student_id=?",

        (student_id,)

    )

    student = cursor.fetchone()

    connection.close()

    return student


# -----------------------------------------------------------

def get_student_by_roll(roll_number):
    """
    Return student using Roll Number.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM students WHERE roll_number=?",

        (roll_number,)

    )

    student = cursor.fetchone()

    connection.close()

    return student


# -----------------------------------------------------------

def get_student_by_email(email):
    """
    Return student using Email.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM students WHERE email=?",

        (email,)

    )

    student = cursor.fetchone()

    connection.close()

    return student


# -----------------------------------------------------------

def get_all_students():
    """
    Return all students.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM students

    ORDER BY department,
             semester,
             full_name

    """)

    students = cursor.fetchall()

    connection.close()

    return students

# ==========================================================
# UPDATE STUDENT
# ==========================================================

def update_student(

    student_id,
    full_name,
    gender,
    department,
    semester,
    email,
    phone,
    cgpa,
    attendance_percentage,
    lms_login_frequency,
    time_spent_learning,
    communication_skills,
    discipline_score

):
    """
    Update student information.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE students

    SET

        full_name=?,
        gender=?,
        department=?,
        semester=?,
        email=?,
        phone=?,
        cgpa=?,
        attendance_percentage=?,
        lms_login_frequency=?,
        time_spent_learning=?,
        communication_skills=?,
        discipline_score=?

    WHERE student_id=?

    """, (

        full_name,
        gender,
        department,
        semester,
        email,
        phone,
        cgpa,
        attendance_percentage,
        lms_login_frequency,
        time_spent_learning,
        communication_skills,
        discipline_score,
        student_id

    ))

    connection.commit()

    connection.close()



# ===========================================================
# FACULTY CRUD OPERATIONS
# ===========================================================

def add_faculty(
    employee_id,
    full_name,
    department,
    email,
    phone,
    password
):
    """
    Add a new faculty member.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
        INSERT INTO faculty(
            employee_id,
            full_name,
            department,
            email,
            phone,
            password
        )

        VALUES(?,?,?,?,?,?,?)
        """, (

            employee_id,
            full_name,
            department,
            email,
            phone,
            hash_password(password)

        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError as error:

        print(f"Database Error : {error}")

        return False

    finally:

        connection.close()


# -----------------------------------------------------------

def get_faculty(faculty_id):
    """
    Return faculty using Faculty ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM faculty WHERE faculty_id=?",

        (faculty_id,)

    )

    faculty = cursor.fetchone()

    connection.close()

    return faculty





# -----------------------------------------------------------

def get_faculty_by_email(email):
    """
    Return faculty using Email.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM faculty WHERE email=?",

        (email,)

    )

    faculty = cursor.fetchone()

    connection.close()

    return faculty


# -----------------------------------------------------------

def get_all_faculty():
    """
    Return all faculty members.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM faculty

    ORDER BY department,
             full_name

    """)

    faculty = cursor.fetchall()

    connection.close()

    return faculty


# ===========================================================
# ADMIN OPERATIONS
# ===========================================================

def add_admin(username, password, full_name, email):
    """
    Add a new administrator.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
        INSERT INTO admin(
            username,
            password,
            full_name,
            email
        )

        VALUES(?,?,?,?)
        """, (

            username,
            hash_password(password),
            full_name,
            email

        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError as error:

        print(f"Database Error : {error}")

        return False

    finally:

        connection.close()


# ----------------------------------------------------------

def get_admin(username):
    """
    Get admin details using username.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "SELECT * FROM admin WHERE username=?",

        (username,)

    )

    admin = cursor.fetchone()

    connection.close()

    return admin


# ----------------------------------------------------------

def update_admin(admin_id, full_name, email):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE admin

    SET

        full_name=?,
        email=?

    WHERE admin_id=?

    """, (

        full_name,
        email,
        admin_id

    ))

    connection.commit()

    connection.close()


# ----------------------------------------------------------

def delete_admin(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(

        "DELETE FROM admin WHERE admin_id=?",

        (admin_id,)

    )

    connection.commit()

    connection.close()


# ===========================================================
# PASSWORD VERIFICATION
# ===========================================================

def verify_password(plain_password, hashed_password):
    """
    Verify bcrypt password.
    """

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# ===========================================================
# LOGIN FUNCTIONS
# ===========================================================

def student_login(enrollment_no, password):
    """
    Authenticate student using permanent Enrollment Number.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE enrollment_no = ?
        AND account_status = 'Active'
    """, (enrollment_no,))

    student = cursor.fetchone()

    connection.close()

    if student is None:
        return None

    if verify_password(password, student["password"]):
        return student

    return None


# ----------------------------------------------------------

def faculty_login(employee_id, password):
    """
    Authenticate faculty.
    """

    faculty = get_faculty_by_employee_id(employee_id)

    if faculty is None:
        return None

    if verify_password(password, faculty["password"]):
        return faculty

    return None


# ----------------------------------------------------------

def admin_login(username, password):
    """
    Authenticate admin.
    """

    admin = get_admin(username)

    if admin is None:
        return None

    if verify_password(password, admin["password"]):
        return admin

    return None


# ===========================================================
# CHANGE PASSWORD
# ===========================================================

def change_student_password(student_id, new_password):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE students

    SET password=?

    WHERE student_id=?

    """, (

        hash_password(new_password),

        student_id

    ))

    connection.commit()

    connection.close()


# ----------------------------------------------------------

def change_faculty_password(faculty_id, new_password):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE faculty

    SET password=?

    WHERE faculty_id=?

    """, (

        hash_password(new_password),

        faculty_id

    ))

    connection.commit()

    connection.close()


# ----------------------------------------------------------

def change_admin_password(admin_id, new_password):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE admin

    SET password=?

    WHERE admin_id=?

    """, (

        hash_password(new_password),

        admin_id

    ))

    connection.commit()

    connection.close()
# ==========================================================
# GET ALL STUDENTS
# ==========================================================

def get_all_students():
    """
    Return all students.
    """

    connection: sqlite3.Connection = sqlite3.connect(DATABASE_PATH)

    dataframe = pd.read_sql_query(

        """
        SELECT
            student_id,
            roll_number,
            full_name,
            department,
            semester
        FROM students
        ORDER BY roll_number
        """,

        connection

    )

    connection.close()

    return dataframe


# ==========================================================
# GET STUDENT BY ROLL NUMBER
# ==========================================================

def get_student_by_roll(roll_number):
    """
    Return complete student details.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(

        """
        SELECT *

        FROM students

        WHERE roll_number = ?

        """,

        (roll_number,)

    )

    row = cursor.fetchone()

    connection.close()

    if row:

        return dict(row)
 
    return None

def update_student_marks(
    student_id,
    assignment_marks,
    quiz_marks,
    mid_exam_marks,
    end_sem_marks,
    lab_marks
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE students
        SET assignment_marks=?,
            quiz_marks=?,
            mid_exam_marks=?,
            end_sem_marks=?,
            lab_marks=?
        WHERE student_id=?
    """, (
        assignment_marks,
        quiz_marks,
        mid_exam_marks,
        end_sem_marks,
        lab_marks,
        student_id
    ))

    connection.commit()
    connection.close()

# ===========================================================
# MARKS OPERATIONS
# ===========================================================

def calculate_average_marks(
    assignment_marks,
    quiz_marks,
    mid_exam_marks,
    end_sem_marks,
    lab_marks
):
    """
    Calculate average marks.
    """

    return round(

        (
            assignment_marks +
            quiz_marks +
            mid_exam_marks +
            end_sem_marks +
            lab_marks

        ) / 5,

        2

    )


# -----------------------------------------------------------

def add_or_update_marks(

    student_id,
    subject_name,
    assignment_marks,
    quiz_marks,
    mid_exam_marks,
    end_sem_marks,
    lab_marks

):
    """
    Insert or update subject marks.
    """

    average_marks = calculate_average_marks(

        assignment_marks,
        quiz_marks,
        mid_exam_marks,
        end_sem_marks,
        lab_marks

    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT mark_id

    FROM marks

    WHERE student_id=?

    AND subject_name=?

    """,

    (

        student_id,
        subject_name

    ))

    record = cursor.fetchone()

    if record:

        cursor.execute("""

        UPDATE marks

        SET

            assignment_marks=?,
            quiz_marks=?,
            mid_exam_marks=?,
            end_sem_marks=?,
            lab_marks=?,
            average_marks=?

        WHERE student_id=?

        AND subject_name=?

        """,

        (

            assignment_marks,
            quiz_marks,
            mid_exam_marks,
            end_sem_marks,
            lab_marks,
            average_marks,
            student_id,
            subject_name

        ))

    else:

        cursor.execute("""

        INSERT INTO marks(

            student_id,
            subject_name,
            assignment_marks,
            quiz_marks,
            mid_exam_marks,
            end_sem_marks,
            lab_marks,
            average_marks

        )

        VALUES(?,?,?,?,?,?,?,?)

        """,

        (

            student_id,
            subject_name,
            assignment_marks,
            quiz_marks,
            mid_exam_marks,
            end_sem_marks,
            lab_marks,
            average_marks

        ))

    connection.commit()

    connection.close()


# -----------------------------------------------------------

def update_student_attendance(student_id, attendance):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE students
        SET attendance_percentage=?
        WHERE student_id=?
    """, (
        attendance,
        student_id
    ))

    connection.commit()
    connection.close()
    """
    Return all subject marks of a student.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM marks

    WHERE student_id=?

    ORDER BY subject_name

    """,

    (

        student_id,

    ))

    marks = cursor.fetchall()

    connection.close()

    return marks


# -----------------------------------------------------------

def get_subject_marks(subject_name):
    """
    Return all marks for a subject.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM marks

    WHERE subject_name=?

    """,

    (

        subject_name,

    ))

    marks = cursor.fetchall()

    connection.close()

    return marks


# -----------------------------------------------------------

def delete_subject_marks(
    student_id,
    subject_name
):
    """
    Delete marks of one subject.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    DELETE FROM marks

    WHERE student_id=?

    AND subject_name=?

    """,

    (

        student_id,
        subject_name

    ))

    connection.commit()

    connection.close()

# ===========================================================
# ATTENDANCE OPERATIONS
# ===========================================================

def calculate_attendance_percentage(
    attended_classes,
    total_classes
):
    """
    Calculate attendance percentage.
    """

    if total_classes <= 0:
        return 0.0

    return round(
        (attended_classes / total_classes) * 100,
        2
    )


# -----------------------------------------------------------

def add_or_update_attendance(
    student_id,
    total_classes,
    attended_classes
):
    """
    Add or update attendance.
    Attendance cannot be edited after it is locked.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT attendance_id,
           is_locked

    FROM attendance

    WHERE student_id=?

    """,

    (student_id,))

    record = cursor.fetchone()

    attendance_percentage = calculate_attendance_percentage(
        attended_classes,
        total_classes
    )

    if record:

        if record["is_locked"] == 1:

            connection.close()

            return False

        cursor.execute("""

        UPDATE attendance

        SET

            total_classes=?,
            attended_classes=?,
            attendance_percentage=?

        WHERE student_id=?

        """,

        (
            total_classes,
            attended_classes,
            attendance_percentage,
            student_id
        ))

    else:

        cursor.execute("""

        INSERT INTO attendance(

            student_id,
            total_classes,
            attended_classes,
            attendance_percentage

        )

        VALUES(?,?,?,?)

        """,

        (
            student_id,
            total_classes,
            attended_classes,
            attendance_percentage
        ))

    cursor.execute("""

    UPDATE students

    SET attendance_percentage=?

    WHERE student_id=?

    """,

    (
        attendance_percentage,
        student_id
    ))

    connection.commit()

    connection.close()

    return True


# -----------------------------------------------------------

def get_attendance(student_id):
    """
    Get attendance of one student.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM attendance

    WHERE student_id=?

    """,

    (student_id,))

    attendance = cursor.fetchone()

    connection.close()

    return attendance


# -----------------------------------------------------------

def lock_attendance(student_id):
    """
    Lock attendance after faculty submits.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE attendance

    SET is_locked=1

    WHERE student_id=?

    """,

    (student_id,))

    connection.commit()

    connection.close()


# -----------------------------------------------------------

def unlock_attendance(student_id):
    """
    Admin can unlock attendance if required.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    UPDATE attendance

    SET is_locked=0

    WHERE student_id=?

    """,

    (student_id,))

    connection.commit()

    connection.close()


# -----------------------------------------------------------

def delete_attendance(student_id):
    """
    Delete attendance record.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    DELETE FROM attendance

    WHERE student_id=?

    """,

    (student_id,))

    connection.commit()

    connection.close()


# -----------------------------------------------------------

def get_low_attendance_students(threshold=75):
    """
    Return students whose attendance is below threshold.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT

        s.student_id,
        s.roll_number,
        s.full_name,
        s.department,
        s.semester,
        a.attendance_percentage

    FROM students s

    JOIN attendance a

    ON s.student_id = a.student_id

    WHERE a.attendance_percentage < ?

    ORDER BY a.attendance_percentage ASC

    """,

    (threshold,))

    students = cursor.fetchall()

    connection.close()

    return students

# ===========================================================
# RECOMMENDATION OPERATIONS
# ===========================================================

def save_recommendation(
    student_id,
    performance_prediction,
    risk_level,
    recommendation
):
    """
    Save AI recommendation for a student.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    INSERT INTO recommendations(

        student_id,
        performance_prediction,
        risk_level,
        recommendation

    )

    VALUES(?,?,?,?)

    """,

    (

        student_id,
        performance_prediction,
        risk_level,
        recommendation

    ))

    connection.commit()

    connection.close()


# -----------------------------------------------------------

def get_student_recommendations(student_id):
    """
    Get all recommendations of a student.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""

    SELECT *

    FROM recommendations

    WHERE student_id=?

    ORDER BY generated_on DESC

    """,

    (

        student_id,

    ))

    recommendations = cursor.fetchall()

    connection.close()

    return recommendations


# ===========================================================
# DASHBOARD STATISTICS
# ===========================================================

def get_dashboard_statistics():
    """
    Return dashboard statistics.
    """

    connection = get_connection()

    cursor = connection.cursor()

    statistics = {}

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    statistics["total_students"] = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM faculty"
    )

    statistics["total_faculty"] = cursor.fetchone()[0]

    cursor.execute("""

    SELECT COUNT(*)

    FROM attendance

    WHERE attendance_percentage < 75

    """)

    statistics["low_attendance"] = cursor.fetchone()[0]

    cursor.execute("""

    SELECT COUNT(*)

    FROM recommendations

    WHERE risk_level='High'

    """)

    statistics["high_risk_students"] = cursor.fetchone()[0]

    cursor.execute("""

    SELECT AVG(cgpa)

    FROM students

    """)

    cgpa = cursor.fetchone()[0]

    statistics["average_cgpa"] = round(cgpa, 2) if cgpa else 0

    connection.close()

    return statistics


# ===========================================================
# SEARCH FUNCTIONS
# ===========================================================

def search_students(keyword):
    """
    Search students by
    Roll Number,
    Name,
    Department.
    """

    connection = get_connection()

    cursor = connection.cursor()

    keyword = f"%{keyword}%"

    cursor.execute("""

    SELECT *

    FROM students

    WHERE

    roll_number LIKE ?

    OR

    full_name LIKE ?

    OR

    department LIKE ?

    ORDER BY full_name

    """,

    (

        keyword,
        keyword,
        keyword

    ))

    students = cursor.fetchall()

    connection.close()

    return students

# =========================================================
# STUDENT APPROVAL SYSTEM
# =========================================================

def upgrade_student_approval_system():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in cursor.fetchall()]

        new_columns = {
            "approved_by": "TEXT",
            "approved_at": "TIMESTAMP",
            "rejection_reason": "TEXT"
        }

        for column, data_type in new_columns.items():

            if column not in columns:

                cursor.execute(
                    f"ALTER TABLE students ADD COLUMN {column} {data_type}"
                )

                print(f"Added student approval column: {column}")

        connection.commit()

        print("Student approval system upgrade completed.")

    except Exception as error:

        connection.rollback()
        print(f"Student approval upgrade error: {error}")

    finally:

        connection.close()

if __name__ == "__main__":
    initialize_database()
    upgrade_student_registration_system()
    upgrade_student_approval_system()

# =========================================================
# GET PENDING STUDENT APPLICATIONS
# =========================================================

def get_pending_student_applications():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            student_id,
            enrollment_no,
            full_name,
            date_of_birth,
            gender,
            father_name,
            mother_name,
            address,
            department,
            admission_year,
            admission_session,
            email,
            phone,
            email_verified,
            account_status,
            created_at
        FROM students
        WHERE account_status = 'Pending Approval'
        AND email_verified = 1
        ORDER BY student_id DESC
    """)

    students = cursor.fetchall()

    connection.close()

    return students


# =========================================================
# APPROVE STUDENT
# =========================================================

def approve_student(student_id, approved_by="Admin"):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE students
            SET
                account_status = 'Active',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                rejection_reason = NULL
            WHERE student_id = ?
            AND email_verified = 1
            AND account_status = 'Pending Approval'
        """, (
            approved_by,
            student_id
        ))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as error:

        connection.rollback()

        print(
            f"Student approval error: {error}"
        )

        return False

    finally:

        connection.close()


# =========================================================
# REJECT STUDENT
# =========================================================

def reject_student(
    student_id,
    reason="",
    rejected_by="Admin"
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE students
            SET
                account_status = 'Rejected',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                rejection_reason = ?
            WHERE student_id = ?
            AND email_verified = 1
            AND account_status = 'Pending Approval'
        """, (
            rejected_by,
            reason,
            student_id
        ))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as error:

        connection.rollback()

        print(
            f"Student rejection error: {error}"
        )

        return False

    finally:

        connection.close()
# =========================================================
# GET PENDING STUDENT APPLICATIONS
# =========================================================

def get_pending_student_applications():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            student_id,
            enrollment_no,
            full_name,
            date_of_birth,
            gender,
            father_name,
            mother_name,
            address,
            department,
            admission_year,
            admission_session,
            email,
            phone,
            email_verified,
            account_status,
            created_at
        FROM students
        WHERE account_status = 'Pending Approval'
        AND email_verified = 1
        ORDER BY student_id DESC
    """)

    students = cursor.fetchall()

    connection.close()

    return students


# =========================================================
# APPROVE STUDENT
# =========================================================

def approve_student(student_id, approved_by="Admin"):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE students
            SET
                account_status = 'Active',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                rejection_reason = NULL
            WHERE student_id = ?
            AND email_verified = 1
            AND account_status = 'Pending Approval'
        """, (
            approved_by,
            student_id
        ))

        connection.commit()

        success = cursor.rowcount > 0

        return success

    except Exception as error:

        connection.rollback()
        print(f"Student approval error: {error}")

        return False

    finally:

        connection.close()


# =========================================================
# REJECT STUDENT
# =========================================================

def reject_student(student_id, reason="", rejected_by="Admin"):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE students
            SET
                account_status = 'Rejected',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                rejection_reason = ?
            WHERE student_id = ?
            AND email_verified = 1
            AND account_status = 'Pending Approval'
        """, (
            rejected_by,
            reason,
            student_id
        ))

        connection.commit()

        success = cursor.rowcount > 0

        return success

    except Exception as error:

        connection.rollback()
        print(f"Student rejection error: {error}")

        return False

    finally:

        connection.close()


# ==========================================================
# GET STUDENT REGISTERED COURSES
# ==========================================================

def get_student_registered_courses(student_id, semester=None):
    connection = get_connection()
    cursor = connection.cursor()

    if semester is None:
        cursor.execute("""
            SELECT
                src.*,
                c.course_code,
                c.course_name,
                c.credits,
                c.course_type,
                sr.academic_year,
                sr.semester,
                sr.status AS registration_status
            FROM student_registered_courses src
            JOIN courses c
                ON src.course_id = c.course_id
            JOIN semester_registrations sr
                ON src.registration_id = sr.registration_id
            WHERE src.student_id = ?
            ORDER BY sr.semester DESC, c.course_code
        """, (student_id,))
    else:
        cursor.execute("""
            SELECT
                src.*,
                c.course_code,
                c.course_name,
                c.credits,
                c.course_type,
                sr.academic_year,
                sr.semester,
                sr.status AS registration_status
            FROM student_registered_courses src
            JOIN courses c
                ON src.course_id = c.course_id
            JOIN semester_registrations sr
                ON src.registration_id = sr.registration_id
            WHERE src.student_id = ?
            AND sr.semester = ?
            ORDER BY c.course_code
        """, (student_id, semester))

    rows = cursor.fetchall()

    connection.close()

    return rows

# ===========================================================
# DATABASE UTILITIES
# ===========================================================

def reset_database():
    """
    Delete all records.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("DELETE FROM recommendations")

    cursor.execute("DELETE FROM attendance")

    cursor.execute("DELETE FROM marks")

    cursor.execute("DELETE FROM students")

    cursor.execute("DELETE FROM faculty")

    connection.commit()

    connection.close()





# ===========================================================
# MAIN
# ===========================================================

if __name__ == "__main__":

    initialize_database()

    print("=" * 50)

    print("AI Academic Decision System")

    print("Database Created Successfully")

    print(f"Database Location : {DATABASE_PATH}")

    print("=" * 50)
