"""
Face Detection and Normalization Module.
Loads Haar cascade classifiers with automatic fallback, extracts bounding boxes,
and applies Contrast Limited Adaptive Histogram Equalization (CLAHE) for illumination invariance.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class FaceDetector:
    """Robust OpenCV Haar-Cascade based face detector with lighting normalization."""

    def __init__(self):
        self.cascade: Optional[cv2.CascadeClassifier] = None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self._load_cascade()

    def _load_cascade(self) -> None:
        """Load the primary or fallback Haar Cascade XML classifier."""
        primary_path = config.PRIMARY_CASCADE_PATH
        fallback_path = config.FALLBACK_CASCADE_PATH

        if primary_path.exists():
            cascade = cv2.CascadeClassifier(str(primary_path))
            if not cascade.empty():
                self.cascade = cascade
                logger.info(f"Loaded primary face cascade from {primary_path.name}")
                return

        if fallback_path.exists():
            cascade = cv2.CascadeClassifier(str(fallback_path))
            if not cascade.empty():
                self.cascade = cascade
                logger.info(f"Loaded fallback face cascade from {fallback_path.name}")
                return

        # Attempt OpenCV internal data path
        internal_default = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if internal_default.exists():
            cascade = cv2.CascadeClassifier(str(internal_default))
            if not cascade.empty():
                self.cascade = cascade
                logger.info("Loaded face cascade from cv2.data internal directory.")
                return

        logger.error("Unable to load any Haar Cascade classifier XML file.")
        raise RuntimeError("Haar Cascade XML classifier could not be loaded.")

    def detect_faces(
        self,
        frame: np.ndarray,
        scale_factor: float = 1.15,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = (60, 60),
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in the given BGR or Grayscale frame.
        Returns list of (x, y, w, h) bounding boxes.
        """
        if self.cascade is None:
            return []

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Apply CLAHE to mitigate poor or uneven illumination
        equalized = self._clahe.apply(gray)

        faces = self.cascade.detectMultiScale(
            equalized,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        return [tuple(box) for box in faces]

    def extract_preprocessed_face(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """
        Crop face bounding box with slight margin, convert to grayscale,
        apply CLAHE normalization, and resize to standard config.FACE_TARGET_SIZE.
        """
        x, y, w, h = bbox
        img_h, img_w = frame.shape[:2]

        # Add 5% padding to capture chin and forehead
        pad_x = int(0.05 * w)
        pad_y = int(0.05 * h)

        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(img_w, x + w + pad_x)
        y2 = min(img_h, y + h + pad_y)

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0 or crop.shape[0] < 20 or crop.shape[1] < 20:
            return None

        # Convert to Grayscale
        if len(crop.shape) == 3:
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray_crop = crop

        # Standardize illumination via CLAHE
        normalized = self._clahe.apply(gray_crop)

        # Bilinear resize to standard dimension
        resized = cv2.resize(
            normalized, config.FACE_TARGET_SIZE, interpolation=cv2.INTER_AREA
        )

        return resized

    @staticmethod
    def get_largest_face(
        bboxes: List[Tuple[int, int, int, int]]
    ) -> Optional[Tuple[int, int, int, int]]:
        """Return the bounding box with the largest surface area (closest user)."""
        if not bboxes:
            return None
        return max(bboxes, key=lambda b: b[2] * b[3])
