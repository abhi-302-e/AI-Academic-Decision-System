import sqlite3
import re
import bcrypt

DATABASE_PATH = "dataset/student.db"

conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

c.execute("SELECT faculty_id, employee_id, full_name, department, email, phone FROM faculty")
rows = c.fetchall()
print(f"Total faculty members found: {len(rows)}")

faculty_pw_hash = bcrypt.hashpw(b"faculty@123", bcrypt.gensalt()).decode()

cse_quals = [
    "Ph.D. in Computer Science & Engineering (IIT Hyderabad)",
    "Ph.D. in Distributed Systems & Cloud Computing (IIT Bombay)",
    "Ph.D. in Cyber Security & Cryptography (IIT Delhi)",
    "Ph.D. in Computer Science & Automation (IISc Bangalore)",
    "Ph.D. in Algorithms & Network Systems (NIT Warangal)",
    "Ph.D. in High Performance Computing (IIT Madras)",
    "Ph.D. in Software Architecture & DevOps (IIT Kharagpur)",
    "M.Tech in Computer Science & Engineering (NIT Surathkal), Ph.D. (Pursuing)",
]

aiml_quals = [
    "Ph.D. in Artificial Intelligence & Deep Learning (IIT Madras)",
    "Ph.D. in Machine Learning & Pattern Recognition (IISc Bangalore)",
    "Ph.D. in Natural Language Processing & Cognitive Systems (IIT Hyderabad)",
    "Ph.D. in Reinforcement Learning & Autonomous Agents (IIT Bombay)",
    "Ph.D. in Computer Vision & Image Understanding (IIT Kanpur)",
    "Ph.D. in Explainable AI & Statistical Learning (NIT Trichy)",
    "M.Tech in AI & Robotics (IIT Roorkee), Ph.D. (Pursuing)",
]

aids_quals = [
    "Ph.D. in Data Science & Big Data Engineering (IISc Bangalore)",
    "Ph.D. in Predictive Analytics & Knowledge Systems (IIT Kharagpur)",
    "Ph.D. in Applied Statistics & Machine Intelligence (IIT Bombay)",
    "Ph.D. in Mathematical Modeling & Optimization (IIT Madras)",
    "Ph.D. in Data Mining & Information Retrieval (NIT Warangal)",
    "Ph.D. in Biomedical Data Science (IIT Delhi)",
    "M.Tech in Data Engineering & Analytics (BITS Pilani), Ph.D. (Pursuing)",
]

designations_cycle = [
    ("Professor", 16),
    ("Associate Professor", 11),
    ("Associate Professor", 10),
    ("Assistant Professor", 6),
    ("Assistant Professor", 5),
    ("Professor", 18),
    ("Associate Professor", 12),
    ("Assistant Professor", 7),
    ("Assistant Professor", 4),
]

phone_prefixes = ["98480", "94401", "91212", "99890", "98665", "97014", "94903"]

# Reserve first professor in each department as Professor & HOD
hod_assigned = set()

updated_count = 0
for i, r in enumerate(rows):
    fid, emp_id, name, dept, old_email, old_phone = r
    
    # Clean name for email
    clean_name = re.sub(r'^(Dr|Mr|Mrs|Ms|Prof)\.?\s*', '', name, flags=re.IGNORECASE)
    clean_parts = re.findall(r'[a-zA-Z]+', clean_name.lower())
    if clean_parts:
        email_handle = ".".join(clean_parts[:2])
    else:
        email_handle = f"faculty.{i+1:04d}"
    
    # Check if duplicate email
    unique_email = f"{email_handle}.{emp_id.lower()}@faculty.academics.edu"
    
    # Pick qualification
    if "data" in dept.lower():
        qual = aids_quals[i % len(aids_quals)]
    elif "intelligence" in dept.lower() or "aiml" in dept.lower():
        qual = aiml_quals[i % len(aiml_quals)]
    else:
        qual = cse_quals[i % len(cse_quals)]
        
    # Designation & experience
    desig, exp = designations_cycle[i % len(designations_cycle)]
    if dept not in hod_assigned and "Dr" in name:
        desig = "Professor & HOD"
        exp = 21 + (i % 3)
        hod_assigned.add(dept)
    elif "Dr" not in name and "Professor" in desig and "Assistant" not in desig:
        desig = "Assistant Professor"
        exp = min(exp, 6)

    # Realistic phone
    prefix = phone_prefixes[i % len(phone_prefixes)]
    phone = f"+91 {prefix} {20000 + i:05d}"
    
    # Update row
    c.execute("""
        UPDATE faculty
        SET password = ?,
            qualification = ?,
            experience = ?,
            designation = ?,
            phone = ?,
            email = ?,
            status = 'Active'
        WHERE faculty_id = ?
    """, (faculty_pw_hash, qual, exp, desig, phone, unique_email, fid))
    updated_count += 1

conn.commit()
conn.close()

print(f"Successfully updated {updated_count} faculty records with qualifications, experience, and password 'faculty@123'!")
