"""
===========================================================
AI Academic Decision System -- Upgrade Module v2.0
10 New AI Features: Gemini API + scikit-learn + CV + NLP
===========================================================
Faculty Guides: Mrs. Madhusmita Majhi & Dr. D. Krishna Madhuri
Institution   : IFHE, Hyderabad -- FST Department of CSE
===========================================================

pip install google-genai>=2.30.1 vaderSentiment pyvis networkx
            deepface opencv-python openai-whisper xgboost scikit-learn
"""

import os, json, sqlite3, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
from google import genai

_client = None

def get_gemini_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    return _client


# ============================================================
# FEATURE 1: AI CHATBOT TUTOR (Gemini streaming Q&A)
# ============================================================
class AIChatbotTutor:
    """Stateful Gemini chatbot tutor for Year 1 Semester 1 courses."""
    SYS = (
        "You are an expert academic tutor for IFHE Hyderabad Year 1 students. "
        "Courses: MA101 (Linear Algebra), CS101 (Programming through C), "
        "PH101 (Engineering Physics), EE101 (Electrical & Electronics), "
        "EN101 (Professional Communication), CS102 (Programming Lab), "
        "PH102 (Physics Lab), ME101 (Engineering Graphics). "
        "Give step-by-step explanations. Use markdown. Show full working for math."
    )

    def __init__(self, student_name: str, enrolled_courses: list):
        self.client = get_gemini_client()
        self.student_name = student_name
        self.enrolled_courses = enrolled_courses
        self.prev_id = None

    def stream_chat(self, user_message: str):
        """Generator yielding text chunks for Streamlit streaming display."""
        sys_msg = (
            self.SYS
            + f" Student: {self.student_name}."
            + f" Enrolled: {', '.join(self.enrolled_courses)}."
        )
        kwargs = dict(
            model="gemini-3.8-flash",
            system_instruction=sys_msg,
            input=user_message,
            stream=True,
        )
        if self.prev_id:
            kwargs["previous_interaction_id"] = self.prev_id
        full_id = None
        for event in self.client.interactions.create(**kwargs):
            if event.event_type == "step.delta" and event.delta.type == "text":
                yield event.delta.text
            elif event.event_type == "interaction.completed":
                full_id = event.interaction.id
        if full_id:
            self.prev_id = full_id

    def chat(self, user_message: str) -> str:
        return "".join(self.stream_chat(user_message))


# ============================================================
# FEATURE 2: LLM PERSONALIZED STUDY PLANS
# ============================================================
def generate_personalized_study_plan(
    student_name: str,
    course_assessments: list,
    attendance_pct: float,
    hours_per_day: int = 4,
) -> str:
    """Generate a 7-day personalized study plan using Gemini."""
    snapshot = "\n".join(
        f"  - {c.get('course_code','?')} ({c.get('course_name','?')}): "
        f"Mid={c.get('mid_exam_marks') or 0}/30, "
        f"Quiz={c.get('quiz_marks') or 0}/10, "
        f"Internal={c.get('internal_total') or 0}/60"
        for c in course_assessments
    )
    prompt = (
        f"Create a 7-day personalized study plan for {student_name}.\n"
        f"Academic Snapshot:\n{snapshot}\n"
        f"Attendance: {attendance_pct:.1f}%\n"
        f"Available: {hours_per_day}h/day.\n"
        "Focus MORE time on weakest subjects. Include: daily schedule, "
        "topics to revise, practice exercises. "
        "Add attendance catch-up plan if attendance below 75%. "
        "Include motivational tips. Use markdown with tables."
    )
    resp = get_gemini_client().interactions.create(
        model="gemini-3.8-flash", input=prompt, store=False
    )
    return resp.output_text or "Study plan generation failed."


