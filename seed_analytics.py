import mysql.connector
import random
from werkzeug.security import generate_password_hash
import time

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '', 
    'host': 'localhost',
    'database': 'course_db'
}

# --- DATA GENERATORS ---
NAMES = ["Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Reyansh", "Muhammad", "Avni", "Diya", "Ananya", 
         "Ishaan", "Vivaan", "Rohan", "Rahul", "Sarthak", "Neha", "Priya", "Sneha", "Kavya", "Tanvi"]
SURNAMES = ["Sharma", "Verma", "Gupta", "Malik", "Mehta", "Patel", "Reddy", "Nair", "Iyer", "Singh"]

COURSES = [
    ("CS101", "Intro to Python Programming"),
    ("CS202", "Data Structures & Algorithms"),
    ("CS305", "Database Management Systems"),
    ("AI401", "Artificial Intelligence Basics"),
    ("ML502", "Machine Learning with PyTorch"),
    ("EE101", "Digital Electronics"),
    ("MA201", "Linear Algebra for CS"),
    ("HS301", "Professional Ethics"),
]

LOG_ACTIONS = ["LOGIN", "ADD_COURSE", "UPDATE_GRADE", "VIEW_REPORT", "LOGOUT"]

def connect():
    return mysql.connector.connect(**db_config)

def seed_data():
    conn = connect()
    cursor = conn.cursor()
    
    print("🧹 Clearing old data...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE Enrollments")
    cursor.execute("TRUNCATE TABLE Courses")
    cursor.execute("TRUNCATE TABLE Users")
    cursor.execute("TRUNCATE TABLE AuditLogs")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    print("🌱 Seeding Users...")
    users = []
    
    # 1. Admin & Analyst
    users.append(('Admin User', 'admin@myjus.in', 'admin', 'admin'))
    users.append(('Data Analyst', 'analyst@myjus.in', 'analyst', 'analyst'))
    
    # 2. Instructors (5)
    for i in range(5):
        name = f"Prof. {random.choice(NAMES)} {random.choice(SURNAMES)}"
        email = f"prof{i}@iitkgp.ac.in"
        users.append((name, email, 'pass', 'instructor'))

    # 3. Students (50)
    for i in range(50):
        name = f"{random.choice(NAMES)} {random.choice(SURNAMES)}"
        email = f"student{i}@iitkgp.ac.in"
        users.append((name, email, 'pass', 'student'))

    # Insert Users
    user_ids = {'instructor': [], 'student': []}
    for name, email, pwd, role in users:
        hashed = generate_password_hash(pwd)
        cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (name, email, hashed, role))
        if role in user_ids:
            user_ids[role].append(cursor.lastrowid)
    
    conn.commit()
    print(f"   ✅ Created {len(users)} users.")

    print("📚 Seeding Courses...")
    course_ids = []
    for code, title in COURSES:
        instructor = random.choice(user_ids['instructor'])
        cursor.execute("INSERT INTO Courses (title, description, instructor_id) VALUES (%s, %s, %s)", 
                       (f"{code}: {title}", "A rigorous course at IIT Kharagpur.", instructor))
        course_ids.append(cursor.lastrowid)
    conn.commit()

    print("📝 Seeding Enrollments (Grades)...")
    # Randomly enroll students in courses
    grades = ['A', 'A', 'B', 'B', 'B', 'C', 'C', 'F', 'NA'] # Weighted probability
    count = 0
    for student_id in user_ids['student']:
        # Each student takes 3-6 courses
        num_courses = random.randint(3, 6)
        chosen_courses = random.sample(course_ids, num_courses)
        
        for course_id in chosen_courses:
            grade = random.choice(grades)
            cursor.execute("INSERT INTO Enrollments (student_id, course_id, grade) VALUES (%s, %s, %s)", 
                           (student_id, course_id, grade))
            count += 1
    conn.commit()
    print(f"   ✅ Created {count} enrollments with grades.")

    print("🔒 Seeding Security Logs...")
    for _ in range(20):
        uid = random.choice(user_ids['instructor'] + user_ids['student'])
        action = random.choice(LOG_ACTIONS)
        cursor.execute("INSERT INTO AuditLogs (user_id, action, details) VALUES (%s, %s, %s)",
                       (uid, action, "Automated test action"))
    conn.commit()

    cursor.close()
    conn.close()
    print("\n🚀 DATABASE POPULATED SUCCESSFULLY!")

if __name__ == "__main__":
    seed_data()