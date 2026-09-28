"""
Futuristic Holographic HUD Visualizer.
Renders cyberpunk / holographic heads-up display overlays, glowing sci-fi bounding boxes,
reticles, targeting brackets, and attendance verification badges directly onto OpenCV video frames.
"""

from typing import Tuple, Optional, Dict, Any, List
import cv2
import numpy as np

# BGR Color Constants
BGR_CYAN = (255, 229, 0)       # Holographic Cyan
BGR_GREEN = (118, 230, 0)      # Neon Emerald Green
BGR_RED = (82, 82, 255)        # Alert Red
BGR_AMBER = (0, 171, 255)      # Amber Warning
BGR_WHITE = (248, 250, 252)    # Pure Text White
BGR_DARK_HUD = (20, 25, 35)    # Translucent HUD Slate


class HolographicVisualizer:
    """Renders sleek futuristic HUD interfaces directly onto video stream frames."""

    @staticmethod
    def draw_hud_brackets(
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        color: Tuple[int, int, int] = BGR_CYAN,
        thickness: int = 2,
        bracket_length: int = 24,
    ) -> None:
        """Draw futuristic corner brackets around the face bounding box."""
        x, y, w, h = bbox
        bl = min(bracket_length, w // 3, h // 3)

        # Thin outer box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1, cv2.LINE_AA)

        # Thick Corner Brackets: [  ]
        # Top-Left
        cv2.line(frame, (x, y), (x + bl, y), color, thickness + 1, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + bl), color, thickness + 1, cv2.LINE_AA)

        # Top-Right
        cv2.line(frame, (x + w, y), (x + w - bl, y), color, thickness + 1, cv2.LINE_AA)
        cv2.line(frame, (x + w, y), (x + w, y + bl), color, thickness + 1, cv2.LINE_AA)

        # Bottom-Left
        cv2.line(frame, (x, y + h), (x + bl, y + h), color, thickness + 1, cv2.LINE_AA)
        cv2.line(frame, (x, y + h), (x, y + h - bl), color, thickness + 1, cv2.LINE_AA)

        # Bottom-Right
        cv2.line(frame, (x + w, y + h), (x + w - bl, y + h), color, thickness + 1, cv2.LINE_AA)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - bl), color, thickness + 1, cv2.LINE_AA)

        # Small targeting center crosshair ticks
        cx, cy = x + w // 2, y + h // 2
        tick_len = 6
        cv2.line(frame, (cx - tick_len, cy), (cx + tick_len, cy), color, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy - tick_len), (cx, cy + tick_len), color, 1, cv2.LINE_AA)

    @classmethod
    def draw_scanning_hud(
        cls,
        frame: np.ndarray,
        bbox: Optional[Tuple[int, int, int, int]],
        status_text: str = "SCANNING BIOMETRICS...",
        is_error: bool = False,
    ) -> None:
        """Render active scanning HUD with cybernetic accents."""
        h, w = frame.shape[:2]
        color = BGR_RED if is_error else BGR_CYAN

        # Top HUD Status Bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 42), BGR_DARK_HUD, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Tech status text
        cv2.putText(
            frame,
            f"[SYS:ONLINE]  {status_text}",
            (16, 27),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

        if bbox is not None:
            cls.draw_hud_brackets(frame, bbox, color=color, thickness=2)

    @classmethod
    def draw_registration_guide(
        cls,
        frame: np.ndarray,
        sample_count: int,
        target_samples: int,
        guidance_text: str,
        detected_bbox: Optional[Tuple[int, int, int, int]],
    ) -> None:
        """Renders guidance overlay, target reticle, and capture progress during enrollment."""
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2

        # Draw target guide oval in center
        guide_color = BGR_GREEN if detected_bbox is not None else BGR_AMBER
        cv2.ellipse(frame, (center_x, center_y - 10), (105, 140), 0, 0, 360, guide_color, 2, cv2.LINE_AA)

        # Draw detected face brackets if in frame
        if detected_bbox is not None:
            cls.draw_hud_brackets(frame, detected_bbox, color=BGR_GREEN, thickness=2)

        # Bottom HUD overlay for guidance
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 75), (w, h), BGR_DARK_HUD, -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Progress bar
        bar_x = 20
        bar_y = h - 22
        bar_w = w - 40
        bar_h = 10
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 70, 80), -1)

        progress_pct = min(1.0, sample_count / max(1, target_samples))
        fill_w = int(bar_w * progress_pct)
        if fill_w > 0:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), BGR_CYAN, -1)

        # Guidance Text
        cv2.putText(
            frame,
            f"INSTRUCTION: {guidance_text.upper()}",
            (20, h - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            BGR_WHITE,
            2,
            cv2.LINE_AA,
        )

        # Sample counter
        counter_str = f"SAMPLES: {sample_count}/{target_samples}"
        cv2.putText(
            frame,
            counter_str,
            (w - 180, h - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            BGR_CYAN,
            2,
            cv2.LINE_AA,
        )

    @classmethod
    def draw_verified_hologram(
        cls,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        user_info: Dict[str, Any],
        user_role: str,
    ) -> None:
        """
        Renders the holographic approved attendance card near/below the detected face.
        """
        frame_h, frame_w = frame.shape[:2]
        x, y, w, h = bbox

        # Draw glowing neon emerald HUD brackets on the verified face
        cls.draw_hud_brackets(frame, bbox, color=BGR_GREEN, thickness=3, bracket_length=32)

        # Prepare field lines based on role
        if user_role.lower() == "student":
            name = user_info.get("name", "Unknown")
            class_name = user_info.get("class_name", "")
            section = user_info.get("section", "")
            roll_no = user_info.get("roll_number", "")
            lines = [
                "[✓] ATTENDANCE VERIFIED",
                f"Name: {name}",
                f"Class: {class_name}",
                f"Section: {section}",
                f"Roll No: {roll_no}",
            ]
        else:
            name = user_info.get("name", "Unknown")
            subject = user_info.get("subject", "")
            uid = user_info.get("teacher_uid", "")
            lines = [
                "[✓] ATTENDANCE VERIFIED",
                f"Name: {name}",
                f"Subject: {subject}",
                f"UID: {uid}",
            ]

        # Calculate card dimensions
        card_w = max(290, w + 40)
        line_height = 24
        card_h = 32 + (len(lines) * line_height)

        # Position card below face if space permits; otherwise position to the right or above
        card_x = max(10, min(frame_w - card_w - 10, x - (card_w - w) // 2))
        if y + h + card_h + 10 < frame_h:
            card_y = y + h + 10
        elif y - card_h - 10 > 0:
            card_y = y - card_h - 10
        else:
            card_y = max(10, min(frame_h - card_h - 10, y))
            card_x = max(10, frame_w - card_w - 10)

        # Create semi-transparent holographic glass overlay
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (card_x, card_y),
            (card_x + card_w, card_y + card_h),
            BGR_DARK_HUD,
            -1,
        )
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Holographic neon border
        cv2.rectangle(
            frame,
            (card_x, card_y),
            (card_x + card_w, card_y + card_h),
            BGR_GREEN,
            2,
            cv2.LINE_AA,
        )

        # Top Accent Header Bar
        cv2.rectangle(
            frame,
            (card_x, card_y),
            (card_x + card_w, card_y + 30),
            (25, 45, 30),
            -1,
        )
        cv2.line(
            frame,
            (card_x, card_y + 30),
            (card_x + card_w, card_y + 30),
            BGR_GREEN,
            1,
            cv2.LINE_AA,
        )

        # Header Title: ✓ ATTENDANCE VERIFIED
        cv2.putText(
            frame,
            lines[0],
            (card_x + 12, card_y + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            BGR_GREEN,
            2,
            cv2.LINE_AA,
        )

        # Render field lines
        curr_y = card_y + 54
        for line in lines[1:]:
            cv2.putText(
                frame,
                line,
                (card_x + 16, curr_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                BGR_WHITE,
                1,
                cv2.LINE_AA,
            )
            curr_y += line_height

        # Holographic decorative corner notches
        notch = 8
        cv2.line(frame, (card_x, card_y + notch), (card_x + notch, card_y), BGR_CYAN, 2, cv2.LINE_AA)
        cv2.line(frame, (card_x + card_w - notch, card_y), (card_x + card_w, card_y + notch), BGR_CYAN, 2, cv2.LINE_AA)

    @classmethod
    def draw_hover_card(
        cls,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        user_info: Dict[str, Any],
        user_role: str,
        is_already_marked: bool = False,
    ) -> None:
        """
        Renders a floating holographic hover details card adjacent to the detected face.
        Shows Name, Roll, Class, Sec for students (or Name, UID, Subject for teachers).
        """
        frame_h, frame_w = frame.shape[:2]
        x, y, w, h = bbox

        theme_color = BGR_CYAN if is_already_marked else BGR_GREEN
        cls.draw_hud_brackets(frame, bbox, color=theme_color, thickness=2, bracket_length=24)

        # Build hover details
        if str(user_role).lower() == "student":
            name = user_info.get("name", "Unknown")
            roll_no = user_info.get("roll_number", "N/A")
            class_name = user_info.get("class_name", "N/A")
            section = user_info.get("section", "N/A")
            header_text = "[i] ALREADY RECORDED" if is_already_marked else "[✓] ATTENDANCE MARKED"
            lines = [
                header_text,
                f"Name : {name}",
                f"Roll : {roll_no}",
                f"Class: {class_name}",
                f"Sec  : {section}",
            ]
        else:
            name = user_info.get("name", "Unknown")
            uid = user_info.get("teacher_uid", "N/A")
            subject = user_info.get("subject", "N/A")
            header_text = "[i] ALREADY RECORDED" if is_already_marked else "[✓] ATTENDANCE MARKED"
            lines = [
                header_text,
                f"Name   : {name}",
                f"UID    : {uid}",
                f"Subject: {subject}",
            ]

        # Calculate card dimensions
        card_w = 230
        line_height = 22
        card_h = 28 + (len(lines) * line_height)

        # Positioning: Try placing to the right of the face first
        if x + w + card_w + 12 < frame_w:
            card_x = x + w + 12
            card_y = max(10, min(frame_h - card_h - 10, y))
            # Connecting leader line
            cv2.line(frame, (x + w, y + h // 3), (card_x, card_y + 15), theme_color, 1, cv2.LINE_AA)
            cv2.circle(frame, (x + w, y + h // 3), 3, theme_color, -1)
        elif x - card_w - 12 > 10:
            card_x = x - card_w - 12
            card_y = max(10, min(frame_h - card_h - 10, y))
            cv2.line(frame, (x, y + h // 3), (card_x + card_w, card_y + 15), theme_color, 1, cv2.LINE_AA)
            cv2.circle(frame, (x, y + h // 3), 3, theme_color, -1)
        elif y + h + card_h + 10 < frame_h:
            card_x = max(10, min(frame_w - card_w - 10, x))
            card_y = y + h + 10
            cv2.line(frame, (x + w // 2, y + h), (card_x + card_w // 2, card_y), theme_color, 1, cv2.LINE_AA)
        else:
            card_x = max(10, min(frame_w - card_w - 10, x))
            card_y = max(10, y - card_h - 10)

        # Semi-transparent HUD background
        overlay = frame.copy()
        cv2.rectangle(overlay, (card_x, card_y), (card_x + card_w, card_y + card_h), BGR_DARK_HUD, -1)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

        # Glowing border
        cv2.rectangle(frame, (card_x, card_y), (card_x + card_w, card_y + card_h), theme_color, 1, cv2.LINE_AA)

        # Header bar
        header_bg = (20, 45, 25) if not is_already_marked else (40, 40, 20)
        cv2.rectangle(frame, (card_x, card_y), (card_x + card_w, card_y + 26), header_bg, -1)
        cv2.line(frame, (card_x, card_y + 26), (card_x + card_w, card_y + 26), theme_color, 1, cv2.LINE_AA)

        cv2.putText(
            frame,
            lines[0],
            (card_x + 8, card_y + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            theme_color,
            2,
            cv2.LINE_AA,
        )

        curr_y = card_y + 44
        for line in lines[1:]:
            cv2.putText(
                frame,
                line,
                (card_x + 10, curr_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                BGR_WHITE,
                1,
                cv2.LINE_AA,
            )
            curr_y += line_height

        # Corner notches
        notch = 6
        cv2.line(frame, (card_x, card_y + notch), (card_x + notch, card_y), theme_color, 2, cv2.LINE_AA)
        cv2.line(frame, (card_x + card_w - notch, card_y), (card_x + card_w, card_y + notch), theme_color, 2, cv2.LINE_AA)

    @classmethod
    def draw_unrecognized_hover(
        cls,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        status_text: str = "FACE NOT RECOGNIZED",
    ) -> None:
        """Draw alert reticle and hover tag for unrecognized faces."""
        frame_h, frame_w = frame.shape[:2]
        x, y, w, h = bbox
        cls.draw_hud_brackets(frame, bbox, color=BGR_RED, thickness=2, bracket_length=20)

        tag_w = 210
        tag_h = 28
        tag_x = max(10, min(frame_w - tag_w - 10, x + (w - tag_w) // 2))
        tag_y = max(10, y - tag_h - 6) if y - tag_h - 6 > 0 else y + h + 6

        overlay = frame.copy()
        cv2.rectangle(overlay, (tag_x, tag_y), (tag_x + tag_w, tag_y + tag_h), (25, 20, 45), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        cv2.rectangle(frame, (tag_x, tag_y), (tag_x + tag_w, tag_y + tag_h), BGR_RED, 1, cv2.LINE_AA)

        cv2.putText(
            frame,
            f"[!] {status_text}",
            (tag_x + 8, tag_y + 19),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            BGR_RED,
            1,
            cv2.LINE_AA,
        )
