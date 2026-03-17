CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL
);

INSERT INTO admin (username, password)
VALUES ('admin', '123');

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(50) UNIQUE NOT NULL,
    total_fee NUMERIC(10,2) DEFAULT 0
);

INSERT INTO courses (course_name, total_fee) VALUES
('MSCIT', 5000),
('Computer Typing', 7000),
('Tally', 4000),
('Advance Excel', 5000);

CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    dob DATE,
    address TEXT,
    mobile VARCHAR(15)
);

CREATE TABLE admissions (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id),
    course_id INT REFERENCES courses(id),
    fees_paid NUMERIC(10,2),
    total_fee NUMERIC(10,2),
    remaining_fee NUMERIC(10,2),
    academic_year VARCHAR(20),
    typing_mode VARCHAR(50),
    admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