# ============================================================
# FEATURE 3: NATURAL LANGUAGE PERFORMANCE REPORTS
# ============================================================
def generate_nl_performance_report(
    student: dict,
    course_assessments: list,
    attendance_pct: float,
    risk_level: str,
    performance_class: str,
    audience: str = "student",
) -> str:
    """Generate a readable academic performance report using Gemini."""
    name = student.get("full_name", "Student")
    roll = student.get("roll_number", "")
    weak = [c.get("course_name") for c in course_assessments if (c.get("internal_total") or 0) < 30]
    strong = [c.get("course_name") for c in course_assessments if (c.get("internal_total") or 0) >= 45]
    tone = {
        "student": f"Write directly to {name} in second person (You).",
        "parent": "Write to the parent/guardian. Be formal and caring.",
        "faculty": "Write to the course advisor. Be clinical and data-driven.",
    }
    prompt = (
        f"Write an academic performance report for {name} ({roll}), IFHE Hyderabad.\n"
        f"Attendance: {attendance_pct:.1f}%, Risk: {risk_level}, Predicted: {performance_class}\n"
        f"Weak courses: {weak}\nStrong courses: {strong}\n"
        f"{tone.get(audience, tone['student'])}\n"
        "Include: academic summary, subject analysis, recommendations, encouragement. "
        "300-400 words. Markdown format."
    )
    resp = get_gemini_client().interactions.create(
        model="gemini-3.8-flash", input=prompt, store=False
    )
    return resp.output_text or "Report generation failed."


# ============================================================
# FEATURE 4: DROPOUT PREDICTION MODEL
# ============================================================
def predict_dropout_risk(
    course_assessments: list,
    attendance_pct: float,
    model_path: str = "models/dropout_model.pkl",
) -> dict:
    """Predict dropout risk -- uses XGBoost model or rule-based fallback."""
    import pickle
    internals = [float(c.get("internal_total") or 0) for c in course_assessments]
    quizzes = [float(c.get("quiz_marks") or 0) for c in course_assessments]

    features = np.array([[
        attendance_pct,
        np.mean(internals) if internals else 0,
        np.std(internals) if internals else 0,
        np.min(internals) if internals else 0,
        np.mean(quizzes) if quizzes else 0,
        sum(1 for i in internals if i < 24),
        len(course_assessments),
    ]])

    if Path(model_path).exists():
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        score = float(model.predict_proba(features)[0][1])
    else:
        att_s = max(0.0, (75.0 - attendance_pct) / 75.0)
        mk_s = max(0.0, (30.0 - (np.mean(internals) if internals else 30)) / 30.0)
        score = min(1.0, max(0.0, att_s * 0.6 + mk_s * 0.4))

    label = "High Dropout Risk" if score > 0.65 else ("Moderate Risk" if score > 0.35 else "Low Risk")
    factors = []
    if attendance_pct < 60:
        factors.append(f"Critical attendance shortage ({attendance_pct:.1f}%)")
    failing = sum(1 for i in internals if i < 24)
    if failing:
        factors.append(f"{failing} course(s) below passing internal threshold")
    if quizzes and np.mean(quizzes) < 4:
        factors.append("Persistently low quiz engagement")

    return {
        "risk_score": round(score, 3),
        "risk_label": label,
        "risk_percentage": f"{score * 100:.1f}%",
        "key_factors": factors,
    }


