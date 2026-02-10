from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'myjus_platform_secret_key_2026'

# Database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'course_db'
}

def get_db_connection():
    """Establishes a connection to the backend database."""
    return mysql.connector.connect(**db_config)

# --- PUBLIC ROUTES ---

@app.route('/')
def index():
    """Landing page route."""
    if 'user_id' in session:
        # Redirect authenticated users to their respective dashboards
        role_map = {
            'admin': 'admin_dashboard',
            'student': 'student_dashboard',
            'instructor': 'instructor_dashboard',
            'analyst': 'analyst_dashboard'
        }
        return redirect(url_for(role_map.get(session['role'], 'login')))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user authentication."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['name'] = user['name']
                session['role'] = user['role']
                
                flash(f"Welcome back, {user['name']}", 'success')
                
                if user['role'] == 'admin': return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'student': return redirect(url_for('student_dashboard'))
                elif user['role'] == 'instructor': return redirect(url_for('instructor_dashboard'))
                elif user['role'] == 'analyst': return redirect(url_for('analyst_dashboard'))
            else:
                flash('Invalid credentials provided.', 'danger')
                
        except mysql.connector.Error as err:
            flash(f"System Error: {err}", 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Mock password recovery flow."""
    if request.method == 'POST':
        email = request.form['email']
        # In production, integrate SMTP here.
        flash(f'Reset instructions sent to {email}', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

# --- ROLE-BASED DASHBOARDS ---

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Users ORDER BY created_at DESC")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Courses")
    courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, courses=courses)

@app.route('/add_user', methods=['POST'])
def add_user():
    if session.get('role') != 'admin': return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    hashed_pw = generate_password_hash(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                       (name, email, hashed_pw, role))
        conn.commit()
        flash(f'User {name} created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating user: {e}', 'danger')
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') != 'admin': return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Courses (title, description, instructor_id) VALUES (%s, %s, %s)", 
                       (request.form['title'], request.form['description'], request.form['instructor_id']))
        conn.commit()
        flash('Course added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding course: {e}', 'danger')
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch enrolled courses with grades
    query_enrolled = """
        SELECT c.course_id, c.title, c.description, e.grade, e.enrollment_date
        FROM Enrollments e
        JOIN Courses c ON e.course_id = c.course_id 
        WHERE e.student_id = %s
    """
    cursor.execute(query_enrolled, (user_id,))
    my_courses = cursor.fetchall()
    
    # Fetch available courses
    query_available = """
        SELECT * FROM Courses 
        WHERE course_id NOT IN (SELECT course_id FROM Enrollments WHERE student_id = %s)
    """
    cursor.execute(query_available, (user_id,))
    available_courses = cursor.fetchall()
    
    # Calculate performance metrics
    grades = [c['grade'] for c in my_courses if c['grade'] != 'NA']
    grade_counts = {g: grades.count(g) for g in ['A', 'B', 'C', 'F']}
    
    cursor.close()
    conn.close()
    
    return render_template('student_dashboard.html', 
                           my_courses=my_courses, 
                           available_courses=available_courses,
                           grade_counts=grade_counts)

@app.route('/enroll', methods=['POST'])
def enroll():
    if session.get('role') != 'student': return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Enrollments (student_id, course_id) VALUES (%s, %s)", 
                       (session['user_id'], request.form['course_id']))
        conn.commit()
        flash('Enrollment successful.', 'success')
    except Exception as e:
        flash('Enrollment failed. You might already be enrolled.', 'warning')
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
        
    return redirect(url_for('student_dashboard'))

@app.route('/instructor')
def instructor_dashboard():
    if session.get('role') != 'instructor': return redirect(url_for('login'))
    
    instructor_id = session['user_id']
    course_id = request.args.get('course_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Courses WHERE instructor_id = %s", (instructor_id,))
    my_courses = cursor.fetchall()
    
    selected_course = None
    students = []
    
    if course_id:
        cursor.execute("SELECT * FROM Courses WHERE course_id = %s AND instructor_id = %s", (course_id, instructor_id))
        selected_course = cursor.fetchone()
        
        if selected_course:
            cursor.execute("""
                SELECT u.user_id as student_id, u.name, u.email, e.grade
                FROM Enrollments e
                JOIN Users u ON e.student_id = u.user_id
                WHERE e.course_id = %s
            """, (course_id,))
            students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('instructor_dashboard.html', 
                           courses=my_courses, 
                           selected_course=selected_course, 
                           students=students)

@app.route('/update_grade', methods=['POST'])
def update_grade():
    if session.get('role') != 'instructor': return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Enrollments SET grade = %s WHERE course_id = %s AND student_id = %s", 
                       (request.form['grade'], request.form['course_id'], request.form['student_id']))
        conn.commit()
        flash('Grade updated.', 'success')
    except Exception as e:
        flash(f'Update failed: {e}', 'danger')
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
        
    return redirect(url_for('instructor_dashboard', course_id=request.form['course_id']))

@app.route('/analyst')
def analyst_dashboard():
    if session.get('role') != 'analyst': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch KPIs
    cursor.execute("SELECT COUNT(*) FROM Users WHERE role='student'")
    total_students = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Courses")
    total_courses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Enrollments")
    total_enrollments = cursor.fetchone()[0]
    
    # Analytics: Course Popularity
    cursor.execute("""
        SELECT c.title, COUNT(e.student_id) 
        FROM Courses c
        LEFT JOIN Enrollments e ON c.course_id = e.course_id 
        GROUP BY c.course_id, c.title
    """)
    course_data = cursor.fetchall()
    
    # Analytics: Grade Distribution
    cursor.execute("SELECT grade, COUNT(*) FROM Enrollments WHERE grade != 'NA' GROUP BY grade")
    grade_data = cursor.fetchall()
    
    # Analytics: Top Performers
    cursor.execute("""
        SELECT u.name, u.email, COUNT(e.grade) as a_count
        FROM Users u
        JOIN Enrollments e ON u.user_id = e.student_id
        WHERE e.grade = 'A'
        GROUP BY u.user_id
        ORDER BY a_count DESC
        LIMIT 5
    """)
    top_students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('analyst_dashboard.html', 
                           total_students=total_students,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           course_names=[row[0] for row in course_data],
                           enrollment_counts=[row[1] for row in course_data],
                           grades=[row[0] for row in grade_data],
                           grade_counts=[row[1] for row in grade_data],
                           top_students=top_students)

if __name__ == '__main__':
    app.run(debug=True, port=5000)