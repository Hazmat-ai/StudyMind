-- ============================================================
-- CP372 Assignment 5 — StudyMind Database
-- Schema: rizv5908
-- Student: rizv5908
-- Date: 2026-06-19
-- ============================================================

USE rizv5908;

-- ============================================================
-- DROP everything in reverse dependency order (for re-runs)
-- ============================================================
DROP EVENT   IF EXISTS ev_deactivate_old_courses;
DROP TRIGGER IF EXISTS trg_check_marks_update;
DROP TRIGGER IF EXISTS trg_check_marks_insert;
DROP PROCEDURE IF EXISTS sp_enroll_student;
DROP FUNCTION  IF EXISTS fn_student_average;
DROP VIEW IF EXISTS vEnrollmentDetails;
DROP VIEW IF EXISTS vCourseCategory;
DROP TABLE IF EXISTS submission;
DROP TABLE IF EXISTS assignment;
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS instructor;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS category;

-- ============================================================
-- TABLE 1: category (lookup table, auto-increment PK)
-- ============================================================
CREATE TABLE category (
    category_id   INT           NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(50)   NOT NULL,
    category_desc LONGTEXT      NULL,
    CONSTRAINT pk_category PRIMARY KEY (category_id),
    CONSTRAINT uq_category_name UNIQUE (category_name)
) ENGINE=InnoDB;

-- Non-DATE/TIME field with a custom default — handled via course.max_students
-- Unique index on non-PK: category_name (above)

-- ============================================================
-- TABLE 2: instructor (natural PK — employee ID like 'EMP000001')
-- ============================================================
CREATE TABLE instructor (
    instructor_id CHAR(9)       NOT NULL,
    first_name    VARCHAR(50)   NOT NULL,
    last_name     VARCHAR(50)   NOT NULL,
    email         VARCHAR(100)  NOT NULL,
    hire_date     DATE          NOT NULL,
    salary        DECIMAL(10,2) NOT NULL,
    CONSTRAINT pk_instructor PRIMARY KEY (instructor_id),
    CONSTRAINT uq_instructor_email UNIQUE (email)
) ENGINE=InnoDB;

-- Non-unique index on last_name
CREATE INDEX idx_instructor_last_name ON instructor (last_name);

-- ============================================================
-- TABLE 3: student (natural PK — student ID like '200123456')
-- ============================================================
CREATE TABLE student (
    student_id  CHAR(9)       NOT NULL,
    first_name  VARCHAR(50)   NOT NULL,
    last_name   VARCHAR(50)   NOT NULL,
    email       VARCHAR(100)  NOT NULL,
    enroll_date DATE          NOT NULL,
    gpa         DECIMAL(3,2)  NULL,        -- NULL allowed
    CONSTRAINT pk_student PRIMARY KEY (student_id),
    CONSTRAINT uq_student_email UNIQUE (email)
) ENGINE=InnoDB;

-- Non-unique index on last_name
CREATE INDEX idx_student_last_name ON student (last_name);

