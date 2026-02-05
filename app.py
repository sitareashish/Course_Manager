from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_lab_demo'  # Required for sessions

# --- Database Configuration ---
db_config = {
    'user': 'root',
    'password': '',         
    'host': 'localhost',
    'database': 'course_db' 
}

# --- Helper: Get DB Connection ---
def get_db():
    conn = mysql.connector.connect(**db_config)
    return conn

# --- Route: Home (Redirects to Login) ---
@app.route('/')
def home():
    if 'user_id' in session:
        return f"<h1>Logged in as {session['role']}</h1> <a href='/logout'>Logout</a>"
    return redirect(url_for('login'))

# --- Route: Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            # Check if user exists
            query = "SELECT * FROM Users WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user:
                # Store user info in the Session (Browser Cookie)
                session['user_id'] = user['user_id']
                session['name'] = user['name']
                session['role'] = user['role']
                
                flash('Login Successful!', 'success')
                
                # Redirect based on Role (We will build these pages next)
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'student':
                    return redirect(url_for('student_dashboard'))
                elif user['role'] == 'instructor':
                    return redirect(url_for('instructor_dashboard'))
                elif user['role'] == 'analyst':
                    return redirect(url_for('analyst_dashboard'))
            else:
                flash('Invalid email or password', 'danger')
                
        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", 'danger')
            
    return render_template('login.html')

# --- Route: Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Placeholders for Dashboards (So the app doesn't crash) ---
# --- ADMIN ROUTES ---

@app.route('/admin')
def admin_dashboard():
    # Security Check
    if 'role' not in session or session['role'] != 'admin':
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Get all Users (for the table and dropdowns)
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    
    # 2. Get all Courses
    cursor.execute("SELECT * FROM Courses")
    courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, courses=courses)

@app.route('/add_user', methods=['POST'])
def add_user():
    # Security Check
    if 'role' not in session or session['role'] != 'admin': return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (name, email, password, role))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'User {name} added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/add_course', methods=['POST'])
def add_course():
    # Security Check
    if 'role' not in session or session['role'] != 'admin': return redirect(url_for('login'))

    title = request.form['title']
    description = request.form['description']
    instructor_id = request.form['instructor_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Courses (title, description, instructor_id) VALUES (%s, %s, %s)", 
                       (title, description, instructor_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'Course {title} created!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        
    return redirect(url_for('admin_dashboard'))

# --- STUDENT ROUTES ---

@app.route('/student')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student': return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Get courses the student is ALREADY enrolled in
    query_enrolled = """
        SELECT Courses.course_id, Courses.title, Courses.instructor_id 
        FROM Enrollments 
        JOIN Courses ON Enrollments.course_id = Courses.course_id 
        WHERE Enrollments.student_id = %s
    """
    cursor.execute(query_enrolled, (user_id,))
    my_courses = cursor.fetchall()
    
    # 2. Get courses the student is NOT enrolled in (Available)
    # This logic finds courses where the ID is NOT in the student's enrollment list
    query_available = """
        SELECT * FROM Courses 
        WHERE course_id NOT IN (
            SELECT course_id FROM Enrollments WHERE student_id = %s
        )
    """
    cursor.execute(query_available, (user_id,))
    available_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('student_dashboard.html', my_courses=my_courses, available_courses=available_courses)

@app.route('/enroll', methods=['POST'])
def enroll():
    if 'role' not in session or session['role'] != 'student': return redirect(url_for('login'))
    
    student_id = session['user_id']
    course_id = request.form['course_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Register the student
        cursor.execute("INSERT INTO Enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        flash('Successfully enrolled in course!', 'success')
        
    except mysql.connector.Error as err:
        flash(f'Error enrolling: {err}', 'danger')
        
    return redirect(url_for('student_dashboard'))

@app.route('/instructor')
def instructor_dashboard():
    if 'role' not in session or session['role'] != 'instructor': return redirect(url_for('login'))
    return "<h1>Instructor Dashboard</h1><a href='/logout'>Logout</a>"

# --- ANALYST ROUTES ---

@app.route('/analyst')
def analyst_dashboard():
    if 'role' not in session or session['role'] != 'analyst': return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Simple Counters for the KPI Cards
    cursor.execute("SELECT COUNT(*) FROM Users WHERE role='student'")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Courses")
    total_courses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Enrollments")
    total_enrollments = cursor.fetchone()[0]
    
    # 2. Complex Query for the Graph (Group By)
    # Counts enrollments for each course. Uses LEFT JOIN so empty courses show '0'.
    query_stats = """
        SELECT Courses.title, COUNT(Enrollments.student_id) as count
        FROM Courses
        LEFT JOIN Enrollments ON Courses.course_id = Enrollments.course_id
        GROUP BY Courses.course_id, Courses.title
    """
    cursor.execute(query_stats)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 3. Process Data for Chart.js (Separate into two lists)
    # results looks like: [('DBMS', 5), ('Algorithms', 2)]
    course_names = [row[0] for row in results]
    enrollment_counts = [row[1] for row in results]
    
    return render_template('analyst_dashboard.html', 
                           total_students=total_students,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           course_names=course_names,
                           enrollment_counts=enrollment_counts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)