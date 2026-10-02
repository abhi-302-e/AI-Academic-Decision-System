import sqlite3

con = sqlite3.connect('dataset/student.db')
con.row_factory = sqlite3.Row
rows = con.execute('SELECT faculty_id, employee_id, full_name, department, designation, qualification, experience, email, phone FROM faculty ORDER BY faculty_id').fetchall()
print(f"Total faculty count: {len(rows)}")
for r in rows[:15]:
    print(dict(r))
