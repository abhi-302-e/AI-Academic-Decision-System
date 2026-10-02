import sys
sys.path.insert(0, ".")
import database

conn = database.get_connection()
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in database:", tables)

for t in ["academic_policies", "model_training_runs", "course_assessments", "student_assessments", "students"]:
    if t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"Table {t}: {count} rows")

conn.close()
