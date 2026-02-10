-- 1. Create and Select the Database
CREATE DATABASE IF NOT EXISTS course_db;
USE course_db;

-- 2. Create Users Table
-- Stores Admins, Instructors, Students, and Analysts
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL, -- Stores Hashed Passwords
    role ENUM('admin', 'instructor', 'student', 'analyst') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Courses Table
-- Links to an Instructor (User)
CREATE TABLE IF NOT EXISTS Courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    instructor_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

-- 4. Create Enrollments Table (Many-to-Many Relationship)
-- Links Students to Courses and stores their Grade
CREATE TABLE IF NOT EXISTS Enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    grade VARCHAR(5) DEFAULT 'NA', -- Stores grades like 'A', 'B', 'C', 'NA'
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id) -- Prevents duplicate enrollments
);

-- Optional: Create a View for easier Analysis (Bonus Marks for DBMS)
CREATE OR REPLACE VIEW StudentGrades AS
SELECT 
    U.name AS Student_Name, 
    C.title AS Course_Title, 
    E.grade AS Grade 
FROM Enrollments E
JOIN Users U ON E.student_id = U.user_id
JOIN Courses C ON E.course_id = C.course_id;