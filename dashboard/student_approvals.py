import sys
from pathlib import Path

import streamlit as st

# =========================================================
# PROJECT ROOT
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =========================================================
# DATABASE
# =========================================================

from auth import require_admin
from database import (
    get_pending_student_applications,
    approve_student,
    reject_student
)

# =========================================================
# ADMIN SECURITY
# =========================================================

require_admin()


# =========================================================
# HEADER
# =========================================================

st.title("👨‍🎓 Student Registration Approval")

st.write("Review new student registrations and approve or reject applications.")

st.divider()


# =========================================================
# GET PENDING STUDENTS
# =========================================================

students = get_pending_student_applications()


# =========================================================
# SUMMARY
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Pending Applications",
        len(students)
    )

with col2:
    st.metric("Ready for Review", len(students))

with col3:
    st.metric(
        "Action Required",
        len(students)
    )

if students:
    confirm_bulk_approval = st.checkbox(
        f"I reviewed all {len(students)} pending student applications",
        key="confirm_student_approval_page_bulk"
    )
    if st.button(
        "Approve all pending students",
        type="primary",
        disabled=not confirm_bulk_approval,
        use_container_width=True
    ):
        admin_user = dict(
            st.session_state.get("user")
            or st.session_state.get("user_data")
            or {}
        )
        approved_by = admin_user.get(
            "username",
            admin_user.get("email", "Admin")
        )
        approved_count = sum(
            approve_student(student["student_id"], approved_by)
            for student in students
        )
        st.success(f"Approved {approved_count} of {len(students)} pending student registrations.")
        st.rerun()


st.divider()


# =========================================================
# NO PENDING APPLICATIONS
# =========================================================

if not students:

    st.success(
        "🎉 No pending student applications."
    )

    st.info("New student registrations will appear here for review.")

    st.stop()


# =========================================================
# STUDENT APPLICATIONS
# =========================================================

st.subheader("Pending Applications")


for student in students:

    student_id = student["student_id"]

    enrollment_no = student["enrollment_no"]

    full_name = student["full_name"]

    with st.expander(
        f"🎓 {enrollment_no} — {full_name}"
    ):

        # -------------------------------------------------
        # STUDENT INFORMATION
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Enrollment Number:** {enrollment_no}"
            )

            st.write(
                f"**Full Name:** {full_name}"
            )

            st.write(
                f"**Gender:** {student['gender']}"
            )

            st.write(
                f"**Date of Birth:** "
                f"{student['date_of_birth']}"
            )

            st.write(
                f"**Father's Name:** "
                f"{student['father_name']}"
            )

            st.write(
                f"**Mother's Name:** "
                f"{student['mother_name']}"
            )

        with col2:

            st.write(
                f"**Department:** "
                f"{student['department']}"
            )

            st.write(
                f"**Admission Year:** "
                f"{student['admission_year']}"
            )

            st.write(
                f"**Admission Session:** "
                f"{student['admission_session']}"
            )

            st.write(
                f"**Gmail:** "
                f"{student['email']}"
            )

            st.write(
                f"**Mobile:** "
                f"{student['phone']}"
            )

        st.write(
            f"**Address:** {student['address']}"
        )

        st.divider()

        # -------------------------------------------------
        # REJECTION REASON
        # -------------------------------------------------

        rejection_reason = st.text_input(
            "Rejection reason",
            key=f"reason_{student_id}",
            placeholder="Required only when rejecting"
        )

        approve_col, reject_col = st.columns(2)

        # -------------------------------------------------
        # APPROVE
        # -------------------------------------------------

        with approve_col:

            if st.button(
                "✅ Approve Student",
                key=f"approve_{student_id}",
                use_container_width=True
            ):

                admin_user = dict(st.session_state.get("user") or {})

                approved_by = admin_user.get(
                    "username",
                    admin_user.get(
                        "email",
                        "Admin"
                    )
                )

                success = approve_student(
                    student_id,
                    approved_by
                )

                if success:

                    st.success(
                        f"{full_name} has been approved."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Student approval failed."
                    )

        # -------------------------------------------------
        # REJECT
        # -------------------------------------------------

        with reject_col:

            if st.button(
                "❌ Reject Student",
                key=f"reject_{student_id}",
                use_container_width=True
            ):

                if not rejection_reason.strip():

                    st.warning(
                        "Please provide a rejection reason."
                    )

                else:

                    admin_user = dict(st.session_state.get("user") or {})

                    rejected_by = admin_user.get(
                        "username",
                        admin_user.get(
                            "email",
                            "Admin"
                        )
                    )

                    success = reject_student(
                        student_id,
                        rejection_reason.strip(),
                        rejected_by
                    )

                    if success:

                        st.success(
                            f"{full_name} has been rejected."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Student rejection failed."
                        )


# =========================================================
# BACK TO ADMIN
# =========================================================

st.divider()

if st.button("← Back to Admin Dashboard"):
    st.switch_page("dashboard/admin_dashboard.py")