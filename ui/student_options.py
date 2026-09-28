"""Shared class and section choices for student registration and attendance."""

STUDENT_CLASSES = (
    "Nursery", "LKG", "UKG", "I", "II", "III", "IV", "V", "VI", "VII",
    "VIII", "IX", "X", "XI", "XII",
)

STUDENT_SECTIONS = {
    **{class_name: ("A", "B", "C") for class_name in STUDENT_CLASSES[:11]},
    "IX": ("Commerce", "Science"),
    "X": ("Commerce", "Science"),
    "XI": ("Home Science", "Commerce", "Bio Science", "Computer Science"),
    "XII": ("Home Science", "Commerce", "Bio Science", "Computer Science"),
}
