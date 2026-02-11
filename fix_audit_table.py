import mysql.connector

# Database Configuration
db_config = {
    'user': 'root',
    'password': '', 
    'host': 'localhost',
    'database': 'course_db'
}

def create_audit_table():
    try:
        print("🔧 Connecting to database...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("🩹 Creating missing 'AuditLogs' table...")
        
        # The SQL Command to create the missing table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS AuditLogs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            action VARCHAR(255),
            details VARCHAR(255),
            ip_address VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("   ✅ Success: 'AuditLogs' table created!")
        
        cursor.close()
        conn.close()
        print("\n🎉 Fix complete! You can run app.py now.")

    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")

if __name__ == "__main__":
    create_audit_table()