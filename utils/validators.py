"""Input validation and sanitization utilities."""

import re
from typing import Tuple

def clean_input(value: str) -> str:
    """Trim leading/trailing whitespace and normalize internal spaces."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip())

def validate_student_fields(
    name: str, class_name: str, section: str, roll_number: str
) -> Tuple[bool, str]:
    """Validate student registration and login input fields."""
    name = clean_input(name)
    class_name = clean_input(class_name)
    section = clean_input(section)
    roll_number = clean_input(roll_number)

    if not name:
        return False, "Student Name is required."
    if len(name) < 2:
        return False, "Student Name must be at least 2 characters."
    if not class_name:
        return False, "Class is required (e.g. 10, Grade 11)."
    if not section:
        return False, "Section is required (e.g. A, B, Green)."
    if not roll_number:
        return False, "Roll Number is required."
    return True, ""

def validate_teacher_fields(
    name: str, subject: str, teacher_uid: str
) -> Tuple[bool, str]:
    """Validate teacher registration and login input fields."""
    name = clean_input(name)
    subject = clean_input(subject)
    teacher_uid = clean_input(teacher_uid)

    if not name:
        return False, "Teacher Name is required."
    if len(name) < 2:
        return False, "Teacher Name must be at least 2 characters."
    if not subject:
        return False, "Main Subject is required."
    if not teacher_uid:
        return False, "Teacher UID is required."
    return True, ""
