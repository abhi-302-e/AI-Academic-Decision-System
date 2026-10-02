"""
===========================================================
AI-Based Autonomous Academic Decision System

Recommendation Engine
===========================================================
"""

from prediction import predict_student


from database import get_academic_policies


def recommendations_for_prediction(performance, risk, policies=None):
    if policies is None:
        try:
            policies = get_academic_policies()
        except Exception:
            policies = {}
    att_thresh = int(float(policies.get("attendance_threshold", 75.0)))
    recommendations = []
    if risk == "High":
        recommendations.extend([
            "Meet with your faculty advisor for urgent academic intervention",
            "Attend mandatory remedial sessions for this course",
            f"Increase attendance strictly above {att_thresh}% statutory threshold",
            "Review missed curriculum and submit pending continuous assessments",
        ])
    elif risk == "Medium":
        recommendations.extend([
            "Review course topics where continuous assessment marks were lowest",
            "Attend departmental tutorial and office-hour mentoring sessions",
            f"Maintain regular attendance above {att_thresh}%",
        ])
    else:
        recommendations.extend([
            "Maintain your current consistent course progress and study rhythm",
            "Continue active participation in laboratory and class discussions",
        ])

    if performance == "Fail":
        recommendations.append("Formalize an academic recovery plan with the course instructor")
    elif performance == "Distinction":
        recommendations.append("Eligible for advanced research mini-projects or peer-tutor leadership")
    return list(dict.fromkeys(recommendations))


def generate_course_level_recommendations(course_dict, policies=None):
    """
    Synthesize course marks, attendance, and multi-dataset behavioral factors (OULAD, UCI, Kaggle)
    into concrete, prioritized academic recommendations using Admin-configured policy thresholds.
    """
    if policies is None:
        try:
            policies = get_academic_policies()
        except Exception:
            policies = {}

    att_thresh = float(policies.get("attendance_threshold", 75.0))
    crit_int_thresh = float(policies.get("critical_internal_threshold", 24.0))
    mid_thresh = float(policies.get("mid_exam_threshold", 15.0))
    assn_thresh = float(policies.get("assignment_threshold", 5.0))
    quiz_thresh = float(policies.get("quiz_threshold", 5.0))
    viva_thresh = float(policies.get("viva_threshold", 5.0))

    course_name = course_dict.get("course_name", "this course")
    att = float(course_dict.get("course_attendance") or 0)
    mid = float(course_dict.get("mid_exam_marks") or 0)
    assn = float(course_dict.get("assignment_marks") or 0)
    quiz = float(course_dict.get("quiz_marks") or 0)
    viva = float(course_dict.get("viva_marks") or 0)
    ext = float(course_dict.get("external_marks") or 0)
    internal_total = round(mid + assn + quiz + viva, 2)
    perf = course_dict.get("performance_prediction", "Pass")
    faculty = course_dict.get("faculty_name", "Course Faculty")

    recommendations = []

    # Attendance-specific alerts based on Admin Policy
    if att < att_thresh:
        shortfall = max(1, int(round((att_thresh - att) * 0.35)))
        recommendations.append({
            "category": "Attendance & Regulatory Eligibility",
            "priority": "Critical",
            "icon": "🚨",
            "text": f"Attendance is {att:.1f}% (below the institutional {att_thresh:.0f}% statutory requirement). Attend the next {shortfall} scheduled sessions consecutively to avoid exam debarment.",
        })
    elif att < (att_thresh + 10.0):
        recommendations.append({
            "category": "Attendance",
            "priority": "Medium",
            "icon": "⚠️",
            "text": f"Attendance is at {att:.1f}%. Aim for {(att_thresh + 10.0):.0f}%+ to secure full continuous assessment credits.",
        })

    # Internal marks breakdown & CIE Critical Threshold
    if internal_total < crit_int_thresh:
        recommendations.append({
            "category": "CIE Continuous Evaluation Alert",
            "priority": "Critical",
            "icon": "⚠️",
            "text": f"Total Continuous Internal Evaluation (CIE) is {internal_total:.1f}/60, which is below the institutional passing threshold of {crit_int_thresh:.0f}/60. Mandatory remedial tutorial registration is required.",
        })

    if mid < mid_thresh:
        recommendations.append({
            "category": "UCI Exam Preparation Factor",
            "priority": "High",
            "icon": "📖",
            "text": f"Mid-term examination score is {mid:.1f}/30 (below cutoff of {mid_thresh:.0f}). Schedule a 1-on-1 review with {faculty} to clarify core conceptual deficiencies before the external exam.",
        })

    if assn < assn_thresh:
        recommendations.append({
            "category": "OULAD Continuous Telemetry",
            "priority": "High",
            "icon": "💻",
            "text": f"Assignment score is {assn:.1f}/10 (below target {assn_thresh:.0f}). OULAD learning analytics show that proactive submission correlates with a +18% grade lift. Submit upcoming assignments on time.",
        })

    if quiz < quiz_thresh:
        recommendations.append({
            "category": "Continuous Assessment",
            "priority": "Medium",
            "icon": "📝",
            "text": f"Quiz performance is {quiz:.1f}/10 (below target {quiz_thresh:.0f}). Practice weekly topic-wise formative quizzes on the university LMS to build conceptual mastery.",
        })

    if viva < viva_thresh:
        recommendations.append({
            "category": "Viva Voce & Oral Defense",
            "priority": "Medium",
            "icon": "🗣️",
            "text": f"Oral defense / viva voce is {viva:.1f}/10 (below target {viva_thresh:.0f}). Participate actively in laboratory Q&A sessions to improve technical articulation.",
        })

    if ext < 16.0:
        recommendations.append({
            "category": "External Exam Strategy",
            "priority": "High",
            "icon": "🎯",
            "text": f"External exam score is {ext:.1f}/40 (below minimum passing score 16.0). Solve previous university examination papers under timed 3-hour mock exam conditions.",
        })

    if not recommendations:
        if perf == "Distinction":
            recommendations.append({
                "category": "Advanced Enrichment",
                "priority": "Low",
                "icon": "🌟",
                "text": f"Outstanding standing in {course_name}! Consider undertaking an advanced semester mini-project or mentoring peers.",
            })
        else:
            recommendations.append({
                "category": "Sustained Progress",
                "priority": "Low",
                "icon": "✅",
                "text": f"Consistent performance in {course_name}. Maintain your weekly study rhythm of 6–8 hours and review weekly lecture notes.",
            })

    return recommendations



