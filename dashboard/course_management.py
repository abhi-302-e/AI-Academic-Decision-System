"""
===========================================================
AI-Based Autonomous Academic Decision System
Course & Timetable Management Console (Academic Administration)
Supports:
- Academic Year Structure (2 Semesters per Year)
- Course Catalog & Semester Structure Management (Add, Edit, Unlock, Delete)
- Section Timetable Control for Sections A through J (Add, Edit, Delete)
- Bulk Excel Curriculum & Timetable Ingestion
===========================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from auth import require_admin
from database import (
    get_connection,
    create_semester_structure,
    get_semester_structure,
    lock_semester_structure,
    unlock_semester_structure,
    delete_course,
    update_course_details,
    add_timetable_slot,
    update_timetable_slot,
    delete_timetable_slot,
    get_all_faculty,
    get_default_section_names,
    import_academic_schedule,
)
from preprocessing.academic_schedule_import import parse_academic_workbooks

require_admin()

with st.sidebar:
    st.markdown("### 🛡️ Admin Console")
    st.divider()
    if st.button("🚪 Logout", key="cm_logout", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

st.title("📚 Course & Timetable Management Console")
st.caption("Institutional Academic Administration · Curriculum Governance, 2-Semester Annual Structure & Section Timetables")

st.markdown(
    """
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem;">
        <div style="font-weight: 700; color: #0f172a; margin-bottom: 0.35rem; font-size: 1.05rem;">
            🏛️ Academic Structure & Governance Standard
        </div>
        <div style="font-size: 0.88rem; color: #334155; line-height: 1.5;">
            • <b>Annual Structure:</b> Each Academic Year consists of <b>2 Semesters</b> (Odd / Autumn Semester & Even / Spring Semester).
            <br>• <b>Admin Authority:</b> Full control to create semester structures, unlock and modify courses, add/edit/delete curriculum offerings, and manage section timetables for Sections A through J.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# ACADEMIC YEAR & 2-SEMESTER SELECTION CONTROLS
# ==========================================================
with st.container(border=True):
    st.markdown("##### ⚙️ Academic Program & Semester Selection")
    col_dept, col_batch, col_year, col_sem = st.columns(4)

    with col_dept:
        department_choices = [
            "Computer Science and Engineering",
            "Artificial Intelligence and Machine Learning",
            "AI and Data Science",
        ]
        selected_dept = st.selectbox("Department", department_choices, index=0)

    with col_batch:
        academic_batch = st.text_input("Academic Batch", value="2026-27")

    with col_year:
        year_labels = {
            1: "Year 1 (Freshman)",
            2: "Year 2 (Sophomore)",
            3: "Year 3 (Junior)",
            4: "Year 4 (Senior)",
        }
        selected_year = st.selectbox(
            "Academic Year",
            [1, 2, 3, 4],
            format_func=lambda y: year_labels[y],
            index=0,
        )

    with col_sem:
        # 2 Semesters per Academic Year rule
        sem_for_year = [(selected_year - 1) * 2 + 1, (selected_year - 1) * 2 + 2]
        sem_labels = {
            s: f"Semester {s} ({'Odd / Autumn' if s % 2 != 0 else 'Even / Spring'})"
            for s in sem_for_year
        }
        selected_sem = st.selectbox(
            "Semester (2 Semesters / Year)",
            sem_for_year,
            format_func=lambda s: sem_labels[s],
            index=0,
        )

# Fetch structure for current selection
raw_structure = get_semester_structure(selected_dept, selected_year, selected_sem, academic_batch)
structure = dict(raw_structure) if raw_structure else None
structure_id = structure.get("structure_id") if structure else None
is_locked = bool(structure.get("is_locked", 0)) if structure else False

tab_courses, tab_timetable, tab_import = st.tabs([
    "📚 Semester Courses & Curriculum Control",
    "🗓️ Section Timetable Control (Sections A–J)",
    "📥 Bulk Excel Schedule Import",
])

