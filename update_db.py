import mysql.connector

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '',  # Ensure this is empty (as per your setup)
    'host': 'localhost',
    'database': 'course_db'
}

def update_schema():
    try:
        print("🚀 Connecting to database...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("🔧 Adding 'grade' column to Enrollments table...")
        
        # This SQL command adds the new column
        try:
            cursor.execute("ALTER TABLE Enrollments ADD COLUMN grade VARCHAR(5) DEFAULT 'NA'")
            print("   ✅ Success: Column 'grade' added.")
        except mysql.connector.Error as err:
            if "Duplicate column" in str(err):
                print("   ⚠️ Notice: Column 'grade' already exists. Skipping.")
            else:
                print(f"   ❌ Error: {err}")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Schema update complete!")

    except mysql.connector.Error as err:
        print(f"❌ Critical Error: {err}")

if __name__ == "__main__":
    update_schema()