-- ============================================================
-- TABLE 4: course  (both FK source AND destination)
--   FK source  -> category, instructor
--   FK dest    <- enrollment, assignment
-- ============================================================
CREATE TABLE course (
    course_id     INT          NOT NULL AUTO_INCREMENT,
    course_code   CHAR(8)      NOT NULL,
    course_title  VARCHAR(100) NOT NULL,
    category_id   INT          NOT NULL,
    instructor_id CHAR(9)      NOT NULL,
    max_students  INT          NOT NULL DEFAULT 30,   -- custom non-DATE default
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active     CHAR(1)      NOT NULL DEFAULT 'Y',
    CONSTRAINT pk_course       PRIMARY KEY (course_id),
    CONSTRAINT uq_course_code  UNIQUE (course_code),
    CONSTRAINT fk_course_category
        FOREIGN KEY (category_id)   REFERENCES category(category_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_course_instructor
        FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Non-unique index on is_active (often queried)
CREATE INDEX idx_course_active ON course (is_active);

-- ============================================================
-- TABLE 5: enrollment (composite PK — student_id + course_id)
--   Both FK source AND destination
--   Part of two-step FK chain: enrollment -> course -> category
-- ============================================================
CREATE TABLE enrollment (
    student_id  CHAR(9)      NOT NULL,
    course_id   INT          NOT NULL,
    enrolled_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status      VARCHAR(20)  NOT NULL DEFAULT 'active',
    CONSTRAINT pk_enrollment PRIMARY KEY (student_id, course_id),
    CONSTRAINT fk_enrollment_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_enrollment_course
        FOREIGN KEY (course_id)  REFERENCES course(course_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 6: assignment (course content)
--   FK source -> course
--   FK dest   <- submission
-- ============================================================
CREATE TABLE assignment (
    assignment_id INT           NOT NULL AUTO_INCREMENT,
    course_id     INT           NOT NULL,
    title         VARCHAR(100)  NOT NULL,
    description   LONGTEXT      NULL,                      -- NULL allowed
    due_date      DATETIME      NOT NULL,
    max_marks     DECIMAL(5,2)  NOT NULL DEFAULT 100.00,   -- custom default
    CONSTRAINT pk_assignment PRIMARY KEY (assignment_id),
    CONSTRAINT fk_assignment_course
        FOREIGN KEY (course_id) REFERENCES course(course_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Non-unique index on due_date
CREATE INDEX idx_assignment_due_date ON assignment (due_date);

-- ============================================================
-- TABLE 7: submission (student work on assignments)
--   Two-step FK chain: submission -> assignment -> course
-- ============================================================
CREATE TABLE submission (
    submission_id  INT           NOT NULL AUTO_INCREMENT,
    assignment_id  INT           NOT NULL,
    student_id     CHAR(9)       NOT NULL,
    submitted_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    marks_received DECIMAL(5,2)  NULL,     -- NULL = not graded
    feedback       LONGTEXT      NULL,     -- NULL allowed
    CONSTRAINT pk_submission PRIMARY KEY (submission_id),
    CONSTRAINT fk_submission_assignment
        FOREIGN KEY (assignment_id) REFERENCES assignment(assignment_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_submission_student
        FOREIGN KEY (student_id)    REFERENCES student(student_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Non-unique index on student_id for performance
CREATE INDEX idx_submission_student ON submission (student_id);

-- ============================================================
-- VIEWS
-- ============================================================

-- View 1: vCourseCategory — two-table FK relationship (course + category)
CREATE VIEW vCourseCategory AS
    SELECT
        c.course_id,
        c.course_code,
        c.course_title,
        c.max_students,
        c.is_active,
        ct.category_name,
        ct.category_desc
    FROM course c
    JOIN category ct ON c.category_id = ct.category_id;

-- View 2: vEnrollmentDetails — three-table FK relationship (enrollment + course + category)
CREATE VIEW vEnrollmentDetails AS
    SELECT
        e.student_id,
        e.enrolled_at,
        e.status,
        c.course_code,
        c.course_title,
        ct.category_name
    FROM enrollment e
    JOIN course    c  ON e.course_id    = c.course_id
    JOIN category  ct ON c.category_id  = ct.category_id;

-- ============================================================
-- STORED PROCEDURE: sp_enroll_student
-- Enrolls a student if not already enrolled and course has capacity
-- ============================================================
DELIMITER $$

CREATE PROCEDURE sp_enroll_student (
    IN  p_student_id CHAR(9),
    IN  p_course_id  INT
)
BEGIN
    DECLARE v_count      INT DEFAULT 0;
    DECLARE v_enrolled   INT DEFAULT 0;
    DECLARE v_max        INT DEFAULT 0;

    -- Check if student already enrolled
    SELECT COUNT(*) INTO v_enrolled
    FROM enrollment
    WHERE student_id = p_student_id AND course_id = p_course_id;

    IF v_enrolled > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Student is already enrolled in this course';
    END IF;

    -- Check course capacity
    SELECT max_students INTO v_max
    FROM course
    WHERE course_id = p_course_id;

    SELECT COUNT(*) INTO v_count
    FROM enrollment
    WHERE course_id = p_course_id;

    IF v_count >= v_max THEN
        SIGNAL SQLSTATE '45001'
            SET MESSAGE_TEXT = 'Course has reached maximum capacity';
    END IF;

    -- Enroll the student
    INSERT INTO enrollment (student_id, course_id)
    VALUES (p_student_id, p_course_id);

END$$

-- ============================================================
-- STORED FUNCTION: fn_student_average
-- Returns the average marks received for a student (NULL if no graded submissions)
-- ============================================================
CREATE FUNCTION fn_student_average (
    p_student_id CHAR(9)
)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(5,2);

    SELECT AVG(marks_received) INTO v_avg
    FROM submission
    WHERE student_id = p_student_id
      AND marks_received IS NOT NULL;

    RETURN v_avg;
END$$

-- ============================================================
-- TRIGGER: trg_check_marks_insert
-- Acts as CHECK constraint: marks_received must not exceed max_marks
-- ============================================================
CREATE TRIGGER trg_check_marks_insert
BEFORE INSERT ON submission
FOR EACH ROW
BEGIN
    DECLARE v_max DECIMAL(5,2);

    IF NEW.marks_received IS NOT NULL THEN
        SELECT max_marks INTO v_max
        FROM assignment
        WHERE assignment_id = NEW.assignment_id;

        IF NEW.marks_received > v_max THEN
            SIGNAL SQLSTATE '45002'
                SET MESSAGE_TEXT = 'marks_received cannot exceed max_marks for this assignment';
        END IF;

        IF NEW.marks_received < 0 THEN
            SIGNAL SQLSTATE '45003'
                SET MESSAGE_TEXT = 'marks_received cannot be negative';
        END IF;
    END IF;
END$$

-- ============================================================
-- TRIGGER: trg_check_marks_update
-- Same CHECK constraint applied on UPDATE
-- ============================================================
CREATE TRIGGER trg_check_marks_update
BEFORE UPDATE ON submission
FOR EACH ROW
BEGIN
    DECLARE v_max DECIMAL(5,2);

    IF NEW.marks_received IS NOT NULL THEN
        SELECT max_marks INTO v_max
        FROM assignment
        WHERE assignment_id = NEW.assignment_id;

        IF NEW.marks_received > v_max THEN
            SIGNAL SQLSTATE '45002'
                SET MESSAGE_TEXT = 'marks_received cannot exceed max_marks for this assignment';
        END IF;

        IF NEW.marks_received < 0 THEN
            SIGNAL SQLSTATE '45003'
                SET MESSAGE_TEXT = 'marks_received cannot be negative';
        END IF;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- EVENT: ev_deactivate_old_courses
-- Runs every week: deactivates courses where all due dates
-- are older than 180 days and no active enrollments remain
-- ============================================================
DELIMITER $$

CREATE EVENT ev_deactivate_old_courses
ON SCHEDULE EVERY 1 WEEK
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    UPDATE course
    SET is_active = 'N'
    WHERE is_active = 'Y'
      AND course_id NOT IN (
          SELECT DISTINCT course_id
          FROM enrollment
          WHERE status = 'active'
      )
      AND course_id IN (
          SELECT course_id
          FROM assignment
          GROUP BY course_id
          HAVING MAX(due_date) < DATE_SUB(NOW(), INTERVAL 180 DAY)
      );
END$$

DELIMITER ;

-- ============================================================
-- DATA INSERTION
-- ============================================================

-- category (≥3 rows, lookup table)
INSERT INTO category (category_name, category_desc) VALUES
    ('Computer Science', 'Courses covering programming, algorithms, databases, and software engineering'),
    ('Mathematics',      'Courses in calculus, linear algebra, statistics, and discrete math'),
    ('Business',         'Courses covering management, marketing, finance, and entrepreneurship'),
    ('Natural Sciences', 'Biology, chemistry, physics, and environmental science courses'),
    ('Humanities',       NULL);

-- instructor (≥3 rows, natural PK)
INSERT INTO instructor (instructor_id, first_name, last_name, email, hire_date, salary) VALUES
    ('EMP000001', 'Alice',   'Chen',     'achen@studymind.ca',    '2018-09-01', 92500.00),
    ('EMP000002', 'Bob',     'Martinez', 'bmartinez@studymind.ca','2015-01-15', 105000.00),
    ('EMP000003', 'Carol',   'Johnson',  'cjohnson@studymind.ca', '2020-07-01', 88000.00),
    ('EMP000004', 'David',   'Patel',    'dpatel@studymind.ca',   '2019-03-20', 97000.00),
    ('EMP000005', 'Evelyn',  'Turner',   'eturner@studymind.ca',  '2022-01-10', 79500.00);

-- student (≥3 rows, natural PK)
INSERT INTO student (student_id, first_name, last_name, email, enroll_date, gpa) VALUES
    ('200100001', 'Hamza',   'Rizvi',    'rizv5908@mylaurier.ca',  '2023-09-05', 3.85),
    ('200100002', 'Sarah',   'Kim',      'sarak@mylaurier.ca',     '2023-09-05', 3.70),
    ('200100003', 'James',   'Okonkwo',  'jokow@mylaurier.ca',     '2023-09-05', 3.50),
    ('200100004', 'Priya',   'Singh',    'psingh@mylaurier.ca',    '2024-01-08', 3.92),
    ('200100005', 'Lucas',   'Bouchard', 'lbouch@mylaurier.ca',    '2024-01-08', NULL),
    ('200100006', 'Mei',     'Wong',     'mwong@mylaurier.ca',     '2024-01-08', 3.30),
    ('200100007', 'Omar',    'Hassan',   'ohassan@mylaurier.ca',   '2024-05-01', 3.10),
    ('200100008', 'Nina',    'Kowalski', 'nkowal@mylaurier.ca',    '2024-05-01', 3.65),
    ('200100009', 'Ethan',   'Leblanc',  'elebl@mylaurier.ca',     '2024-09-04', 2.95),
    ('200100010', 'Fatima',  'Diallo',   'fdiallo@mylaurier.ca',   '2024-09-04', 3.75);

-- course (≥3 rows, uses category + instructor FKs)
INSERT INTO course (course_code, course_title, category_id, instructor_id, max_students, is_active) VALUES
    ('CP100001', 'Intro to Programming',       1, 'EMP000001', 35, 'Y'),
    ('CP200001', 'Data Structures',            1, 'EMP000002', 30, 'Y'),
    ('CP363001', 'Database Management',        1, 'EMP000003', 30, 'Y'),
    ('MA100001', 'Calculus I',                 2, 'EMP000004', 40, 'Y'),
    ('BU200001', 'Principles of Marketing',    3, 'EMP000005', 45, 'Y'),
    ('NS100001', 'Introduction to Biology',    4, 'EMP000001', 35, 'N');

-- enrollment (composite PK, ≥3 rows)
INSERT INTO enrollment (student_id, course_id, status) VALUES
    ('200100001', 1, 'active'),
    ('200100001', 3, 'active'),
    ('200100002', 1, 'active'),
    ('200100002', 4, 'active'),
    ('200100003', 2, 'active'),
    ('200100003', 3, 'active'),
    ('200100004', 1, 'active'),
    ('200100004', 5, 'active'),
    ('200100005', 2, 'completed'),
    ('200100006', 3, 'active'),
    ('200100007', 4, 'active'),
    ('200100008', 5, 'active'),
    ('200100009', 1, 'active'),
    ('200100010', 2, 'active');

-- assignment (≥3 rows)
INSERT INTO assignment (course_id, title, description, due_date, max_marks) VALUES
    (1, 'Hello World Program',   'Write a hello world program in Python',         '2026-10-01 23:59:00', 100.00),
    (1, 'Loops and Functions',   'Implement sorting functions using loops',        '2026-10-20 23:59:00', 100.00),
    (2, 'Linked List Lab',       'Implement a singly linked list in Java',         '2026-10-15 23:59:00', 100.00),
    (2, 'Binary Search Tree',    'Build and traverse a BST',                       '2026-11-01 23:59:00', 100.00),
    (3, 'ER Diagram',            'Design an ER diagram for a library system',      '2026-10-10 23:59:00',  50.00),
    (3, 'SQL Queries Assignment',NULL,                                             '2026-11-15 23:59:00', 100.00),
    (4, 'Derivatives Quiz',      'Differentiate 20 functions using chain rule',    '2026-10-05 23:59:00',  75.00),
    (5, 'Marketing Plan',        'Create a marketing plan for a startup product',  '2026-11-20 23:59:00', 150.00);

-- submission (≥10 rows)
INSERT INTO submission (assignment_id, student_id, submitted_at, marks_received, feedback) VALUES
    (1, '200100001', '2026-09-30 14:22:00', 95.00, 'Excellent work, clean code'),
    (1, '200100002', '2026-09-30 18:05:00', 88.00, 'Good but missing comments'),
    (1, '200100004', '2026-10-01 09:10:00', 92.00, NULL),
    (1, '200100009', '2026-10-01 22:55:00', 78.00, 'Needs improvement on variable naming'),
    (2, '200100001', '2026-10-19 20:30:00', 98.00, 'Outstanding submission'),
    (2, '200100002', '2026-10-20 11:00:00', 85.00, 'Good implementation'),
    (3, '200100003', '2026-10-14 16:45:00', 90.00, 'Well-structured linked list'),
    (3, '200100010', '2026-10-15 08:00:00', 82.00, 'Minor edge case missed'),
    (5, '200100001', '2026-10-09 23:45:00', 48.00, 'Good ER diagram, minor relationship errors'),
    (5, '200100003', '2026-10-10 12:30:00', 45.00, 'Solid effort'),
    (5, '200100006', '2026-10-10 22:10:00', 50.00, 'Perfect score'),
    (7, '200100002', '2026-10-04 19:30:00', 70.00, NULL),
    (7, '200100007', '2026-10-05 10:00:00', NULL,  NULL);

-- ============================================================
-- VERIFICATION QUERIES (run these to confirm everything works)
-- ============================================================

-- Show all tables
SHOW TABLES;

-- Count rows in each table
SELECT 'category'   AS tbl, COUNT(*) AS rows FROM category
UNION ALL
SELECT 'instructor', COUNT(*) FROM instructor
UNION ALL
SELECT 'student',    COUNT(*) FROM student
UNION ALL
SELECT 'course',     COUNT(*) FROM course
UNION ALL
SELECT 'enrollment', COUNT(*) FROM enrollment
UNION ALL
SELECT 'assignment', COUNT(*) FROM assignment
UNION ALL
SELECT 'submission', COUNT(*) FROM submission;

-- Test the views
SELECT * FROM vCourseCategory;
SELECT * FROM vEnrollmentDetails;

-- Test the function
SELECT fn_student_average('200100001') AS avg_marks;

-- Test the procedure
CALL sp_enroll_student('200100005', 1);
