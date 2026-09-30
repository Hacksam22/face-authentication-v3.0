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
        self.profile_cascade: Optional[cv2.CascadeClassifier] = None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self._load_cascade()

    def _load_cascade(self) -> None:
        """Load frontal and profile Haar Cascade XML classifiers."""
        frontal_candidates = (
            config.PRIMARY_CASCADE_PATH,
            config.FALLBACK_CASCADE_PATH,
            Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml",
        )
        for cascade_path in frontal_candidates:
            if not cascade_path.exists():
                continue
            cascade = cv2.CascadeClassifier(str(cascade_path))
            if not cascade.empty():
                self.cascade = cascade
                logger.info(f"Loaded frontal face cascade from {cascade_path.name}")
                break

        if self.cascade is None:
            logger.error("Unable to load any frontal Haar Cascade classifier XML file.")
            raise RuntimeError("Frontal Haar Cascade XML classifier could not be loaded.")

        profile_candidates = (
            config.PROFILE_CASCADE_PATH,
            Path(cv2.data.haarcascades) / "haarcascade_profileface.xml",
        )
        for cascade_path in profile_candidates:
            if not cascade_path.exists():
                continue
            cascade = cv2.CascadeClassifier(str(cascade_path))
            if not cascade.empty():
                self.profile_cascade = cascade
                logger.info(f"Loaded profile face cascade from {cascade_path.name}")
                break

        if self.profile_cascade is None:
            logger.warning("No profile-face cascade found; side-view detection is disabled.")

    def detect_faces(
        self,
        frame: np.ndarray,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = config.DETECTION_MIN_FACE_SIZE,
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

        def scan_orientations(
            image: np.ndarray,
            inverse_rotation=None,
            classifiers: Optional[List[cv2.CascadeClassifier]] = None,
        ) -> List[Tuple[int, int, int, int]]:
            detections: List[Tuple[int, int, int, int]] = []
            classifiers = classifiers or [self.cascade]
            image_size = max(image.shape[:2])
            search_scale = (
                min(config.DETECTION_SEARCH_SCALE, 1.0)
                if image_size > 320
                else 1.0
            )
            search_image = cv2.resize(
                image,
                None,
                fx=search_scale,
                fy=search_scale,
                interpolation=cv2.INTER_AREA,
            )
            search_min_size = tuple(
                max(8, round(value * search_scale)) for value in min_size
            )

            for classifier in classifiers:
                flips = (False, True) if classifier is self.profile_cascade else (False,)
                for flipped in flips:
                    scan_image = cv2.flip(search_image, 1) if flipped else search_image
                    found = classifier.detectMultiScale(
                        scan_image,
                        scaleFactor=scale_factor,
                        minNeighbors=min_neighbors,
                        minSize=search_min_size,
                        flags=cv2.CASCADE_SCALE_IMAGE,
                    )
                    for x, y, w, h in found:
                        if flipped:
                            x = search_image.shape[1] - x - w
                        x = int(round(x / search_scale))
                        y = int(round(y / search_scale))
                        w = int(round(w / search_scale))
                        h = int(round(h / search_scale))
                        if inverse_rotation is not None:
                            corners = np.array(
                                [[x, y, 1], [x + w, y, 1], [x, y + h, 1], [x + w, y + h, 1]],
                                dtype=np.float32,
                            )
                            mapped = corners @ inverse_rotation.T
                            x1 = max(0, int(np.floor(mapped[:, 0].min())))
                            y1 = max(0, int(np.floor(mapped[:, 1].min())))
                            x2 = min(gray.shape[1], int(np.ceil(mapped[:, 0].max())))
                            y2 = min(gray.shape[0], int(np.ceil(mapped[:, 1].max())))
                            x, y, w, h = x1, y1, x2 - x1, y2 - y1
                        if w > 0 and h > 0:
                            detections.append((int(x), int(y), int(w), int(h)))
            return detections

        faces = scan_orientations(equalized, classifiers=[self.cascade])
        if self.profile_cascade is not None:
            faces.extend(
                scan_orientations(equalized, classifiers=[self.profile_cascade])
            )
        if not faces:
            # Rotated scans are the fallback, keeping the common frontal path fast.
            height, width = equalized.shape[:2]
            center = (width / 2.0, height / 2.0)
            for angle in (-30, 30):
                matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                cosine = abs(matrix[0, 0])
                sine = abs(matrix[0, 1])
                rotated_width = int(height * sine + width * cosine)
                rotated_height = int(height * cosine + width * sine)
                matrix[0, 2] += rotated_width / 2.0 - center[0]
                matrix[1, 2] += rotated_height / 2.0 - center[1]
                rotated = cv2.warpAffine(
                    equalized,
                    matrix,
                    (rotated_width, rotated_height),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0,
                )
                inverse = cv2.invertAffineTransform(matrix)
                faces.extend(
                    scan_orientations(
                        rotated,
                        inverse,
                        classifiers=[self.cascade],
                    )
                )

        return self._suppress_overlaps(faces)

    @staticmethod
    def _suppress_overlaps(
        boxes: List[Tuple[int, int, int, int]], threshold: float = 0.4
    ) -> List[Tuple[int, int, int, int]]:
        """Collapse overlapping detections from frontal, profile, and rotated scans."""
        selected: List[Tuple[int, int, int, int]] = []
        for candidate in sorted(boxes, key=lambda box: box[2] * box[3], reverse=True):
            x, y, width, height = candidate
            candidate_area = width * height
            duplicate = False
            for other_x, other_y, other_width, other_height in selected:
                intersection_width = max(0, min(x + width, other_x + other_width) - max(x, other_x))
                intersection_height = max(0, min(y + height, other_y + other_height) - max(y, other_y))
                intersection = intersection_width * intersection_height
                union = candidate_area + other_width * other_height - intersection
                overlap = intersection / min(candidate_area, other_width * other_height)
                if (union and intersection / union >= threshold) or overlap >= 0.7:
                    duplicate = True
                    break
            if not duplicate:
                selected.append(candidate)
        return selected

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