# ==========================================================
# RECOMMENDATION GENERATOR
# ==========================================================

def generate_recommendation(student_data, policies=None):
    """
    Generate AI recommendations based on
    performance and risk prediction and admin policies.
    """
    if policies is None:
        try:
            policies = get_academic_policies()
        except Exception:
            policies = {}
    att_thresh = int(float(policies.get("attendance_threshold", 75.0)))

    prediction = predict_student(student_data)

    performance = prediction["performance_prediction"]

    risk = prediction["risk_level"]

    recommendations = []


    # ------------------------------------------------------
    # HIGH RISK
    # ------------------------------------------------------

    if risk == "High":

        recommendations.extend([

            "Meet Faculty Advisor",

            "Attend Remedial Classes",

            "Complete Pending Assignments",

            f"Increase Attendance Above {att_thresh}%",

            "Weekly Academic Monitoring"

        ])


    # ------------------------------------------------------
    # MEDIUM RISK
    # ------------------------------------------------------

    elif risk == "Medium":

        recommendations.extend([

            "Improve Assignment Submission",

            "Attend Extra Tutorial Sessions",

            "Increase LMS Learning Time",

            "Maintain Regular Attendance"

        ])


    # ------------------------------------------------------
    # LOW RISK
    # ------------------------------------------------------

    else:

        recommendations.extend([

            "Maintain Current Performance",

            "Participate in Workshops",

            "Take Advanced Learning Activities",

            "Help Peer Learning Groups"

        ])
# ==========================================================
# PERFORMANCE-BASED RECOMMENDATIONS
# ==========================================================

    if performance == "Fail":

        recommendations.extend([

            "Schedule Parent-Teacher Meeting",

            "Prepare Individual Study Plan",

            "Practice Previous Year Question Papers"

        ])

    elif performance == "Pass":

        recommendations.extend([

            "Improve Subject Understanding",

            "Focus on Weak Subjects",

            "Increase Daily Study Hours"

        ])

    elif performance == "Distinction":

        recommendations.extend([

            "Eligible for Merit Scholarship",

            "Participate in Research Projects",

            "Become Student Mentor"

        ])


# ==========================================================
# REMOVE DUPLICATE RECOMMENDATIONS
# ==========================================================

    recommendations = list(dict.fromkeys(recommendations))


# ==========================================================
# RETURN RESULT
# ==========================================================

    return {

        "performance_prediction": performance,

        "risk_level": risk,

        "recommendations": recommendations

    }


# ==========================================================
# SAMPLE TEST
# ==========================================================

if __name__ == "__main__":

    sample_student = {

        "cgpa": 8.6,

        "attendance_percentage": 90,

        "assignment_marks": 84,

        "quiz_marks": 82,

        "mid_exam_marks": 85,

        "end_sem_marks": 88,

        "lab_marks": 91,

        "average_marks": 86,

        "lms_login_frequency": 70,

        "time_spent_learning": 45,

        "course_completion_percentage": 94,

        "classroom_participation": 9,

        "communication_skills": 9,

        "discipline_score": 10,

        "performance_score": 87.2,

        "engagement_score": 165

    }

    result = generate_recommendation(sample_student)

    print("=" * 50)

    print("AI Recommendation Result")

    print("=" * 50)

    print(f"Performance : {result['performance_prediction']}")

    print(f"Risk Level : {result['risk_level']}")

    print("\nRecommendations:")

    for recommendation in result["recommendations"]:

        print(f"✓ {recommendation}")

    print("=" * 50)