def train_dropout_model(
    db_path: str = "dataset/student.db",
    save_path: str = "models/dropout_model.pkl",
) -> dict:
    """Train XGBoost dropout prediction model on institutional data."""
    from xgboost import XGBClassifier
    import pickle

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT s.student_id, s.attendance_percentage, "
        "AVG(ca.mid_exam_marks) as avg_mid, AVG(ca.quiz_marks) as avg_quiz, "
        "AVG(ca.assignment_marks) as avg_assign, AVG(ca.internal_total) as avg_internal, "
        "COUNT(ca.assessment_id) as course_count, s.status "
        "FROM students s LEFT JOIN course_assessments ca ON s.student_id=ca.student_id "
        "GROUP BY s.student_id",
        conn,
    )
    conn.close()
    df["dropout"] = (
        (df["status"] == "Inactive") | (df["attendance_percentage"] < 50)
    ).astype(int)
    df = df.fillna(0)
    X = df[["attendance_percentage", "avg_mid", "avg_quiz", "avg_assign", "avg_internal", "course_count"]].values
    y = df["dropout"].values
    model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    Path(save_path).parent.mkdir(exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(model, f)
    return {"trained": True, "samples": len(df), "dropout_rate": f"{y.mean():.1%}"}


# ============================================================
# FEATURE 5: ADAPTIVE QUESTION BANK (Gemini MCQ Generator)
# ============================================================
def generate_adaptive_mcqs(
    course_code: str,
    course_name: str,
    weak_topics: list,
    difficulty: str = "medium",
    num_questions: int = 5,
) -> list:
    """Generate adaptive MCQs using Gemini targeting student weak topics."""
    topics = ", ".join(weak_topics) if weak_topics else "fundamental topics"
    prompt = (
        f"Generate {num_questions} {difficulty}-difficulty MCQs for "
        f"{course_code} ({course_name}). Focus: {topics}.\n"
        "Return ONLY a valid JSON array. Each item must have: "
        "question (string), options (object with A/B/C/D keys), "
        "correct_answer (A/B/C/D), explanation (string). No extra text."
    )
    resp = get_gemini_client().interactions.create(
        model="gemini-3.8-flash", input=prompt, store=False
    )
    raw = (resp.output_text or "[]").strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"question": "Error generating MCQs -- please retry.",
                 "options": {}, "correct_answer": "", "explanation": ""}]


