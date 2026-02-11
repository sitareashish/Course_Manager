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
    return mysql.connector.connect(**db_config)

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    if 'user_id' in session:
        role_map = {'admin': 'admin_dashboard', 'student': 'student_dashboard', 
                    'instructor': 'instructor_dashboard', 'analyst': 'analyst_dashboard'}
        return redirect(url_for(role_map.get(session['role'], 'login')))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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

# --- ADMIN DASHBOARD (REVERTED) ---
# --- ADVANCED ADMIN DASHBOARD ---
# --- ADMIN DASHBOARD WITH SORTING & PAGINATION ---
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    # 1. Get Parameters from URL (Defaults: Limit=10, Sort=created_at, Order=DESC)
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    # 2. Whitelist columns to prevent SQL Injection
    valid_columns = ['user_id', 'name', 'email', 'role', 'created_at']
    if sort_by not in valid_columns: sort_by = 'created_at'
    if order not in ['asc', 'desc']: order = 'desc'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 3. Dynamic SQL Query
    query = f"SELECT * FROM Users ORDER BY {sort_by} {order.upper()} LIMIT {limit}"
    cursor.execute(query)
    users = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) as count FROM Users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT c.course_id, c.title, u.name as instructor_name FROM Courses c LEFT JOIN Users u ON c.instructor_id = u.user_id")
    courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           users=users, 
                           courses=courses, 
                           total_users=total_users, 
                           current_limit=limit,
                           current_sort=sort_by,
                           current_order=order)

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
        flash(f'User {name} created.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
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
        flash('Course added.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
    return redirect(url_for('admin_dashboard'))

# --- OTHER DASHBOARDS (UNCHANGED) ---
@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT c.course_id, c.title, c.description, e.grade FROM Enrollments e JOIN Courses c ON e.course_id = c.course_id WHERE e.student_id = %s", (user_id,))
    my_courses = cursor.fetchall()
    cursor.execute("SELECT * FROM Courses WHERE course_id NOT IN (SELECT course_id FROM Enrollments WHERE student_id = %s)", (user_id,))
    available_courses = cursor.fetchall()
    grades = [c['grade'] for c in my_courses if c['grade'] != 'NA']
    grade_counts = {g: grades.count(g) for g in ['A', 'B', 'C', 'F']}
    cursor.close(); conn.close()
    return render_template('student_dashboard.html', my_courses=my_courses, available_courses=available_courses, grade_counts=grade_counts)

@app.route('/enroll', methods=['POST'])
def enroll():
    if session.get('role') != 'student': return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Enrollments (student_id, course_id) VALUES (%s, %s)", (session['user_id'], request.form['course_id']))
        conn.commit()
    except: pass
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
            cursor.execute("SELECT u.user_id as student_id, u.name, u.email, e.grade FROM Enrollments e JOIN Users u ON e.student_id = u.user_id WHERE e.course_id = %s", (course_id,))
            students = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('instructor_dashboard.html', courses=my_courses, selected_course=selected_course, students=students)

@app.route('/update_grade', methods=['POST'])
def update_grade():
    if session.get('role') != 'instructor': return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Enrollments SET grade = %s WHERE course_id = %s AND student_id = %s", (request.form['grade'], request.form['course_id'], request.form['student_id']))
        conn.commit()
    except: pass
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
    return redirect(url_for('instructor_dashboard', course_id=request.form['course_id']))

@app.route('/analyst')
def analyst_dashboard():
    # KEEPING YOUR ANALYST FEATURES (Since you only asked to revert Admin)
    if session.get('role') != 'analyst': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM Users WHERE role='student'")
    total_students = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM Courses")
    total_courses = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM Enrollments")
    total_enrollments = cursor.fetchone()['count']
    cursor.execute("SELECT u.name, u.email, c.title as course, e.grade FROM Enrollments e JOIN Users u ON e.student_id = u.user_id JOIN Courses c ON e.course_id = c.course_id WHERE e.grade = 'F' LIMIT 5")
    at_risk_students = cursor.fetchall()
    cursor.execute("SELECT c.title, COUNT(e.student_id) as total, SUM(CASE WHEN e.grade != 'F' AND e.grade != 'NA' THEN 1 ELSE 0 END) as passed FROM Courses c JOIN Enrollments e ON c.course_id = e.course_id GROUP BY c.course_id, c.title HAVING total > 0 ORDER BY (passed/total) ASC LIMIT 5")
    hardest_courses = cursor.fetchall()
    cursor.execute("SELECT grade, COUNT(*) as count FROM Enrollments WHERE grade != 'NA' GROUP BY grade")
    grade_data = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('analyst_dashboard.html', total_students=total_students, total_courses=total_courses, total_enrollments=total_enrollments, at_risk_students=at_risk_students, hardest_courses=hardest_courses, grades=[row['grade'] for row in grade_data], grade_counts=[row['count'] for row in grade_data])

if __name__ == '__main__':
    app.run(debug=True, port=5000)