# ==========================================================
# TAB 1: SEMESTER COURSES & CURRICULUM CONTROL
# ==========================================================
with tab_courses:
    st.markdown(f"#### 📚 Course Offerings · {selected_dept} — Year {selected_year}, Semester {selected_sem}")

    if not structure:
        st.warning(f"⚠️ No course structure has been created yet for {selected_dept} — Year {selected_year}, Semester {selected_sem} (Batch {academic_batch}).")
        if st.button("➕ Initialize Semester Course Structure", type="primary"):
            new_id = create_semester_structure(selected_dept, selected_year, selected_sem, academic_batch)
            if new_id:
                st.success("Semester course structure created successfully!")
                st.rerun()
            else:
                st.error("Failed to initialize structure.")
    else:
        # Status Card & Lock/Unlock Buttons
        with st.container(border=True):
            stat_c1, stat_c2 = st.columns([3, 2])
            with stat_c1:
                if is_locked:
                    st.success("🔒 **Status: Published & Locked** — Registered students are enrolled in this accredited structure.")
                else:
                    st.info("🔓 **Status: Draft / Unlocked** — Administrator can freely add, modify, or delete course offerings.")
            with stat_c2:
                if is_locked:
                    if st.button("🔓 Unlock Structure to Modify Courses", type="secondary"):
                        unlock_semester_structure(structure_id)
                        st.success("Structure unlocked! You can now edit and manage courses.")
                        st.rerun()
                else:
                    if st.button("🔒 Lock & Publish Course Structure", type="primary"):
                        lock_semester_structure(structure_id)
                        st.success("Structure locked and published successfully!")
                        st.rerun()

        # Fetch current courses
        conn = get_connection()
        courses_query = conn.execute(
            """
            SELECT course_id, course_code, catalog_code, course_name, credits, course_type, status, is_locked
            FROM courses
            WHERE structure_id = ? OR (department = ? AND year = ? AND semester = ?)
            ORDER BY course_code
            """,
            (structure_id, selected_dept, selected_year, selected_sem)
        ).fetchall()
        conn.close()

        course_list = [dict(c) for c in courses_query]
        total_credits = sum(float(c.get("credits") or 0) for c in course_list)

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total Courses", len(course_list))
        with k2:
            st.metric("Total Semester Credits", f"{total_credits:.1f} Credits")
        with k3:
            st.metric("Structure ID", f"#{structure_id}")

        st.markdown("##### 📋 Current Semester Course Inventory")
        if course_list:
            display_df = pd.DataFrame([
                {
                    "Course ID": c["course_id"],
                    "Course Code": c["course_code"],
                    "Catalog Code": c.get("catalog_code") or c["course_code"],
                    "Course Title": c["course_name"],
                    "Credits": c["credits"],
                    "Course Type": c["course_type"],
                    "Status": c["status"],
                }
                for c in course_list
            ])
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No courses currently linked to this semester structure.")

        st.divider()

        # Manage Course Actions (Add, Edit, Delete)
        action_col1, action_col2 = st.columns(2)

        # Form: Add New Course
        with action_col1:
            with st.container(border=True):
                st.markdown("##### ➕ Add New Course to Semester")
                new_c_code = st.text_input("Course Code (e.g., CS102, AI101)", key="add_ccode")
                new_cat_code = st.text_input("Catalog Code (e.g., 11UC102)", key="add_catcode")
                new_c_name = st.text_input("Course Name", key="add_cname")
                new_c_credits = st.number_input("Credits", min_value=1, max_value=8, value=3, key="add_ccredits")
                new_c_type = st.selectbox("Course Type", ["Theory", "Lab", "Theory+Lab"], key="add_ctype")

                if st.button("➕ Add Course to Structure", type="primary", use_container_width=True):
                    if not new_c_code.strip() or not new_c_name.strip():
                        st.error("Please provide both Course Code and Course Name.")
                    else:
                        c_conn = get_connection()
                        try:
                            c_conn.execute(
                                """
                                INSERT INTO courses (course_code, catalog_code, course_name, department, year, semester, credits, course_type, status, structure_id, is_locked)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
                                """,
                                (new_c_code.strip(), new_cat_code.strip() or new_c_code.strip(), new_c_name.strip(), selected_dept, selected_year, selected_sem, new_c_credits, new_c_type, structure_id, int(is_locked))
                            )
                            c_conn.commit()
                            st.success(f"Course '{new_c_name}' successfully added to Year {selected_year}, Semester {selected_sem}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding course: {e}")
                        finally:
                            c_conn.close()

        # Form: Edit or Delete Existing Course
        with action_col2:
            with st.container(border=True):
                st.markdown("##### ✏️ Edit or Delete Existing Course")
                if course_list:
                    course_options = {
                        f"{c.get('catalog_code') or c['course_code']} - {c['course_name']} (ID: {c['course_id']})": c
                        for c in course_list
                    }
                    selected_course_key = st.selectbox("Select Course to Modify", list(course_options.keys()))
                    course_to_edit = course_options[selected_course_key]

                    edit_code = st.text_input("Edit Course Code", value=course_to_edit["course_code"], key="edit_code")
                    edit_cat = st.text_input("Edit Catalog Code", value=course_to_edit.get("catalog_code") or course_to_edit["course_code"], key="edit_cat")
                    edit_name = st.text_input("Edit Course Title", value=course_to_edit["course_name"], key="edit_name")
                    edit_cred = st.number_input("Edit Credits", min_value=1, max_value=8, value=int(course_to_edit["credits"]), key="edit_cred")
                    type_opts = ["Theory", "Lab", "Theory+Lab"]
                    cur_type_idx = type_opts.index(course_to_edit["course_type"]) if course_to_edit["course_type"] in type_opts else 0
                    edit_type = st.selectbox("Edit Course Type", type_opts, index=cur_type_idx, key="edit_type")

                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        if st.button("💾 Save Course Changes", type="primary", use_container_width=True):
                            update_course_details(
                                course_to_edit["course_id"],
                                edit_code.strip(),
                                edit_cat.strip(),
                                edit_name.strip(),
                                edit_cred,
                                edit_type
                            )
                            st.success(f"Course '{edit_name}' updated successfully!")
                            st.rerun()
                    with e_col2:
                        if st.button("🗑️ Remove Course", type="secondary", use_container_width=True):
                            delete_course(course_to_edit["course_id"])
                            st.success("Course removed from semester structure.")
                            st.rerun()
                else:
                    st.info("No courses available to edit.")

