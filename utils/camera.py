"""
Camera Management Module.
Provides robust webcam acquisition with automatic fallback to a dynamic
virtual test camera when hardware video input devices are unavailable.
"""

import time
import math
import hashlib
import cv2
import numpy as np
from typing import Tuple, Optional

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class CameraManager:
    """Encapsulates video frame acquisition with graceful hardware fallback."""

    def __init__(self, camera_index: int = config.DEFAULT_CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_mock = False
        self._sim_frame_count = 0
        self._current_subject_seed = "default_user"

    def set_subject_seed(self, seed: str) -> None:
        """Sets a unique seed for the virtual camera to generate distinct faces per user."""
        self._current_subject_seed = seed

    def start(self, camera_index: Optional[int] = None) -> bool:
        """Initialize and open the camera device or fallback simulator."""
        if camera_index is not None:
            self.camera_index = camera_index

        self.release()

        # Attempt to open physical webcam device across candidate indices
        candidate_indices = [self.camera_index]
        if 0 not in candidate_indices:
            candidate_indices.append(0)
        if 1 not in candidate_indices:
            candidate_indices.append(1)

        for idx in candidate_indices:
            try:
                logger.info(f"Attempting to open physical camera at index {idx}...")
                cap = cv2.VideoCapture(idx)
                if cap and cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_FRAME_HEIGHT)
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        self.cap = cap
                        self.camera_index = idx
                        self.is_running = True
                        self.is_mock = False
                        logger.info(
                            f"Physical camera (index {idx}) opened and verified successfully. Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}"
                        )
                        return True
                    else:
                        logger.warning(f"Camera index {idx} opened but returned no frame.")
                        cap.release()
            except Exception as e:
                logger.warning(f"Error accessing physical camera at index {idx}: {e}")

        # If physical camera failed, check if mock fallback is permitted
        if config.MOCK_CAMERA_IF_UNAVAILABLE:
            logger.info("Starting virtual webcam simulator (no physical camera attached).")
            self.is_mock = True
            self.is_running = True
            self._sim_frame_count = 0
            return True

        self.is_running = False
        self.is_mock = False
        logger.error("No camera available and mock camera is disabled.")
        return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Fetch the next video frame from either hardware or simulator."""
        if not self.is_running:
            return False, None

        if not self.is_mock and self.cap:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Optionally mirror horizontally for natural webcam feel
                frame = cv2.flip(frame, 1)
                return True, frame
            else:
                logger.warning("Physical camera frame drop.")
                return False, None

        # Virtual Webcam Simulator
        frame = self._generate_simulated_frame()
        return True, frame

    def _generate_simulated_frame(self) -> np.ndarray:
        """
        Generates a synthetic camera frame with realistic lighting and face features
        that OpenCV Haar Cascade detects and LBPH can learn.
        """
        self._sim_frame_count += 1
        h, w = config.CAMERA_FRAME_HEIGHT, config.CAMERA_FRAME_WIDTH

        # Background gradient (modern room/classroom wall)
        frame = np.full((h, w, 3), 35, dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (w, int(h * 0.7)), (45, 52, 60), -1)

        # Ambient lighting drift
        t = self._sim_frame_count * 0.05
        micro_dx = int(12 * math.sin(t * 0.7))
        micro_dy = int(8 * math.cos(t * 0.5))

        # Derive subject facial attributes deterministically from subject seed
        hash_val = int(hashlib.md5(self._current_subject_seed.encode()).hexdigest()[:6], 16)
        skin_tone_b = 150 + (hash_val % 40)
        skin_tone_g = 175 + ((hash_val >> 4) % 35)
        skin_tone_r = 205 + ((hash_val >> 8) % 35)
        skin_color = (skin_tone_b, skin_tone_g, skin_tone_r)

        center_x = (w // 2) + micro_dx
        center_y = (h // 2) + micro_dy - 10

        # Shoulders & Clothing
        cv2.ellipse(
            frame,
            (center_x, center_y + 240),
            (190, 130),
            0,
            0,
            360,
            (60 + (hash_val % 50), 40, 30),
            -1,
        )

        # Neck
        cv2.rectangle(
            frame,
            (center_x - 35, center_y + 80),
            (center_x + 35, center_y + 140),
            (skin_tone_b - 20, skin_tone_g - 20, skin_tone_r - 20),
            -1,
        )

        # Head / Face Oval
        cv2.ellipse(
            frame,
            (center_x, center_y),
            (88, 120),
            0,
            0,
            360,
            skin_color,
            -1,
        )

        # Hair
        cv2.ellipse(
            frame,
            (center_x, center_y - 65),
            (92, 65),
            0,
            180,
            360,
            (25, 20, 20),
            -1,
        )

        # Eyes & Eyebrows
        eye_y = center_y - 20
        # Left eye
        cv2.circle(frame, (center_x - 38, eye_y), 15, (230, 230, 230), -1)
        cv2.circle(frame, (center_x - 38, eye_y), 7, (40, 30, 20), -1)
        cv2.circle(frame, (center_x - 36, eye_y - 2), 2, (255, 255, 255), -1)
        cv2.line(
            frame,
            (center_x - 55, eye_y - 18),
            (center_x - 20, eye_y - 15),
            (30, 25, 25),
            4,
        )

        # Right eye
        cv2.circle(frame, (center_x + 38, eye_y), 15, (230, 230, 230), -1)
        cv2.circle(frame, (center_x + 38, eye_y), 7, (40, 30, 20), -1)
        cv2.circle(frame, (center_x + 40, eye_y - 2), 2, (255, 255, 255), -1)
        cv2.line(
            frame,
            (center_x + 20, eye_y - 15),
            (center_x + 55, eye_y - 18),
            (30, 25, 25),
            4,
        )

        # Nose bridge and nostrils
        nose_y = center_y + 15
        cv2.line(
            frame,
            (center_x, eye_y + 10),
            (center_x, nose_y + 12),
            (skin_tone_b - 35, skin_tone_g - 35, skin_tone_r - 35),
            3,
        )
        cv2.circle(
            frame,
            (center_x - 8, nose_y + 12),
            3,
            (skin_tone_b - 45, skin_tone_g - 45, skin_tone_r - 45),
            -1,
        )
        cv2.circle(
            frame,
            (center_x + 8, nose_y + 12),
            3,
            (skin_tone_b - 45, skin_tone_g - 45, skin_tone_r - 45),
            -1,
        )

        # Mouth / Smile
        mouth_y = center_y + 55
        cv2.ellipse(
            frame,
            (center_x, mouth_y),
            (32, 14),
            0,
            0,
            180,
            (60, 50, 160),
            -1,
        )
        cv2.line(
            frame,
            (center_x - 30, mouth_y),
            (center_x + 30, mouth_y),
            (40, 30, 130),
            2,
        )

        # Small watermark indicator when using virtual simulator
        cv2.putText(
            frame,
            "CAMERA SIMULATOR ACTIVE",
            (16, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 229, 255),
            1,
            cv2.LINE_AA,
        )

        return frame

    def release(self) -> None:
        """Release camera hardware resources."""
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            finally:
                self.cap = None

    def __del__(self):
        self.release()
