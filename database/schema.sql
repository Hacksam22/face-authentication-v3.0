-- School Attendance System SQLite Schema

PRAGMA foreign_keys = ON;

-- Students Table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    section TEXT NOT NULL,
    roll_number TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student UNIQUE (class_name, section, roll_number)
);

-- Teachers Table
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    teacher_uid TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Face Samples Table
CREATE TABLE IF NOT EXISTS face_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_role TEXT NOT NULL CHECK(user_role IN ('student', 'teacher')),
    user_id INTEGER NOT NULL,
    sample_path TEXT NOT NULL,
    sample_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_role TEXT NOT NULL CHECK(user_role IN ('student', 'teacher')),
    name TEXT NOT NULL,
    date TEXT NOT NULL,         -- YYYY-MM-DD
    time TEXT NOT NULL,         -- HH:MM:SS
    status TEXT NOT NULL DEFAULT 'Present',
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_attendance_per_day UNIQUE (user_role, user_id, date)
);

-- Indexes for lightning-fast lookups
CREATE INDEX IF NOT EXISTS idx_students_lookup 
    ON students (class_name, section, roll_number);

CREATE INDEX IF NOT EXISTS idx_teachers_uid 
    ON teachers (teacher_uid);

CREATE INDEX IF NOT EXISTS idx_attendance_date 
    ON attendance (date);

CREATE INDEX IF NOT EXISTS idx_attendance_user 
    ON attendance (user_role, user_id, date);
