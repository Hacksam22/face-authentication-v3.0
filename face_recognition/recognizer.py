"""
Face Recognizer Module using OpenCV Local Binary Patterns Histograms (LBPH).
Handles multi-sample training, model serialization/deserialization, label mapping,
and 1:1 biometric identity verification.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import cv2
import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class FaceRecognizerManager:
    """Manages LBPH model lifecycle, training, and 1:1 identity verification."""

    def __init__(self):
        self.model_path = Path(config.LBPH_MODEL_PATH)
        self.label_map_path = Path(config.USER_LABEL_MAP_PATH)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=config.LBPH_RADIUS,
            neighbors=config.LBPH_NEIGHBORS,
            grid_x=config.LBPH_GRID_X,
            grid_y=config.LBPH_GRID_Y,
            threshold=float(config.LBPH_CONFIDENCE_THRESHOLD * 1.5),
        )
        self.label_to_user: Dict[int, Dict[str, Any]] = {}
        self.user_to_label: Dict[str, int] = {}
        self.is_trained = False
        self.load_model()

    def _user_key(self, role: str, user_id: int) -> str:
        """Create composite key for role and ID."""
        return f"{role.lower()}_{user_id}"

    def load_model(self) -> bool:
        """Load trained LBPH XML model and JSON label mapping from disk."""
        if not self.model_path.exists() or not self.label_map_path.exists():
            self.is_trained = False
            return False

        try:
            self.recognizer.read(str(self.model_path))
            with open(self.label_map_path, "r", encoding="utf-8") as f:
                raw_map = json.load(f)
                self.label_to_user = {int(k): v for k, v in raw_map.items()}
                self.user_to_label = {
                    self._user_key(v["role"], v["id"]): int(k)
                    for k, v in raw_map.items()
                }
            self.is_trained = True
            logger.info(
                f"LBPH model loaded successfully with {len(self.label_to_user)} enrolled identities."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load LBPH face model: {e}", exc_info=True)
            self.is_trained = False
            return False

    def train_from_database(self, db_manager) -> Tuple[bool, str]:
        """
        Extract all registered face samples from database, train LBPH model,
        and persist both model XML and label mapping.
        """
        enrolled_users = db_manager.get_all_registered_face_users()
        if not enrolled_users:
            return False, "No face samples enrolled in the system."

        images: List[np.ndarray] = []
        labels: List[int] = []

        label_to_user: Dict[int, Dict[str, Any]] = {}
        user_to_label: Dict[str, int] = {}

        current_label = 1
        total_samples = 0

        for user in enrolled_users:
            role = user["user_role"]
            uid = user["user_id"]
            user_key = self._user_key(role, uid)

            sample_paths = db_manager.get_face_samples_for_user(role, uid)
            if not sample_paths:
                continue

            user_images: List[np.ndarray] = []
            for path_str in sample_paths:
                p = Path(path_str)
                if p.exists():
                    img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        # Ensure target size
                        if img.shape[:2] != config.FACE_TARGET_SIZE:
                            img = cv2.resize(img, config.FACE_TARGET_SIZE)
                        user_images.append(img)

            if len(user_images) < 3:
                logger.warning(
                    f"Skipping {user_key}: insufficient valid face samples ({len(user_images)} found)."
                )
                continue

            # Assign integer label
            label_to_user[current_label] = {"role": role, "id": uid}
            user_to_label[user_key] = current_label

            for img in user_images:
                images.append(img)
                labels.append(current_label)
                total_samples += 1

            current_label += 1

        if not images:
            return False, "No valid face sample images found on disk to train."

        try:
            logger.info(
                f"Training LBPH recognizer with {total_samples} samples across {len(label_to_user)} identities..."
            )
            # Fresh recognizer instance
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                radius=config.LBPH_RADIUS,
                neighbors=config.LBPH_NEIGHBORS,
                grid_x=config.LBPH_GRID_X,
                grid_y=config.LBPH_GRID_Y,
            )
            self.recognizer.train(images, np.array(labels, dtype=np.int32))

            # Persist model and mapping
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self.recognizer.write(str(self.model_path))

            with open(self.label_map_path, "w", encoding="utf-8") as f:
                json.dump(label_to_user, f, indent=2)

            self.label_to_user = label_to_user
            self.user_to_label = user_to_label
            self.is_trained = True

            msg = f"Model trained successfully! ({total_samples} samples, {len(label_to_user)} users)"
            logger.info(msg)
            return True, msg
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return False, f"Model training error: {e}"

    def verify_user_face(
        self,
        face_crop: np.ndarray,
        target_role: str,
        target_user_id: int,
    ) -> Tuple[bool, float, str]:
        """
        Perform 1:1 face verification of the provided face crop against the specified target identity.
        Returns (is_match, distance_metric, message).
        """
        if not self.is_trained:
            # Try reloading once in case another process trained the model
            if not self.load_model():
                return False, 999.0, "Face recognition model is not trained yet."

        user_key = self._user_key(target_role, target_user_id)
        if user_key not in self.user_to_label:
            return False, 999.0, f"No registered biometric profile found for {target_role} ID: {target_user_id}."

        expected_label = self.user_to_label[user_key]

        # Ensure single-channel grayscale 200x200
        if len(face_crop.shape) == 3:
            face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        if face_crop.shape[:2] != config.FACE_TARGET_SIZE:
            face_crop = cv2.resize(face_crop, config.FACE_TARGET_SIZE)

        try:
            predicted_label, distance = self.recognizer.predict(face_crop)
            logger.debug(
                f"LBPH predict: expected={expected_label}, got={predicted_label}, distance={distance:.2f}"
            )

            # Verification rule:
            # 1. Predicted label matches candidate's enrolled label
            # 2. Distance metric <= LBPH_CONFIDENCE_THRESHOLD
            if predicted_label == expected_label and distance <= config.LBPH_CONFIDENCE_THRESHOLD:
                return True, float(distance), "Identity Verified"
            else:
                return False, float(distance), "Face not recognized. Please try again."
        except Exception as e:
            logger.error(f"Face verification prediction exception: {e}", exc_info=True)
            return False, 999.0, "Biometric evaluation error."

    def find_duplicate(self, face_crop: np.ndarray) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """
        Check whether the provided face_crop matches any enrolled identity strongly enough
        to be considered a duplicate registration.

        Returns (is_duplicate, user_ref, distance). user_ref is the matched label_to_user entry.
        """
        if not self.is_trained:
            if not self.load_model():
                return False, None, 999.0

        if not self.label_to_user:
            return False, None, 999.0

        # Ensure grayscale and target size
        if len(face_crop.shape) == 3:
            face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        if face_crop.shape[:2] != config.FACE_TARGET_SIZE:
            face_crop = cv2.resize(face_crop, config.FACE_TARGET_SIZE)

        try:
            predicted_label, distance = self.recognizer.predict(face_crop)
            logger.debug(f"Duplicate check LBPH predict: label={predicted_label}, distance={distance:.2f}")

            # Use a stricter threshold for duplicate detection. If distance <= DUPLICATE_FACE_THRESHOLD,
            # we consider the face already enrolled.
            if distance <= config.DUPLICATE_FACE_THRESHOLD:
                user_ref = self.label_to_user.get(predicted_label)
                return True, user_ref, float(distance)
            return False, None, float(distance)
        except Exception as e:
            logger.error(f"Duplicate detection exception: {e}", exc_info=True)
            return False, None, 999.0

    def identify_face(
        self,
        face_crop: np.ndarray,
        role_filter: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """
        Perform 1:N face identification of the provided face crop against all enrolled identities.
        Returns (is_recognized, user_ref, distance).
        user_ref contains {"role": str, "id": int}.
        """
        if not self.is_trained:
            if not self.load_model():
                return False, None, 999.0

        if not self.label_to_user:
            return False, None, 999.0

        # Ensure single-channel grayscale 200x200
        if len(face_crop.shape) == 3:
            face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        if face_crop.shape[:2] != config.FACE_TARGET_SIZE:
            face_crop = cv2.resize(face_crop, config.FACE_TARGET_SIZE)

        try:
            predicted_label, distance = self.recognizer.predict(face_crop)
            logger.debug(
                f"1:N LBPH identify: label={predicted_label}, distance={distance:.2f}"
            )

            if distance <= config.LBPH_CONFIDENCE_THRESHOLD:
                user_ref = self.label_to_user.get(predicted_label)
                if user_ref:
                    # Role filtering if requested
                    if role_filter and role_filter.lower() not in ("all", ""):
                        if user_ref["role"].lower() != role_filter.lower():
                            return False, None, float(distance)
                    return True, user_ref, float(distance)

            return False, None, float(distance)
        except Exception as e:
            logger.error(f"1:N face identification exception: {e}", exc_info=True)
            return False, None, 999.0
