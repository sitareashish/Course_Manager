import mysql.connector

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '', 
    'host': 'localhost',
    'database': 'course_db'
}

def patch_database():
    try:
        print("🔧 Connecting to database...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print(" Attempting to add missing 'created_at' column...")
        
        # 1. Fix Users Table
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print(" Success: Added 'created_at' to Users table.")
        except mysql.connector.Error as err:
            if "Duplicate column" in str(err):
                print(" Notice: 'created_at' already exists in Users.")
            else:
                print(f"  Error updating Users: {err}")

        # 2. Fix Courses Table (Just in case)
        try:
            cursor.execute("ALTER TABLE Courses ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print(" Success: Added 'created_at' to Courses table.")
        except mysql.connector.Error as err:
            if "Duplicate column" in str(err):
                print(" Notice: 'created_at' already exists in Courses.")
            else:
                print(f" Error updating Courses: {err}")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Database patched! You can run app.py now.")

    except mysql.connector.Error as err:
        print(f"Critical Connection Error: {err}")

if __name__ == "__main__":
    patch_database()