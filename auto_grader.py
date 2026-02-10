import mysql.connector
import random

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '', 
    'host': 'localhost',
    'database': 'course_db'
}

def auto_grade_students():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("🤖 AI Auto-Grader Initialized...")

        # 1. Find all students who don't have a grade yet ('NA')
        cursor.execute("SELECT enrollment_id FROM Enrollments WHERE grade = 'NA' OR grade IS NULL")
        enrollments = cursor.fetchall()
        
        if not enrollments:
            print("   ✅ No ungraded students found! Everyone is graded.")
            return

        print(f"   found {len(enrollments)} ungraded assignments. Grading now...")

        # 2. Define Grade Probabilities (Realistic Bell Curve)
        # A: 30%, B: 40%, C: 20%, D: 5%, F: 5%
        grade_options = ['A', 'B', 'C', 'D', 'F']
        weights = [30, 40, 20, 5, 5]

        updates = []
        for (enrollment_id,) in enrollments:
            # Pick a random grade based on weights
            assigned_grade = random.choices(grade_options, weights=weights, k=1)[0]
            updates.append((assigned_grade, enrollment_id))

        # 3. Bulk Update the Database
        query = "UPDATE Enrollments SET grade = %s WHERE enrollment_id = %s"
        cursor.executemany(query, updates)
        conn.commit()

        print(f"   🎉 Success! {len(updates)} students have been graded.")
        print("   (Distribution: Mostly A's and B's, rare F's)")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")

if __name__ == "__main__":
    auto_grade_students()