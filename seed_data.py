import mysql.connector
from werkzeug.security import generate_password_hash
from faker import Faker
import random

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '',  # Ensure this matches your DB
    'host': 'localhost',
    'database': 'course_db'
}

fake = Faker()
# Set locale to India to get names like "Sharma", "Patel", "Singh"
fake = Faker('en_IN') 

def seed_database():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    print("🚀 Starting Data Injection...")

    # 1. Clear existing data (Optional: Remove if you want to keep old data)
    print("   - Clearing old data...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE Enrollments")
    cursor.execute("TRUNCATE TABLE Courses")
    cursor.execute("TRUNCATE TABLE Users")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 2. Prepare Common Password
    common_password = generate_password_hash('12345')
    users_data = []
    
    # --- CREATE USERS ---
    print("   - Generating Users...")
    
    # A. Create Fixed Admin
    users_data.append(('Super Admin', 'admin@iitkgp.ac.in', common_password, 'admin'))
    
    # B. Create Fixed Analyst
    users_data.append(('Data Analyst', 'analyst@iitkgp.ac.in', common_password, 'analyst'))

    # C. Create 5 Instructors
    instructor_ids = []
    for _ in range(5):
        name = fake.name()
        email = f"{name.split()[0].lower()}@iitkgp.ac.in"
        users_data.append((name, email, common_password, 'instructor'))

    # D. Create 50 Students
    student_ids = []
    for _ in range(50):
        name = fake.name()
        email = fake.email()
        users_data.append((name, email, common_password, 'student'))

    # Insert All Users
    sql = "INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)"
    cursor.executemany(sql, users_data)
    conn.commit()
    print(f"     ✅ Added {len(users_data)} Users.")

    # --- GET IDs BACK ---
    # We need the real IDs from the database to link courses/enrollments
    cursor.execute("SELECT user_id FROM Users WHERE role='instructor'")
    instructor_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT user_id FROM Users WHERE role='student'")
    student_ids = [row[0] for row in cursor.fetchall()]

    # --- CREATE COURSES ---
    print("   - Generating Courses...")
    courses_data = []
    course_titles = [
        "Advanced Machine Learning", "Database Management Systems", "Compiler Design", 
        "Operating Systems", "Computer Networks", "Discrete Mathematics", 
        "Software Engineering", "Artificial Intelligence", "Cloud Computing", 
        "Blockchain Fundamentals", "Cyber Security", "Data Structures & Algorithms"
    ]

    for title in course_titles:
        desc = fake.paragraph(nb_sentences=2)
        inst_id = random.choice(instructor_ids)
        courses_data.append((title, desc, inst_id))

    sql = "INSERT INTO Courses (title, description, instructor_id) VALUES (%s, %s, %s)"
    cursor.executemany(sql, courses_data)
    conn.commit()
    print(f"     ✅ Added {len(courses_data)} Courses.")

    # --- GET COURSE IDs ---
    cursor.execute("SELECT course_id FROM Courses")
    course_ids = [row[0] for row in cursor.fetchall()]

    # --- CREATE ENROLLMENTS ---
    print("   - Enrolling Students...")
    enrollments_data = []
    
    # Randomly enroll students in 1 to 4 courses each
    for student in student_ids:
        # Pick 1 to 4 random courses
        courses_to_take = random.sample(course_ids, k=random.randint(1, 4))
        for course in courses_to_take:
            enrollments_data.append((student, course))

    sql = "INSERT INTO Enrollments (student_id, course_id) VALUES (%s, %s)"
    cursor.executemany(sql, enrollments_data)
    conn.commit()
    print(f"     ✅ Added {len(enrollments_data)} Enrollments.")

    cursor.close()
    conn.close()
    print("\n🎉 SUCCESS! Your database is now populated.")
    print("------------------------------------------------")
    print("🔑 Login Credentials for Testing:")
    print("   Admin:    admin@iitkgp.ac.in / 12345")
    print("   Analyst:  analyst@iitkgp.ac.in / 12345")
    print("   Any Student: (Use any email from DB) / 12345")
    print("------------------------------------------------")

if __name__ == "__main__":
    seed_database()