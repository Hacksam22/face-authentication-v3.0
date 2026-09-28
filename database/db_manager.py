"""
Database Manager Module for School Attendance System.
Handles SQLite schema initialization, parameterized queries, transactional operations,
and robust data retrieval for students, teachers, face samples, and attendance records.
"""

import sqlite3
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Encapsulates SQLite database operations with parameterized queries."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_tables()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def initialize_tables(self) -> None:
        """Execute schema.sql to ensure all required tables and indexes exist."""
        schema_path = config.BASE_DIR / "database" / "schema.sql"
        if not schema_path.exists():
            logger.error(f"Schema file not found at: {schema_path}")
            raise FileNotFoundError(f"Missing schema: {schema_path}")

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}", exc_info=True)
            raise

    # ---------------------------------------------------------
    # Student Operations
    # ---------------------------------------------------------
    def register_student(
        self, name: str, class_name: str, section: str, roll_number: str
    ) -> int:
        """
        Register a new student.
        Prevents duplicate registration by checking unique (class_name, section, roll_number).
        """
        name = name.strip()
        class_name = class_name.strip()
        section = section.strip().upper()
        roll_number = roll_number.strip()

        if not all([name, class_name, section, roll_number]):
            raise ValueError("All student registration fields must be non-empty.")

        query = """
            INSERT INTO students (name, class_name, section, roll_number)
            VALUES (?, ?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, class_name, section, roll_number))
                conn.commit()
                student_id = cursor.lastrowid
                logger.info(
                    f"Registered student: {name} (ID: {student_id}, Class: {class_name}-{section}, Roll: {roll_number})"
                )
                return student_id
        except sqlite3.IntegrityError as e:
            logger.warning(
                f"Student duplicate detected: Class {class_name}, Sec {section}, Roll {roll_number}"
            )
            raise ValueError(
                f"Student with Class '{class_name}', Section '{section}', and Roll Number '{roll_number}' is already registered."
            ) from e

    def verify_student_credentials(
        self, name: str, class_name: str, section: str, roll_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify student credentials.
        Text fields (name, class_name, section) are matched case-insensitively,
        while roll_number is matched exactly.
        """
        name = name.strip().lower()
        class_name = class_name.strip().lower()
        section = section.strip().lower()
        roll_number = roll_number.strip()

        query = """
            SELECT id, name, class_name, section, roll_number, created_at
            FROM students
            WHERE LOWER(TRIM(name)) = ?
              AND LOWER(TRIM(class_name)) = ?
              AND LOWER(TRIM(section)) = ?
              AND TRIM(roll_number) = ?
            LIMIT 1;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, class_name, section, roll_number))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_student_by_class_section_roll(
        self, class_name: str, section: str, roll_number: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a registered student using the unique class/section/roll tuple."""
        query = """
            SELECT id, name, class_name, section, roll_number, created_at
            FROM students
            WHERE LOWER(TRIM(class_name)) = LOWER(TRIM(?))
              AND LOWER(TRIM(section)) = LOWER(TRIM(?))
              AND TRIM(roll_number) = TRIM(?)
            LIMIT 1;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (class_name, section, roll_number))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Fetch student record by primary key."""
        query = "SELECT * FROM students WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Return list of all registered students."""
        query = "SELECT * FROM students ORDER BY class_name, section, roll_number ASC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    # ---------------------------------------------------------
    # Teacher Operations
    # ---------------------------------------------------------
    def register_teacher(self, name: str, subject: str, teacher_uid: str) -> int:
        """
        Register a new teacher.
        Teacher UID must be unique.
        """
        name = name.strip()
        subject = subject.strip()
        teacher_uid = teacher_uid.strip()

        if not all([name, subject, teacher_uid]):
            raise ValueError("All teacher registration fields must be non-empty.")

        query = """
            INSERT INTO teachers (name, subject, teacher_uid)
            VALUES (?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, subject, teacher_uid))
                conn.commit()
                teacher_id = cursor.lastrowid
                logger.info(
                    f"Registered teacher: {name} (ID: {teacher_id}, Subject: {subject}, UID: {teacher_uid})"
                )
                return teacher_id
        except sqlite3.IntegrityError as e:
            logger.warning(f"Teacher UID duplicate detected: {teacher_uid}")
            raise ValueError(
                f"Teacher UID '{teacher_uid}' is already registered."
            ) from e

    def verify_teacher_credentials(
        self, name: str, subject: str, teacher_uid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify teacher credentials.
        Name and subject are case-insensitive, while teacher_uid is matched exactly.
        """
        name = name.strip().lower()
        subject = subject.strip().lower()
        teacher_uid = teacher_uid.strip()

        query = """
            SELECT id, name, subject, teacher_uid, created_at
            FROM teachers
            WHERE LOWER(TRIM(name)) = ?
              AND LOWER(TRIM(subject)) = ?
              AND TRIM(teacher_uid) = ?
            LIMIT 1;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, subject, teacher_uid))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_teacher_by_id(self, teacher_id: int) -> Optional[Dict[str, Any]]:
        """Fetch teacher record by primary key."""
        query = "SELECT * FROM teachers WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (teacher_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """Return list of all registered teachers."""
        query = "SELECT * FROM teachers ORDER BY name ASC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_user_by_role_and_id(
        self, user_role: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch user record by role ('student' or 'teacher') and ID."""
        if str(user_role).lower() == "student":
            return self.get_student_by_id(user_id)
        elif str(user_role).lower() == "teacher":
            return self.get_teacher_by_id(user_id)
        return None

    # ---------------------------------------------------------
    # Face Data Operations
    # ---------------------------------------------------------
    def save_face_samples(
        self, user_role: str, user_id: int, sample_paths: List[str]
    ) -> None:
        """Record face sample file paths for a user in SQLite."""
        if user_role not in ("student", "teacher"):
            raise ValueError("Invalid user_role. Must be 'student' or 'teacher'.")

        delete_query = "DELETE FROM face_samples WHERE user_role = ? AND user_id = ?;"
        insert_query = """
            INSERT INTO face_samples (user_role, user_id, sample_path, sample_index)
            VALUES (?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_query, (user_role, user_id))
            for idx, path in enumerate(sample_paths):
                cursor.execute(insert_query, (user_role, user_id, path, idx + 1))
            conn.commit()
            logger.info(
                f"Saved {len(sample_paths)} face sample records for {user_role} ID: {user_id}"
            )

    def get_face_samples_for_user(
        self, user_role: str, user_id: int
    ) -> List[str]:
        """Fetch all stored face sample file paths for a given user."""
        query = """
            SELECT sample_path FROM face_samples
            WHERE user_role = ? AND user_id = ?
            ORDER BY sample_index ASC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_role, user_id))
            return [row["sample_path"] for row in cursor.fetchall()]

    def get_all_registered_face_users(self) -> List[Dict[str, Any]]:
        """Fetch all distinct registered users who have face samples."""
        query = """
            SELECT DISTINCT user_role, user_id FROM face_samples
            ORDER BY user_role, user_id ASC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    # ---------------------------------------------------------
    # Attendance Operations
    # ---------------------------------------------------------
    def is_attendance_marked_today(
        self, user_role: str, user_id: int, date_str: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if user has already marked attendance on the given date."""
        target_date = date_str or datetime.date.today().isoformat()
        query = """
            SELECT * FROM attendance
            WHERE user_role = ? AND user_id = ? AND date = ?
            LIMIT 1;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_role, user_id, target_date))
            row = cursor.fetchone()
            if row:
                return True, dict(row)
            return False, None

    def mark_attendance(
        self,
        user_id: int,
        user_role: str,
        name: str,
        confidence: Optional[float] = None,
        date_str: Optional[str] = None,
        time_str: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Mark attendance for a verified student or teacher.
        Enforces duplicate prevention unless ALLOW_DUPLICATE_ATTENDANCE_SAME_DAY is True.
        """
        today_date = date_str or datetime.date.today().isoformat()
        current_time = time_str or datetime.datetime.now().strftime("%H:%M:%S")

        already_marked, existing_record = self.is_attendance_marked_today(
            user_role, user_id, today_date
        )

        if already_marked and not config.ALLOW_DUPLICATE_ATTENDANCE_SAME_DAY:
            time_recorded = existing_record.get("time", "earlier today") if existing_record else "earlier"
            msg = f"Attendance already marked for today at {time_recorded}."
            logger.warning(f"Duplicate attendance rejected for {user_role} {user_id}: {msg}")
            return False, msg, existing_record

        insert_query = """
            INSERT INTO attendance (user_id, user_role, name, date, time, status, confidence)
            VALUES (?, ?, ?, ?, ?, 'Present', ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_query,
                    (user_id, user_role, name, today_date, current_time, confidence),
                )
                conn.commit()
                new_id = cursor.lastrowid
                logger.info(
                    f"Attendance recorded: ID {new_id}, {user_role} '{name}' ({user_id}) on {today_date} at {current_time}"
                )
                return True, "Attendance marked successfully!", {
                    "id": new_id,
                    "user_id": user_id,
                    "user_role": user_role,
                    "name": name,
                    "date": today_date,
                    "time": current_time,
                    "status": "Present",
                    "confidence": confidence,
                }
        except sqlite3.IntegrityError:
            return False, "Attendance record conflict detected for today.", None

    def get_attendance_records(
        self,
        role: Optional[str] = None,
        date_str: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Fetch attendance records with optional filtering."""
        sql = "SELECT * FROM attendance WHERE 1=1"
        params: List[Any] = []

        if role:
            sql += " AND user_role = ?"
            params.append(role.lower())

        if date_str:
            sql += " AND date = ?"
            params.append(date_str)

        if search_query:
            sql += " AND LOWER(name) LIKE ?"
            params.append(f"%{search_query.lower()}%")

        sql += " ORDER BY date DESC, time DESC LIMIT ?;"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_system_summary(self) -> Dict[str, Any]:
        """Return system statistics for admin dashboard."""
        today = datetime.date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM students;")
            total_students = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM teachers;")
            total_teachers = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM attendance WHERE date = ?;", (today,))
            today_attendance = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(DISTINCT user_role || '_' || user_id) AS count FROM face_samples;")
            biometric_enrolled = cursor.fetchone()["count"]

            return {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "today_attendance": today_attendance,
                "biometric_enrolled": biometric_enrolled,
                "today_date": today,
            }

    def delete_student(self, student_id: int) -> Tuple[bool, str]:
        """
        Delete a student and all related data (face_samples, attendance records).
        This operation is performed inside a transaction. Face sample image files
        referenced by `face_samples.sample_path` will be deleted from disk when present.

        Returns (success, message).
        """
        # Validate student exists
        student = self.get_student_by_id(student_id)
        if not student:
            return False, f"Student id {student_id} does not exist."

        # Collect sample paths to remove files after DB deletion
        sample_paths = self.get_face_samples_for_user("student", student_id)

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                # Delete attendance rows
                cur.execute("DELETE FROM attendance WHERE user_role = ? AND user_id = ?;", ("student", student_id))
                # Delete face_samples rows
                cur.execute("DELETE FROM face_samples WHERE user_role = ? AND user_id = ?;", ("student", student_id))
                # Delete student row
                cur.execute("DELETE FROM students WHERE id = ?;", (student_id,))
                conn.commit()

            # Remove sample image files from disk (best-effort)
            removed_files = 0
            for p in sample_paths:
                try:
                    fp = Path(p)
                    if fp.exists():
                        fp.unlink()
                        removed_files += 1
                except Exception:
                    logger.warning(f"Failed to remove face sample file: {p}")

            logger.info(f"Deleted student {student_id} and removed {removed_files} face sample files.")
            return True, f"Deleted student {student_id}. Removed {removed_files} sample files."
        except Exception as e:
            logger.error(f"Failed to delete student {student_id}: {e}", exc_info=True)
            return False, f"Error deleting student: {e}"

    def delete_teacher(self, teacher_id: int) -> Tuple[bool, str]:
        """
        Delete a teacher and all related data (face_samples, attendance records).
        Performs best-effort cleanup of face sample files on disk.
        Returns (success, message).
        """
        teacher = self.get_teacher_by_id(teacher_id)
        if not teacher:
            return False, f"Teacher id {teacher_id} does not exist."

        sample_paths = self.get_face_samples_for_user("teacher", teacher_id)

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM attendance WHERE user_role = ? AND user_id = ?;", ("teacher", teacher_id))
                cur.execute("DELETE FROM face_samples WHERE user_role = ? AND user_id = ?;", ("teacher", teacher_id))
                cur.execute("DELETE FROM teachers WHERE id = ?;", (teacher_id,))
                conn.commit()

            removed_files = 0
            for p in sample_paths:
                try:
                    fp = Path(p)
                    if fp.exists():
                        fp.unlink()
                        removed_files += 1
                except Exception:
                    logger.warning(f"Failed to remove face sample file: {p}")

            logger.info(f"Deleted teacher {teacher_id} and removed {removed_files} face sample files.")
            return True, f"Deleted teacher {teacher_id}. Removed {removed_files} sample files."
        except Exception as e:
            logger.error(f"Failed to delete teacher {teacher_id}: {e}", exc_info=True)
            return False, f"Error deleting teacher: {e}"
