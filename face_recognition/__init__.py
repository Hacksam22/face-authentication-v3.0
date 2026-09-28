"""Face recognition package for School Attendance Management System."""
from .detector import FaceDetector
from .recognizer import FaceRecognizerManager
from .visualizer import HolographicVisualizer

__all__ = [
    "FaceDetector",
    "FaceRecognizerManager",
    "HolographicVisualizer",
]
