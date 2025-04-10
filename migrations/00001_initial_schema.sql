-- Initial schema for ArtificialU PostgreSQL database

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    code VARCHAR NOT NULL UNIQUE,
    faculty VARCHAR NOT NULL,
    description TEXT NOT NULL
);

-- Professors table
CREATE TABLE IF NOT EXISTS professors (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    department VARCHAR NOT NULL,
    specialization VARCHAR NOT NULL,
    background TEXT NOT NULL,
    personality TEXT NOT NULL,
    teaching_style TEXT NOT NULL,
    gender VARCHAR,
    accent VARCHAR,
    description TEXT,
    age INTEGER,
    voice_settings TEXT,
    image_path VARCHAR
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id VARCHAR PRIMARY KEY,
    code VARCHAR NOT NULL UNIQUE,
    title VARCHAR NOT NULL,
    department VARCHAR NOT NULL,
    level VARCHAR NOT NULL,
    credits INTEGER NOT NULL DEFAULT 3,
    professor_id VARCHAR NOT NULL,
    description TEXT NOT NULL,
    lectures_per_week INTEGER NOT NULL DEFAULT 2,
    total_weeks INTEGER NOT NULL DEFAULT 14,
    syllabus TEXT,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors (id)
);

-- Lectures table
CREATE TABLE IF NOT EXISTS lectures (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    course_id VARCHAR NOT NULL,
    week_number INTEGER NOT NULL,
    order_in_week INTEGER NOT NULL DEFAULT 1,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    audio_path VARCHAR,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_professors_department ON professors (department);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses (department);
CREATE INDEX IF NOT EXISTS idx_courses_professor_id ON courses (professor_id);
CREATE INDEX IF NOT EXISTS idx_lectures_course_id ON lectures (course_id);
CREATE INDEX IF NOT EXISTS idx_lectures_week_order ON lectures (course_id, week_number, order_in_week); 