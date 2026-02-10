import mysql.connector
from werkzeug.security import generate_password_hash

# --- CONFIG ---
db_config = {
    'user': 'root',
    'password': '',  # Use YOUR database password
    'host': 'localhost',
    'database': 'course_db'
}

# --- CONNECT ---
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    print("1. Deleting old insecure users...")
    cursor.execute("DELETE FROM Users")

    print("2. Creating secure hashed passwords...")
    # We use the same password '12345' for everyone for simplicity
    pw_hash = generate_password_hash('12345')

    print("3. Inserting new secure users...")
    users = [
        ('Admin Boss', 'admin@iitkgp.ac.in', pw_hash, 'admin'),
        ('Prof. Sharma', 'sharma@iitkgp.ac.in', pw_hash, 'instructor'),
        ('Ashish Sitare', 'ashish@student.iitkgp.ac.in', pw_hash, 'student'),
        ('Data Guy', 'analyst@iitkgp.ac.in', pw_hash, 'analyst')
    ]

    query = "INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)"
    cursor.executemany(query, users)
    
    conn.commit()
    print("SUCCESS! Database updated with hashed passwords.")
    
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")