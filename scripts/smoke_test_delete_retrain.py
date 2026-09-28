"""
Smoke test: register dummy student with synthetic face samples, train recognizer,
verify duplicate detection, delete student, retrain, verify duplicate no longer detected.

Run: python scripts/smoke_test_delete_retrain.py
"""
import os
import sys
from pathlib import Path
import numpy as np
import cv2

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from database.db_manager import DatabaseManager
from face_recognition.recognizer import FaceRecognizerManager

print("Starting smoke test: delete & retrain")

db = DatabaseManager()
rec = FaceRecognizerManager()

# 1. Create dummy student
name = "Smoke Test Student"
class_name = "10"
section = "A"
roll = "999"

# Clean up any existing with same roll if present
existing = db.verify_student_credentials(name, class_name, section, roll)
if existing:
    print("Found existing student; deleting first")
    db.delete_student(existing['id'])

student_id = db.register_student(name, class_name, section, roll)
print(f"Registered student id={student_id}")

# 2. Create 3 synthetic face images and save
faces_dir = Path(config.FACES_DIR)
faces_dir.mkdir(parents=True, exist_ok=True)
paths = []
for i in range(3):
    img = np.full((config.FACE_TARGET_SIZE[1], config.FACE_TARGET_SIZE[0]), 120 + i*10, dtype=np.uint8)
    # add a small circle pattern to vary
    cv2.circle(img, (50 + i*10, 60), 20, (200,), -1)
    fname = faces_dir / f"smoke_student_{student_id}_{i+1}.png"
    cv2.imwrite(str(fname), img)
    paths.append(str(fname))

# Save face_samples
db.save_face_samples('student', student_id, paths)
print(f"Saved {len(paths)} sample images for student {student_id}")

# 3. Train recognizer
succ, msg = rec.train_from_database(db)
print('Train:', succ, msg)

# 4. Test duplicate detection using one of the saved images
test_img = cv2.imread(paths[0], cv2.IMREAD_GRAYSCALE)
if test_img is None:
    print('Failed to load test image')
    sys.exit(1)

is_dup, user_ref, dist = rec.find_duplicate(test_img)
print('Duplicate detection before delete ->', is_dup, user_ref, dist)

# 5. Delete the student
succ, msg = db.delete_student(student_id)
print('Delete student:', succ, msg)

# 6. Retrain recognizer
succ2, msg2 = rec.train_from_database(db)
print('Retrain after delete:', succ2, msg2)

# 7. Test duplicate detection again
is_dup2, user_ref2, dist2 = rec.find_duplicate(test_img)
print('Duplicate detection after delete ->', is_dup2, user_ref2, dist2)

print('Smoke test completed')