# ==========================================================
# TAB 2: SECTION TIMETABLE CONTROL (Sections A through J)
# ==========================================================
with tab_timetable:
    st.markdown(f"#### 🗓️ Section Timetable Schedule Control · Year {selected_year}, Semester {selected_sem}")
    st.caption("Administrator can inspect, add, modify, and delete teaching session slots across all 10 sections (Sections A to J).")

    tt_conn = get_connection()
    tt_query = tt_conn.execute(
        """
        SELECT timetable_id, section, day, slot, start_time, end_time,
               course_code, course_name, faculty_name, room_number
        FROM timetable
        WHERE year = ? AND semester = ? AND academic_batch = ?
        ORDER BY section,
            CASE day
                WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
                WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6 ELSE 7
            END,
            slot
        """,
        (selected_year, selected_sem, academic_batch)
    ).fetchall()
    tt_conn.close()

    tt_records = [dict(r) for r in tt_query]

    # Filters
    f_sec, f_day = st.columns(2)
    default_sections = get_default_section_names()
    with f_sec:
        sec_filter = st.selectbox("Filter by Section", ["All Sections"] + default_sections)
    with f_day:
        day_filter = st.selectbox("Filter by Day", ["All Days", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])

    filtered_tt = tt_records
    if sec_filter != "All Sections":
        filtered_tt = [r for r in filtered_tt if r["section"] == sec_filter]
    if day_filter != "All Days":
        filtered_tt = [r for r in filtered_tt if r["day"] == day_filter]

    st.metric("Scheduled Timetable Slots", f"{len(filtered_tt)} Sessions (Filtered) / {len(tt_records)} Total")
    if filtered_tt:
        st.dataframe(pd.DataFrame(filtered_tt), use_container_width=True, hide_index=True)
    else:
        st.info("No timetable slots match the selected filters.")

    st.divider()

    # Timetable Modifications (Add Slot, Edit/Change Slot, Delete Slot)
    all_fac_list = get_all_faculty()
    faculty_names = sorted(list({f["full_name"] for f in all_fac_list if f.get("full_name")}))
    semester_courses = course_list if course_list else []
    course_name_map = {
        f"{c.get('catalog_code') or c['course_code']} - {c['course_name']}": (c["course_code"], c["course_name"])
        for c in semester_courses
    }

    SLOT_TIMINGS = {
        "P1": ("09:30 AM", "10:20 AM"),
        "P2": ("10:20 AM", "11:10 AM"),
        "P3": ("11:25 AM", "12:15 PM"),
        "P4": ("12:15 PM", "01:05 PM"),
        "P6": ("01:45 PM", "02:35 PM"),
        "P7": ("02:35 PM", "03:25 PM"),
    }

    tt_col1, tt_col2 = st.columns(2)

    # Form: Schedule New Timetable Slot
    with tt_col1:
        with st.container(border=True):
            st.markdown("##### ➕ Schedule New Timetable Slot")
            in_sec = st.selectbox("Target Section", default_sections, key="add_tt_sec")
            in_day = st.selectbox("Day of Week", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], key="add_tt_day")
            in_slot = st.selectbox(
                "Teaching Period",
                list(SLOT_TIMINGS.keys()),
                format_func=lambda s: f"{s} ({SLOT_TIMINGS[s][0]} – {SLOT_TIMINGS[s][1]})",
                key="add_tt_slot",
            )
            s_time, e_time = SLOT_TIMINGS[in_slot]

            if course_name_map:
                in_c_choice = st.selectbox("Select Course", list(course_name_map.keys()), key="add_tt_course")
                chosen_ccode, chosen_cname = course_name_map[in_c_choice]
            else:
                chosen_ccode = st.text_input("Course Code", value="CS101", key="add_tt_manual_ccode")
                chosen_cname = st.text_input("Course Title", value="Programming", key="add_tt_manual_cname")

            in_fac = st.selectbox("Faculty Instructor", faculty_names or ["Dr. Faculty Advisor"], key="add_tt_fac")
            in_room = st.text_input("Assigned Room / Lab", value="Room #301", key="add_tt_room")

            if st.button("➕ Schedule Timetable Slot", type="primary", use_container_width=True):
                add_timetable_slot(
                    department=selected_dept,
                    year=selected_year,
                    semester=selected_sem,
                    section=in_sec,
                    day=in_day,
                    slot=in_slot,
                    start_time=s_time,
                    end_time=e_time,
                    course_code=chosen_ccode,
                    course_name=chosen_cname,
                    faculty_name=in_fac,
                    room_number=in_room,
                    academic_batch=academic_batch,
                )
                st.success(f"Slot {in_slot} ({in_day}) scheduled for Section {in_sec}!")
                st.rerun()

    # Form: Edit or Delete Existing Timetable Slot
    with tt_col2:
        with st.container(border=True):
            st.markdown("##### ✏️ Edit or Delete Existing Timetable Slot")
            if tt_records:
                slot_options = {
                    f"ID #{r['timetable_id']}: Sec {r['section']} · {r['day']} {r['slot']} ({r['course_code']} - {r['course_name']})": r
                    for r in tt_records
                }
                selected_slot_key = st.selectbox("Select Timetable Slot to Modify", list(slot_options.keys()))
                slot_to_edit = slot_options[selected_slot_key]

                edit_tt_cname = st.text_input("Course Title", value=slot_to_edit["course_name"], key="edit_tt_cname")
                edit_tt_ccode = st.text_input("Course Code", value=slot_to_edit["course_code"], key="edit_tt_ccode")
                
                fac_idx = faculty_names.index(slot_to_edit["faculty_name"]) if slot_to_edit["faculty_name"] in faculty_names else 0
                edit_tt_fac = st.selectbox("Faculty Instructor", faculty_names or [slot_to_edit["faculty_name"]], index=fac_idx, key="edit_tt_fac")
                edit_tt_room = st.text_input("Room / Lab", value=slot_to_edit.get("room_number", "Room #301"), key="edit_tt_room")

                day_opts = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
                d_idx = day_opts.index(slot_to_edit["day"]) if slot_to_edit["day"] in day_opts else 0
                edit_tt_day = st.selectbox("Day", day_opts, index=d_idx, key="edit_tt_day")

                slot_keys = list(SLOT_TIMINGS.keys())
                s_idx = slot_keys.index(slot_to_edit["slot"]) if slot_to_edit["slot"] in slot_keys else 0
                edit_tt_slot = st.selectbox(
                    "Period",
                    slot_keys,
                    index=s_idx,
                    format_func=lambda s: f"{s} ({SLOT_TIMINGS[s][0]} – {SLOT_TIMINGS[s][1]})",
                    key="edit_tt_slot_box"
                )
                new_s_time, new_e_time = SLOT_TIMINGS[edit_tt_slot]

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("💾 Save Slot Changes", type="primary", use_container_width=True):
                        update_timetable_slot(
                            slot_to_edit["timetable_id"],
                            edit_tt_ccode.strip(),
                            edit_tt_cname.strip(),
                            edit_tt_fac,
                            edit_tt_room.strip(),
                            edit_tt_day,
                            edit_tt_slot,
                            new_s_time,
                            new_e_time
                        )
                        st.success("Timetable slot successfully updated!")
                        st.rerun()
                with b2:
                    if st.button("🗑️ Remove Slot", type="secondary", use_container_width=True):
                        delete_timetable_slot(slot_to_edit["timetable_id"])
                        st.success("Timetable slot removed.")
                        st.rerun()
            else:
                st.info("No timetable slots available to edit.")

