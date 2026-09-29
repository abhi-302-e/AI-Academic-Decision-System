import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from database import (
    get_connection,
    create_semester_structure,
    get_semester_structure,
    lock_semester_structure
)

st.set_page_config(
    page_title="Course Management",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Course & Semester Structure Management")
st.divider()


# ==========================================================
# SELECT SEMESTER STRUCTURE
# ==========================================================

st.subheader("🎓 Create / Manage Semester Course Structure")

col1, col2, col3, col4 = st.columns(4)

with col1:
    department = st.selectbox(
        "Department",
        ["CSE"]
    )

with col2:
    year = st.selectbox(
        "Year",
        [1, 2, 3, 4]
    )

with col3:
    semester = st.selectbox(
        "Semester",
        [1, 2, 3, 4, 5, 6, 7, 8]
    )

with col4:
    academic_batch = st.text_input(
        "Academic Batch",
        value="2026-27"
    )


# ==========================================================
# GET EXISTING STRUCTURE
# ==========================================================

structure = get_semester_structure(
    department,
    year,
    semester,
    academic_batch
)


# ==========================================================
# CREATE STRUCTURE
# ==========================================================

if structure is None:

    st.info(
        "No course structure exists for this Year and Semester."
    )

    if st.button(
        "➕ Create Semester Structure",
        type="primary"
    ):

        structure_id = create_semester_structure(
            department,
            year,
            semester,
            academic_batch
        )

        if structure_id:

            st.success(
                "Semester course structure created successfully."
            )

            st.rerun()

        else:

            st.error(
                "Structure already exists or could not be created."
            )

else:

    structure_id = structure["structure_id"]
    is_locked = structure["is_locked"]

    if is_locked:

        st.success(
            "🔒 This semester course structure is PUBLISHED and LOCKED."
        )

        st.warning(
            "Courses in this structure cannot be changed."
        )

    else:

        st.warning(
            "⚠️ This structure is not published yet."
        )


st.divider()


# ==========================================================
# ADD COURSE TO STRUCTURE
# ==========================================================

if structure is not None and not structure["is_locked"]:

    st.subheader("➕ Add Fixed Course")

    col1, col2 = st.columns(2)

    with col1:

        course_code = st.text_input(
            "Course Code",
            key="course_code"
        )

        course_name = st.text_input(
            "Course Name",
            key="course_name"
        )

        credits = st.number_input(
            "Credits",
            min_value=1,
            max_value=10,
            value=3
        )

    with col2:

        course_type = st.selectbox(
            "Course Type",
            [
                "Theory",
                "Lab",
                "Theory+Lab"
            ]
        )

    if st.button(
        "Add Course to Semester",
        type="primary"
    ):

        if not course_code.strip() or not course_name.strip():

            st.error(
                "Please enter Course Code and Course Name."
            )

        else:

            conn = get_connection()

            try:

                # Check whether course already exists
                existing = conn.execute(
                    """
                    SELECT course_id
                    FROM courses
                    WHERE course_code = ?
                    """,
                    (course_code.strip(),)
                ).fetchone()

                if existing:

                    course_id = existing["course_id"]

                    # Check if already linked
                    linked = conn.execute(
                        """
                        SELECT course_id
                        FROM courses
                        WHERE course_id = ?
                        AND structure_id = ?
                        """,
                        (
                            course_id,
                            structure_id
                        )
                    ).fetchone()

                    if linked:

                        st.warning(
                            "This course is already in this structure."
                        )

                    else:

                        conn.execute(
                            """
                            UPDATE courses
                            SET structure_id = ?,
                                is_locked = 0,
                                course_name = ?,
                                department = ?,
                                year = ?,
                                semester = ?,
                                credits = ?,
                                course_type = ?,
                                status = 'Active'
                            WHERE course_id = ?
                            """,
                            (
                                structure_id,
                                course_name.strip(),
                                department,
                                year,
                                semester,
                                credits,
                                course_type,
                                course_id
                            )
                        )

                        conn.commit()

                        st.success(
                            "Existing course added to the semester structure."
                        )

                        st.rerun()

                else:

                    conn.execute(
                        """
                        INSERT INTO courses
                        (
                            course_code,
                            course_name,
                            department,
                            year,
                            semester,
                            credits,
                            course_type,
                            status,
                            structure_id,
                            is_locked
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            course_code.strip(),
                            course_name.strip(),
                            department,
                            year,
                            semester,
                            credits,
                            course_type,
                            "Active",
                            structure_id,
                            0
                        )
                    )

                    conn.commit()

                    st.success(
                        "Course added successfully."
                    )

                    st.rerun()

            except Exception as error:

                st.error(
                    f"Error: {error}"
                )

            finally:

                conn.close()


# ==========================================================
# SHOW COURSES IN CURRENT STRUCTURE
# ==========================================================

if structure is not None:

    st.subheader(
        f"📚 Courses — Year {year}, Semester {semester}"
    )

    conn = get_connection()

    courses = conn.execute(
        """
        SELECT
            course_id,
            course_code,
            course_name,
            credits,
            course_type,
            status,
            is_locked
        FROM courses
        WHERE structure_id = ?
        ORDER BY course_code
        """,
        (structure_id,)
    ).fetchall()

    conn.close()

    if not courses:

        st.info(
            "No courses have been added to this structure yet."
        )

    else:

        for course in courses:

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write(
                        f"**{course['course_code']}**"
                    )

                with col2:
                    st.write(
                        course["course_name"]
                    )

                with col3:
                    st.write(
                        f"Credits: {course['credits']}"
                    )

                with col4:
                    st.write(
                        course["course_type"]
                    )


        st.write("")

        # ==================================================
        # PUBLISH / LOCK
        # ==================================================

        if not structure["is_locked"]:

            st.warning(
                "⚠️ After publishing, the course structure "
                "cannot be changed."
            )

            confirm_lock = st.checkbox(
                "I confirm that these are the final fixed courses."
            )

            if st.button(
                "🔒 Publish & Lock Course Structure",
                type="primary"
            ):

                if not confirm_lock:

                    st.error(
                        "Please confirm that the course list is final."
                    )

                else:

                    lock_semester_structure(
                        structure_id
                    )

                    st.success(
                        "✅ Course structure published and locked successfully."
                    )

                    st.rerun()

        else:

            st.success(
                "🔒 Published — Students will use this fixed course structure."
            )