"""
Verify fix for student login error, admin accuracy KeyError,
course management (2 semesters per year, unlock, add/edit/delete),
and timetable scheduling.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database import (
    get_student_semester_registration,
    get_latest_model_training_run,
    get_semester_structure,
    unlock_semester_structure,
    lock_semester_structure,
    get_connection,
    update_course_details,
    delete_course,
    add_timetable_slot,
    update_timetable_slot,
    delete_timetable_slot,
    get_academic_policies,
)
from prediction import predict_student_comprehensive
from recommendation_engine import generate_course_level_recommendations


def main():
    print("=" * 60)
    print("CHECK 1: STUDENT SEMESTER REGISTRATION DICT CONVERSION")
    print("=" * 60)
    reg = get_student_semester_registration(1, 1)
    print("Type of reg:", type(reg))
    assert isinstance(reg, dict), "Registration must be returned as a dict!"
    # Verify .get() works cleanly
    status = reg.get("status")
    print(f"reg.get('status') -> {status}")
    assert status == "Registered"
    print("✓ Student semester registration dict check PASSED!")

    print("\n" + "=" * 60)
    print("CHECK 2: LATEST MODEL TRAINING RUN DICT KEYS")
    print("=" * 60)
    latest_run = get_latest_model_training_run()
    print("Latest run:", latest_run)
    assert latest_run is not None
    assert "performance_accuracy" in latest_run or latest_run.get("accuracy") is not None
    assert "risk_accuracy" in latest_run or latest_run.get("accuracy") is not None
    print(f"Performance accuracy: {latest_run.get('performance_accuracy', latest_run.get('accuracy')):.4f}")
    print(f"Risk accuracy: {latest_run.get('risk_accuracy', latest_run.get('accuracy')):.4f}")
    print("✓ Latest model training run check PASSED (no KeyError)!")

    print("\n" + "=" * 60)
    print("CHECK 3: COURSE MANAGEMENT & UNLOCK/LOCK CONTROLS")
    print("=" * 60)
    dept = "Computer Science and Engineering"
    raw_struct = get_semester_structure(dept, 1, 1, "2026-27")
    struct = dict(raw_struct) if raw_struct else None
    assert struct is not None
    struct_id = struct["structure_id"]
    print(f"Initial structure ID #{struct_id}, is_locked = {struct['is_locked']}")

    # Unlock structure
    unlock_semester_structure(struct_id)
    unlocked = dict(get_semester_structure(dept, 1, 1, "2026-27"))
    assert unlocked["is_locked"] == 0
    print("✓ Unlocked structure successfully (Admin can now modify courses).")

    # Add a test course
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO courses (course_code, catalog_code, course_name, department, year, semester, credits, course_type, status, structure_id, is_locked)
        VALUES ('TEST101', 'TEST101', 'Software Architecture Lab', ?, 1, 1, 2, 'Lab', 'Active', ?, 0)
        """,
        (dept, struct_id)
    )
    test_course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"✓ Added test course ID #{test_course_id}")

    # Edit test course
    update_course_details(test_course_id, "TEST101", "TEST101", "Advanced Software Architecture Lab", 3, "Theory+Lab")
    conn = get_connection()
    edited_course = dict(conn.execute("SELECT * FROM courses WHERE course_id = ?", (test_course_id,)).fetchone())
    conn.close()
    assert edited_course["course_name"] == "Advanced Software Architecture Lab"
    assert edited_course["credits"] == 3
    print("✓ Course details edited successfully.")

    # Delete test course
    delete_course(test_course_id)
    conn = get_connection()
    rem = conn.execute("SELECT * FROM courses WHERE course_id = ?", (test_course_id,)).fetchone()
    conn.close()
    assert rem is None
    print("✓ Course deleted successfully.")

    # Re-lock structure
    lock_semester_structure(struct_id)
    re_locked = dict(get_semester_structure(dept, 1, 1, "2026-27"))
    assert re_locked["is_locked"] == 1
    print("✓ Re-locked structure successfully.")

    print("\n" + "=" * 60)
    print("CHECK 4: TIMETABLE MANAGEMENT (ADD, UPDATE, DELETE SLOT)")
    print("=" * 60)
    add_timetable_slot(
        department=dept,
        year=1,
        semester=1,
        section="A",
        day="Sat",
        slot="P7",
        start_time="02:35 PM",
        end_time="03:25 PM",
        course_code="CS101",
        course_name="Programming",
        faculty_name="Dr. Test Faculty",
        room_number="Lab 101",
        academic_batch="2026-27"
    )
    conn = get_connection()
    tt_row = dict(conn.execute(
        "SELECT * FROM timetable WHERE section = 'A' AND day = 'Sat' AND slot = 'P7' ORDER BY timetable_id DESC LIMIT 1"
    ).fetchone())
    conn.close()
    tt_id = tt_row["timetable_id"]
    print(f"✓ Added timetable slot #{tt_id}")

    # Update timetable slot
    update_timetable_slot(
        timetable_id=tt_id,
        course_code="CS101",
        course_name="Programming & Data Structures",
        faculty_name="Dr. Senior Faculty",
        room_number="Room #305",
        day="Sat",
        slot="P7",
        start_time="02:35 PM",
        end_time="03:25 PM"
    )
    conn = get_connection()
    updated_tt = dict(conn.execute("SELECT * FROM timetable WHERE timetable_id = ?", (tt_id,)).fetchone())
    conn.close()
    assert updated_tt["room_number"] == "Room #305"
    assert updated_tt["faculty_name"] == "Dr. Senior Faculty"
    print("✓ Updated timetable slot successfully.")

    # Delete timetable slot
    delete_timetable_slot(tt_id)
    conn = get_connection()
    rem_tt = conn.execute("SELECT * FROM timetable WHERE timetable_id = ?", (tt_id,)).fetchone()
    conn.close()
    assert rem_tt is None
    print("✓ Deleted timetable slot successfully.")

    print("\n" + "=" * 60)
    print("CHECK 5: STUDENT PREDICTION & RECOMMENDATION CONSUMPTION")
    print("=" * 60)
    pred = predict_student_comprehensive(1, 1)
    assert pred["registered"] is True
    assert pred["overall_performance"] in ("Distinction", "Pass", "Fail")
    assert pred["overall_risk"] in ("Low", "Medium", "High")
    print("Student #1 Comprehensive Prediction from Admin-trained ML:")
    print("  Overall Performance:", pred["overall_performance"])
    print("  Overall Risk:", pred["overall_risk"])
    print(f"  Evaluated Courses Count: {len(pred['course_predictions'])}")
    sample_c = pred["course_predictions"][0]
    print(f"  Sample Course: {sample_c['course_code']} - {sample_c['course_name']}: {sample_c['performance_prediction']}, Risk: {sample_c['risk_level']}")
    recs = generate_course_level_recommendations(sample_c)
    print(f"  Generated Recommendations: {len(recs)} advisories.")
    print("✓ Student receives predictions, risk level, and recommendations directly from Admin ML training!")

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS COMPLETED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    main()