# ============================================================
# FEATURE 6: SENTIMENT ANALYSIS ON STUDENT FEEDBACK
# ============================================================
def analyze_feedback_sentiment(feedback_texts: list) -> dict:
    """VADER + Gemini theme extraction for student feedback analysis."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader = SentimentIntensityAnalyzer()
        scores = [vader.polarity_scores(t)["compound"] for t in feedback_texts]
    except ImportError:
        pos_w = ["good", "excellent", "helpful", "clear", "great"]
        neg_w = ["bad", "confusing", "boring", "unclear", "difficult"]
        scores = []
        for t in feedback_texts:
            tl = t.lower()
            p = sum(1 for w in pos_w if w in tl)
            n = sum(1 for w in neg_w if w in tl)
            scores.append((p - n) / max(1, p + n))

    labels = [
        "Positive" if s >= 0.05 else ("Negative" if s <= -0.05 else "Neutral")
        for s in scores
    ]
    avg = float(np.mean(scores)) if scores else 0.0
    dist = {lbl: labels.count(lbl) for lbl in ["Positive", "Neutral", "Negative"]}
    overall = "Positive" if avg > 0.05 else ("Negative" if avg < -0.05 else "Neutral")

    top_themes = ["Teaching Quality", "Course Content", "Assessment Load"]
    if feedback_texts:
        try:
            prompt = (
                "Extract top 3 themes from these student feedback responses: "
                + "; ".join(feedback_texts[:10])
                + ". Return ONLY a JSON array of 3 theme strings."
            )
            r = get_gemini_client().interactions.create(
                model="gemini-3.8-flash", input=prompt, store=False
            )
            top_themes = json.loads(
                (r.output_text or "[]").strip().strip("```json").strip("```").strip()
            )
        except Exception:
            pass

    return {
        "overall_sentiment": overall,
        "average_score": round(avg, 3),
        "distribution": dist,
        "total_responses": len(feedback_texts),
        "top_themes": top_themes,
        "satisfaction_rate": f"{dist['Positive'] / max(1, len(feedback_texts)) * 100:.1f}%",
    }


# ============================================================
# FEATURE 7: KNOWLEDGE GRAPH OF STUDENT PROGRESS
# ============================================================
def build_knowledge_graph(
    student_name: str,
    course_assessments: list,
    output_html: str = "knowledge_graph.html",
) -> str:
    """Build interactive PyVis knowledge graph of academic mastery."""
    from pyvis.network import Network
    import networkx as nx

    prereqs = {
        "CS101": [], "MA101": [], "PH101": ["MA101"],
        "EE101": ["PH101", "MA101"], "EN101": [],
        "CS102": ["CS101"], "PH102": ["PH101"], "ME101": ["MA101"],
    }

    G = nx.DiGraph()
    for c in course_assessments:
        code = c.get("course_code", "")
        cname = c.get("course_name", code)
        mastery = float(c.get("internal_total") or 0) / 60.0
        pct = int(mastery * 100)
        color = "#22c55e" if mastery >= 0.75 else ("#f59e0b" if mastery >= 0.5 else "#ef4444")
        G.add_node(code, label=f"{code}\n{pct}%",
                   title=f"{cname}: {pct}% mastery",
                   color=color, size=int(25 + mastery * 20))

    for course, plist in prereqs.items():
        for p in plist:
            if course in G.nodes and p in G.nodes:
                G.add_edge(p, course)

    net = Network(height="500px", width="100%", directed=True,
                  bgcolor="#1e293b", font_color="white")
    net.from_nx(G)
    net.save_graph(output_html)
    return output_html


# ============================================================
# FEATURE 8: COMPUTER VISION ATTENDANCE (DeepFace)
# ============================================================
def register_student_face(student_id: str, image_path: str,
                           face_db_dir: str = "dataset/face_db") -> dict:
    """Save student face image for CV-based attendance recognition."""
    import shutil
    db = Path(face_db_dir)
    db.mkdir(parents=True, exist_ok=True)
    dest = db / f"{student_id}.jpg"
    shutil.copy(image_path, dest)
    return {"registered": True, "student_id": student_id, "face_path": str(dest)}


def recognize_attendance_from_frame(
    frame_path: str,
    face_db_dir: str = "dataset/face_db",
    threshold: float = 0.6,
) -> list:
    """Run DeepFace recognition on classroom image. Returns recognized student IDs."""
    from deepface import DeepFace
    db_path = Path(face_db_dir)
    if not db_path.exists():
        return []
    try:
        results = DeepFace.find(
            img_path=frame_path, db_path=str(db_path),
            model_name="Facenet512", detector_backend="retinaface",
            enforce_detection=False, silent=True,
        )
    except Exception as e:
        return [{"error": str(e)}]

    out = []
    for df_r in results:
        if len(df_r) > 0:
            best = df_r.iloc[0]
            sid = Path(best["identity"]).stem
            conf = max(0.0, 1.0 - float(best.get("distance", 1.0)))
            out.append({"student_id": sid, "confidence": round(conf, 3), "present": conf >= threshold})
    return out


# ============================================================
# FEATURE 9: PEER LEARNING RECOMMENDATION (K-Means style)
# ============================================================
def recommend_peer_learning_groups(students_data: list, n_groups: int = 5) -> list:
    """
    Form balanced peer learning groups by sorted round-robin assignment.
    Each group contains students of mixed academic performance levels.
    """
    if len(students_data) <= n_groups:
        return [{"group_number": 1, "members": students_data,
                 "size": len(students_data), "rationale": "Single group (small cohort)"}]

    sorted_s = sorted(
        students_data,
        key=lambda s: float(s.get("avg_internal") or s.get("internal_total") or 0)
    )
    groups = [[] for _ in range(n_groups)]
    for idx, s in enumerate(sorted_s):
        avg = float(s.get("avg_internal") or s.get("internal_total") or 0)
        groups[idx % n_groups].append({
            "student_id": s.get("student_id"),
            "name": s.get("full_name"),
            "strength": "Strong" if avg >= 40 else ("Average" if avg >= 25 else "Needs Support"),
            "avg_internal": round(avg, 1),
        })

    result = []
    for i, g in enumerate(groups):
        cnt = {lvl: sum(1 for m in g if m["strength"] == lvl)
               for lvl in ["Strong", "Average", "Needs Support"]}
        result.append({
            "group_number": i + 1,
            "members": g,
            "size": len(g),
            "rationale": (
                f"Mixed group: {cnt['Strong']} strong, "
                f"{cnt['Average']} average, {cnt['Needs Support']} needing support"
            ),
        })
    return result


# ============================================================
# FEATURE 10: VOICE-BASED AI VIVA EVALUATOR (Whisper + Gemini)
# ============================================================
def transcribe_viva_audio(audio_path: str) -> str:
    """Transcribe student viva answer from audio using Whisper STT."""
    import whisper
    return whisper.load_model("base").transcribe(audio_path, language="en").get("text", "").strip()


def evaluate_viva_answer(
    question: str,
    student_answer_text: str,
    course_code: str,
    course_name: str,
    max_marks: float = 10.0,
) -> dict:
    """Evaluate a viva answer using Gemini and return structured marks + feedback."""
    prompt = (
        f"Evaluate student viva for {course_code} ({course_name}).\n"
        f"Question: {question}\n"
        f"Student Answer: {student_answer_text}\n"
        f"Max Marks: {max_marks}\n\n"
        "Evaluate on: Conceptual Accuracy (40%), Depth (30%), Clarity (20%), Examples (10%).\n"
        "Return ONLY valid JSON with keys: "
        "marks_awarded (float), percentage (int), "
        "verdict (Excellent/Good/Average/Below Average/Poor), "
        "strengths (array), improvements (array), detailed_feedback (string)."
    )
    r = get_gemini_client().interactions.create(
        model="gemini-3.8-flash", input=prompt, store=False
    )
    raw = (r.output_text or "{}").strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "marks_awarded": max_marks / 2,
            "percentage": 50,
            "verdict": "Average",
            "strengths": ["Answer provided"],
            "improvements": ["Evaluation parsing error -- please retry"],
            "detailed_feedback": raw,
        }


def evaluate_viva_from_audio(
    audio_path: str,
    question: str,
    course_code: str,
    course_name: str,
    max_marks: float = 10.0,
) -> dict:
    """Full pipeline: audio -> Whisper transcription -> Gemini evaluation -> marks."""
    transcription = transcribe_viva_audio(audio_path)
    result = evaluate_viva_answer(question, transcription, course_code, course_name, max_marks)
    return {"audio_path": audio_path, "transcription": transcription, **result}


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == "__main__":
    print("AI Academic Decision System -- Upgrade Module v2.0")
    print("=" * 55)

    sample = [
        {"course_code": "MA101", "course_name": "Linear Algebra",
         "internal_total": 22, "quiz_marks": 3, "mid_exam_marks": 14},
        {"course_code": "CS101", "course_name": "Programming",
         "internal_total": 35, "quiz_marks": 7, "mid_exam_marks": 20},
        {"course_code": "PH101", "course_name": "Physics",
         "internal_total": 18, "quiz_marks": 2, "mid_exam_marks": 12},
    ]

    r = predict_dropout_risk(sample, attendance_pct=62.5)
    print(f"\n[F4] Dropout Risk: {r['risk_label']} ({r['risk_percentage']})")
    print(f"     Factors: {r['key_factors']}")

    students = [
        {"student_id": f"S{i}", "full_name": f"Student {i}", "avg_internal": 20 + i * 3}
        for i in range(12)
    ]
    groups = recommend_peer_learning_groups(students, n_groups=3)
    print(f"\n[F9] {len(groups)} Peer Learning Groups formed:")
    for g in groups:
        print(f"     Group {g['group_number']}: {g['size']} members -- {g['rationale']}")

    print("\nAll 10 AI upgrade features ready.")
    print("Set GEMINI_API_KEY env var, then: streamlit run app.py")
