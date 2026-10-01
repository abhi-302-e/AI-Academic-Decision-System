import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from auth import require_admin
from database import (
    get_connection,
    create_semester_structure,
    get_semester_structure,
    lock_semester_structure,
    import_academic_schedule,
)
from preprocessing.academic_schedule_import import parse_academic_workbooks

require_admin()

st.title("📚 Course & Semester Structure Management")
st.subheader("Import academic courses and timetable")

st.info("Upload both Excel files to preview and import the academic schedule.")
master_upload = st.file_uploader(
    "Upload master course workbook",
    type=["xlsx"],
    key="academic_master_upload"
)
section_upload = st.file_uploader(
    "Upload sectionwise timetable workbook",
    type=["xlsx"],
    key="academic_sections_upload"
)

master_bytes = master_upload.getvalue() if master_upload else None
section_bytes = section_upload.getvalue() if section_upload else None
master_name = master_upload.name if master_upload else None
section_name = section_upload.name if section_upload else None

academic_batch = st.text_input("Academic batch", value="2026-27", key="import_academic_batch")
st.warning(
    "The timetable sheets are labeled A.Y. 2025–2026, while both workbook filenames say 2026–2027. "
    "Confirm the intended batch before publishing."
)
confirm_year = st.checkbox(
    "I confirm these timetables belong to the selected academic batch.",
    key="confirm_schedule_batch"
)

if st.button("Preview workbook import", type="primary", disabled=not (master_bytes and section_bytes)):
    try:
        preview = parse_academic_workbooks(master_bytes, section_bytes, academic_batch.strip())
        st.session_state.schedule_import_preview = preview
        st.session_state.schedule_import_sources = (master_name, section_name, academic_batch.strip())
    except Exception as error:
        st.error(f"Could not parse these workbooks: {error}")

preview = st.session_state.get("schedule_import_preview")
preview_sources = st.session_state.get("schedule_import_sources")
if preview and preview_sources == (master_name, section_name, academic_batch.strip()):
    st.markdown("#### Import preview")
    metric_cols = st.columns(4)
    for column, label, key in zip(
        metric_cols,
        ["Course offerings", "Semester structures", "Sections", "Timetable periods"],
        ["courses", "structures", "sections", "timetable"],
    ):
        column.metric(label, len(preview[key]))

    if preview.get("conflicts"):
        st.error(f"{len(preview['conflicts'])} conflicting section-period assignments will be omitted from the timetable.")
        st.dataframe(pd.DataFrame(preview["conflicts"]), use_container_width=True, hide_index=True)
    if preview.get("warnings"):
        with st.expander("Import warnings"):
            for warning in preview["warnings"]:
                st.warning(warning)

    if st.button("Import and publish courses and timetable", disabled=not confirm_year):
        try:
            result = import_academic_schedule(preview)
            st.session_state.schedule_import_preview = None
            st.session_state.schedule_import_sources = None
            st.success(
                "Academic schedule created and published: "
                f"{result['courses']} course offerings, "
                f"{result['sections_added']} new sections, "
                f"{result['timetable_added']} timetable periods."
            )
            st.info(
                f"Skipped {result['timetable_skipped']} already-imported periods and "
                f"{result['conflicts_skipped']} conflicting source periods."
            )
            st.rerun()
        except Exception as error:
            st.error(f"Import failed; no partial schedule was kept: {error}")

st.divider()


# ==========================================================
# SELECT SEMESTER STRUCTURE
# ==========================================================

st.subheader("🎓 Create / Manage Semester Course Structure")

structure_connection = get_connection()
department_options = [
    row["department"]
    for row in structure_connection.execute(
        "SELECT DISTINCT department FROM semester_course_structure ORDER BY department"
    ).fetchall()
]

col1, col2, col3, col4 = st.columns(4)

with col1:
    department = st.selectbox(
        "Department",
        department_options or ["CSE"]
    )

with col4:
    academic_batch = st.text_input(
        "Academic Batch",
        value="2026-27"
    )

with col2:
    year = st.selectbox(
        "Year",
        sorted({row["year"] for row in structure_connection.execute(
            "SELECT year FROM semester_course_structure WHERE department = ? AND academic_batch = ?",
            (department, academic_batch)
        ).fetchall()}) or [1, 2, 3, 4]
    )

with col3:
    semester = st.selectbox(
        "Semester",
        sorted({row["semester"] for row in structure_connection.execute(
            "SELECT semester FROM semester_course_structure WHERE department = ? AND year = ? AND academic_batch = ?",
            (department, year, academic_batch)
        ).fetchall()}) or [1, 2, 3, 4, 5, 6, 7, 8]
    )

structure_connection.close()


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
            catalog_code,
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
                        f"**{course['catalog_code'] or course['course_code']}**"
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

    st.subheader("🗓️ Timetable")
    timetable_connection = get_connection()
    timetable_rows = timetable_connection.execute(
        """
        SELECT day, slot, start_time, end_time, section, course_code,
               course_name, faculty_name, room_number
        FROM timetable
        WHERE department = ? AND year = ? AND semester = ?
          AND academic_batch = ?
        ORDER BY day, slot, section
        """,
        (department, year, semester, academic_batch)
    ).fetchall()
    timetable_connection.close()
    if timetable_rows:
        st.dataframe(
            pd.DataFrame([dict(row) for row in timetable_rows]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No timetable periods were imported for this structure.")