# ==========================================================
# TAB 3: BULK EXCEL SCHEDULE IMPORT
# ==========================================================
with tab_import:
    st.markdown("#### 📥 Bulk Excel Workbook Ingestion")
    st.info("Upload university master course catalog and sectionwise timetable spreadsheets for automated parsing and scheduling.")

    up_col1, up_col2 = st.columns(2)
    with up_col1:
        master_upload = st.file_uploader("Upload Master Course Workbook (.xlsx)", type=["xlsx"], key="academic_master_upload")
    with up_col2:
        section_upload = st.file_uploader("Upload Sectionwise Timetable Workbook (.xlsx)", type=["xlsx"], key="academic_sections_upload")

    master_bytes = master_upload.getvalue() if master_upload else None
    section_bytes = section_upload.getvalue() if section_upload else None
    master_name = master_upload.name if master_upload else None
    section_name = section_upload.name if section_upload else None

    confirm_batch = st.checkbox("I confirm these workbooks correspond to Academic Batch 2026–27.", key="confirm_batch")

    if st.button("Preview Excel Import", type="primary", disabled=not (master_bytes and section_bytes)):
        try:
            preview = parse_academic_workbooks(master_bytes, section_bytes, academic_batch.strip())
            st.session_state.schedule_import_preview = preview
            st.session_state.schedule_import_sources = (master_name, section_name, academic_batch.strip())
        except Exception as error:
            st.error(f"Could not parse workbooks: {error}")

    preview = st.session_state.get("schedule_import_preview")
    preview_sources = st.session_state.get("schedule_import_sources")
    if preview and preview_sources == (master_name, section_name, academic_batch.strip()):
        st.markdown("##### 🔍 Import Preview")
        metric_cols = st.columns(4)
        for column, label, key in zip(
            metric_cols,
            ["Course Offerings", "Semester Structures", "Sections", "Timetable Periods"],
            ["courses", "structures", "sections", "timetable"],
        ):
            column.metric(label, len(preview[key]))

        if preview.get("conflicts"):
            st.warning(f"{len(preview['conflicts'])} conflicting section-period assignments detected.")
            st.dataframe(pd.DataFrame(preview["conflicts"]), use_container_width=True, hide_index=True)

        if st.button("Publish Courses & Timetable from Excel", type="primary", disabled=not confirm_batch):
            try:
                result = import_academic_schedule(preview)
                st.session_state.schedule_import_preview = None
                st.session_state.schedule_import_sources = None
                st.success(
                    f"Schedule published: {result['courses']} courses, {result['sections_added']} sections, {result['timetable_added']} timetable periods."
                )
                st.rerun()
            except Exception as error:
                st.error(f"Import failed: {error}")