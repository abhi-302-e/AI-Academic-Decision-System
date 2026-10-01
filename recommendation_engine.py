"""
===========================================================
AI-Based Autonomous Academic Decision System

Recommendation Engine
===========================================================
"""

from prediction import predict_student


def recommendations_for_prediction(performance, risk):
    recommendations = []
    if risk == "High":
        recommendations.extend([
            "Meet with your faculty advisor",
            "Attend remedial sessions for this course",
            "Review missed material and upcoming assessments",
        ])
    elif risk == "Medium":
        recommendations.extend([
            "Review course topics where marks were lowest",
            "Attend tutorial or office-hour support",
            "Maintain regular attendance",
        ])
    else:
        recommendations.extend([
            "Maintain your current course progress",
            "Continue participating in class",
        ])

    if performance == "Fail":
        recommendations.append("Agree an improvement plan with the course faculty")
    elif performance == "Distinction":
        recommendations.append("Consider advanced course projects or peer mentoring")
    return list(dict.fromkeys(recommendations))


# ==========================================================
# RECOMMENDATION GENERATOR
# ==========================================================

def generate_recommendation(student_data):
    """
    Generate AI recommendations based on
    performance and risk prediction.
    """

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

            "Increase Attendance Above 75%",

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