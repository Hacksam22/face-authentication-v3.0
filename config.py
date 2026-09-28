"""
Central Configuration Module for School Face Attendance System.
All paths, face recognition parameters, camera configurations, and UI constants
are defined here.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FACES_DIR = DATA_DIR / "faces"
MODELS_DIR = DATA_DIR / "models"
CASCADES_DIR = BASE_DIR / "face_recognition" / "cascades"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
FACES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
CASCADES_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "school_attendance.db"

# Haar Cascade Paths
PRIMARY_CASCADE_PATH = CASCADES_DIR / "haarcascade_frontalface_default.xml"
FALLBACK_CASCADE_PATH = CASCADES_DIR / "haarcascade_frontalface_alt2.xml"

# Model File Path
LBPH_MODEL_PATH = MODELS_DIR / "lbph_face_model.xml"
USER_LABEL_MAP_PATH = MODELS_DIR / "label_map.json"

# Face Recognition Parameters
LBPH_RADIUS = 1
LBPH_NEIGHBORS = 8
LBPH_GRID_X = 8
LBPH_GRID_Y = 8

# LBPH Confidence Threshold:
# In LBPH, confidence represents distance between histograms.
# 0 is exact match; smaller values mean higher similarity.
# Threshold of 65.0 - 75.0 provides high accuracy while accommodating natural variations.
LBPH_CONFIDENCE_THRESHOLD = 68.0

# Duplicate detection threshold for registration (LBPH distance):
# In LBPH lower distance means more similar. Use a stricter threshold for
# rejecting duplicate registrations than the general verification threshold.
# Adjust after empirical testing. Default: 50.0 (more conservative)
DUPLICATE_FACE_THRESHOLD = 40.0

# Face quality checks for registration pre-validation
# Minimum face width/height in pixels (before resizing)
MIN_FACE_WIDTH = 80
MIN_FACE_HEIGHT = 80

# Blur threshold: Laplacian variance below this value indicates blur
REGISTRATION_BLUR_THRESHOLD = 80.0

# Brightness thresholds (mean pixel value)
REGISTRATION_BRIGHTNESS_MIN = 50
REGISTRATION_BRIGHTNESS_MAX = 200

# Face normalization & preprocessing size
FACE_TARGET_SIZE = (200, 200)

# Recognition acceptance threshold (LBPH distance). Lower is more similar.
# Use a stricter value than LBPH_CONFIDENCE_THRESHOLD to reduce false positives
# especially in multi-face frames.
RECOGNITION_ACCEPT_THRESHOLD = 50.0

# Registration Sample Parameters
SAMPLES_PER_REGISTRATION = 25
SAMPLE_CAPTURE_DELAY_MS = 450  # milliseconds between captures to allow natural expression and angle changes

# Verification Stability
# Require multiple consecutive positive match frames before locking verification
CONSECUTIVE_MATCH_FRAMES_REQUIRED = 4

# Attendance Business Rules
ALLOW_DUPLICATE_ATTENDANCE_SAME_DAY = False

# Camera Settings
DEFAULT_CAMERA_INDEX = 0
CAMERA_FRAME_WIDTH = 640
CAMERA_FRAME_HEIGHT = 480
CAMERA_FPS = 30
MOCK_CAMERA_IF_UNAVAILABLE = True  # Use simulator when no physical camera is available

# UI Styling Constants (Modern Dark Cyber-Clean School Theme)
APP_TITLE = "ANMS ATTENDANCE | Authpur National Model Higher Secondary School"
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720

# Color Palette
COLOR_BG_DARK = "#0F172A"         # Slate 900
COLOR_CARD_DARK = "#1E293B"       # Slate 800
COLOR_CARD_HOVER = "#334155"      # Slate 700
COLOR_BORDER = "#334155"

COLOR_PRIMARY = "#0284C7"         # Sky Blue 600
COLOR_PRIMARY_HOVER = "#0369A1"   # Sky Blue 700
COLOR_SECONDARY = "#475569"       # Slate 600

COLOR_NEON_CYAN = "#00E5FF"       # Holographic Cyan
COLOR_NEON_GREEN = "#00E676"      # Success Emerald
COLOR_NEON_RED = "#FF5252"        # Alert Red
COLOR_NEON_AMBER = "#FFAB00"      # Warning Amber

COLOR_TEXT_PRIMARY = "#F8FAFC"    # Off-white
COLOR_TEXT_SECONDARY = "#94A3B8"  # Slate 400
COLOR_TEXT_MUTED = "#64748B"      # Slate 500
