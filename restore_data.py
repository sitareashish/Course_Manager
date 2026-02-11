import mysql.connector
from werkzeug.security import generate_password_hash

# Config
db_config = {'user': 'root', 'password': '', 'host': 'localhost', 'database': 'course_db'}

def restore():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 1. Clear Everything
    print("🧹 Cleaning database...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE Users")
    cursor.execute("TRUNCATE TABLE Courses")
    cursor.execute("TRUNCATE TABLE Enrollments")
    # We ignore AuditLogs table, it can stay empty
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 2. Add Your Preferred Admin
    print("👤 Restoring Admin...")
    admin_pw = generate_password_hash("12345")
    cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                   ("Ashish Admin", "admin@iitkgp.ac.in", admin_pw, "admin"))
    
    # 3. Add a Student
    student_pw = generate_password_hash("12345")
    cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                   ("Test Student", "student@iitkgp.ac.in", student_pw, "student"))

    conn.commit()
    conn.close()
    print("✅ RESTORE COMPLETE!")
    print("👉 Login with: admin@iitkgp.ac.in / 12345")

if __name__ == "__main__":
    restore()