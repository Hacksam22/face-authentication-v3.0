"""
Registration View.
Handles data collection and multi-sample biometric face capture for Students and Teachers.
Integrates live camera stream, face detection feedback, angle guidance, SQLite enrollment,
and LBPH model re-training.
"""

import time
from pathlib import Path
from typing import Callable, Optional, List
import cv2
import numpy as np
import customtkinter as ctk

import config
from utils.logger import get_logger
from utils.validators import validate_student_fields, validate_teacher_fields, clean_input
from ui.components import CardFrame, VideoCanvas, NotificationBanner
from ui.student_options import STUDENT_CLASSES, STUDENT_SECTIONS
from face_recognition.visualizer import HolographicVisualizer
import config

logger = get_logger(__name__)


class RegistrationView(ctk.CTkFrame):
    """Enrollment interface for Students and Teachers."""

    def __init__(
        self,
        master,
        role: str,
        db_manager,
        face_detector,
        face_recognizer,
        camera_manager,
        on_back: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.role = role.lower()  # "student" or "teacher"
        self.db = db_manager
        self.detector = face_detector
        self.recognizer = face_recognizer
        self.cam = camera_manager
        self.on_back = on_back

        # Capture session state
        self.is_capturing = False
        self.captured_crops: List[np.ndarray] = []
        self.last_capture_time = 0.0
        self.enrolled_user_id: Optional[int] = None
        self.current_guidance = "Look straight into camera"

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the two-column registration interface."""
        is_student = self.role == "student"
        role_label = "Student Registration" if is_student else "Teacher Registration"
        theme_color = config.COLOR_PRIMARY if is_student else "#0D9488"

        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=32, pady=(20, 12))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text=f"📝 {role_label}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        back_btn = ctk.CTkButton(
            top_bar,
            text="⬅ Cancel / Back",
            font=ctk.CTkFont(size=13),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#334155",
            height=36,
            corner_radius=8,
            command=self._on_cancel,
        )
        back_btn.pack(side="right")

        # Notification Banner
        self.notifier = NotificationBanner(self)

        # Main Layout Container (Left: Form, Right: Camera Preview)
        content_box = ctk.CTkFrame(self, fg_color="transparent")
        content_box.pack(fill="both", expand=True, padx=32, pady=10)
        content_box.grid_columnconfigure(0, weight=4)  # Form Column
        content_box.grid_columnconfigure(1, weight=6)  # Camera Column

        # ---------------------------------------------
        # LEFT COLUMN: Profile Form
        # ---------------------------------------------
        self.form_card = CardFrame(content_box)
        self.form_card.grid(row=0, column=0, padx=(0, 14), pady=0, sticky="nsew")

        f_hdr = ctk.CTkLabel(
            self.form_card,
            text="1. Enter Details",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.COLOR_NEON_CYAN,
        )
        f_hdr.pack(anchor="w", padx=20, pady=(20, 14))

        # Dynamic Form Inputs
        if is_student:
            self.name_entry = self._create_input(self.form_card, "Full Name *", "e.g. Rahul Sharma")
            self.class_selector = self._create_dropdown(
                self.form_card,
                "Class / Grade *",
                list(STUDENT_CLASSES),
                "Select class",
                command=self._on_student_class_change,
            )
            self.section_selector = self._create_dropdown(
                self.form_card,
                "Section *",
                ["Select class first"],
                "Select section",
                state="disabled",
            )
            self.roll_entry = self._create_input(self.form_card, "Roll Number *", "e.g. 23")
        else:
            self.name_entry = self._create_input(self.form_card, "Full Name *", "e.g. Dr. Ananya Sen")
            self.subject_entry = self._create_input(self.form_card, "Main Subject *", "e.g. Mathematics")
            self.uid_entry = self._create_input(self.form_card, "Teacher UID (Unique) *", "e.g. TCH-1042")

        # Capture Control Button
        self.start_cam_btn = ctk.CTkButton(
            self.form_card,
            text="2. Start Biometric Capture ➔",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=theme_color,
            hover_color=config.COLOR_PRIMARY_HOVER if is_student else "#0F766E",
            height=46,
            corner_radius=10,
            command=self._start_capture_flow,
        )
        self.start_cam_btn.pack(fill="x", padx=20, pady=(24, 16))

        # ---------------------------------------------
        # RIGHT COLUMN: Camera & Biometric Guide
        # ---------------------------------------------
        cam_card = CardFrame(content_box)
        cam_card.grid(row=0, column=1, padx=(14, 0), pady=0, sticky="nsew")

        c_hdr = ctk.CTkLabel(
            cam_card,
            text="Live Facial Capture & Preprocessing",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        c_hdr.pack(anchor="w", padx=20, pady=(16, 10))

        # Video Canvas
        self.video_canvas = VideoCanvas(cam_card, width=540, height=360)
        self.video_canvas.pack(padx=20, pady=(0, 10))
        self.video_canvas.show_message("Fill out credentials and press 'Start Biometric Capture'")

        # Active Facial Expression & Pose Guide Banner
        self.expression_prompt_lbl = ctk.CTkLabel(
            cam_card,
            text="Position face in center and start capture to record facial expressions",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_NEON_CYAN,
            wraplength=500,
        )
        self.expression_prompt_lbl.pack(pady=(4, 6))

        # Progress Label
        self.progress_lbl = ctk.CTkLabel(
            cam_card,
            text=f"Samples: 0 / {config.SAMPLES_PER_REGISTRATION}",
            font=ctk.CTkFont(size=12),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.progress_lbl.pack(pady=(0, 14))

    def _create_input(self, parent, label_text: str, placeholder: str) -> ctk.CTkEntry:
        """Helper to create standardized labeled entry fields."""
        lbl = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        lbl.pack(anchor="w", padx=20, pady=(6, 2))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=38,
            corner_radius=8,
            fg_color="#0F172A",
            border_color=config.COLOR_BORDER,
        )
        entry.pack(fill="x", padx=20, pady=(0, 6))
        return entry

    def _create_dropdown(
        self,
        parent,
        label_text: str,
        values: List[str],
        placeholder: str,
        state: str = "normal",
        command=None,
    ) -> ctk.CTkOptionMenu:
        """Create a standardized labeled dropdown for student class fields."""
        lbl = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        lbl.pack(anchor="w", padx=20, pady=(6, 2))

        dropdown = ctk.CTkOptionMenu(
            parent,
            values=values,
            command=command,
            height=38,
            corner_radius=8,
            fg_color="#0F172A",
            button_color=config.COLOR_PRIMARY,
            button_hover_color=config.COLOR_PRIMARY_HOVER,
            state=state,
        )
        dropdown.set(placeholder)
        dropdown.pack(fill="x", padx=20, pady=(0, 6))
        return dropdown

    def _on_student_class_change(self, class_name: str) -> None:
        """Refresh the section choices whenever registration class changes."""
        sections = STUDENT_SECTIONS.get(class_name, ())
        self.section_selector.configure(
            values=list(sections) if sections else ["Select class first"],
            state="normal" if sections else "disabled",
        )
        self.section_selector.set("Select section")

    def _start_capture_flow(self) -> None:
        """Validate input data, create database record, and activate camera stream."""
        if self.is_capturing:
            return

        # 1. Validation
        if self.role == "student":
            name = self.name_entry.get()
            class_name = self.class_selector.get()
            section = self.section_selector.get()
            roll_number = self.roll_entry.get()

            if class_name not in STUDENT_SECTIONS:
                self.notifier.show("Please select a valid class.", level="error")
                return
            if section not in STUDENT_SECTIONS[class_name]:
                self.notifier.show("Please select a section for this class.", level="error")
                return

            valid, err = validate_student_fields(name, class_name, section, roll_number)
            if not valid:
                self.notifier.show(f"Validation Error: {err}", level="error")
                return

            # Check duplicate student in SQLite
            existing = self.db.verify_student_credentials(name, class_name, section, roll_number)
            if existing:
                self.notifier.show(
                    f"Student with Class {class_name}-{section} and Roll {roll_number} is already registered!",
                    level="error",
                )
                return

        else:
            name = self.name_entry.get()
            subject = self.subject_entry.get()
            uid = self.uid_entry.get()

            valid, err = validate_teacher_fields(name, subject, uid)
            if not valid:
                self.notifier.show(f"Validation Error: {err}", level="error")
                return

            # Check duplicate teacher in SQLite
            existing = self.db.verify_teacher_credentials(name, subject, uid)
            if existing:
                self.notifier.show(f"Teacher UID '{uid}' is already registered!", level="error")
                return

        # Start the camera before creating a database record. This prevents failed
        # camera startup from leaving a student/teacher registered without samples.
        cam_started = self.cam.start()
        if not cam_started:
            self.notifier.show("Failed to initialize video input device.", level="error")
            return

        try:
            # Perform face duplicate check BEFORE creating final DB records.
            # Capture multiple quick candidate crops and require consistent duplicate
            # detection across them to avoid transient false positives.
            candidate_crops = []
            max_checks = 3
            attempts = 0
            # Basic face size threshold (pixels)
            min_face_width = 80
            min_face_height = 80

            while len(candidate_crops) < max_checks and attempts < 12:
                attempts += 1
                ret, f = self.cam.read_frame()
                if not ret or f is None:
                    continue
                faces = self.detector.detect_faces(f)
                if len(faces) != 1:
                    continue
                x, y, w, h = faces[0]
                if w < min_face_width or h < min_face_height:
                    continue
                crop = self.detector.extract_preprocessed_face(f, faces[0])
                if crop is not None:
                    # Face quality checks: blur and brightness
                    gray = crop if len(crop.shape) == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    # Blur via Laplacian variance
                    lap = cv2.Laplacian(gray, cv2.CV_64F)
                    blur_var = float(lap.var())
                    mean_brightness = float(gray.mean())
                    if blur_var < config.REGISTRATION_BLUR_THRESHOLD:
                        logger.debug(f"Discarding crop for blur (var={blur_var:.2f})")
                        continue
                    if not (config.REGISTRATION_BRIGHTNESS_MIN <= mean_brightness <= config.REGISTRATION_BRIGHTNESS_MAX):
                        logger.debug(f"Discarding crop for brightness (mean={mean_brightness:.1f})")
                        continue
                    candidate_crops.append(crop)

            if not candidate_crops:
                self.cam.release()
                self.notifier.show("No valid face available for duplicate check. Please try again.", level="error")
                return

            # Run duplicate detection on each candidate crop and collect results
            dup_matches = []  # list of (is_dup, matched_user, dist)
            for crop in candidate_crops:
                is_dup, matched_user, dist = self.recognizer.find_duplicate(crop)
                logger.info(f"Duplicate check result: is_dup={is_dup}, matched={matched_user}, dist={dist:.2f}")
                dup_matches.append((is_dup, matched_user, dist))

            # Decision logic:
            # - If majority (>=2/3) of crops indicate the SAME enrolled user as duplicate -> reject
            # - If any crops show a duplicate but matched_user differs across crops -> treat as borderline
            # - If distances are borderline (greater than DUPLICATE_FACE_THRESHOLD but less than LBPH_CONFIDENCE_THRESHOLD) -> ask recapture
            from collections import Counter

            dup_users = [m[1]["role"] + "_" + str(m[1]["id"]) for m in dup_matches if m[0] and m[1]]
            user_counts = Counter(dup_users)
            most_common = user_counts.most_common(1)

            # Check for majority same-user duplicate
            if most_common and most_common[0][1] >= 2:
                # Confirm distances are strongly below threshold across those crops
                matched_key = most_common[0][0]
                # collect distances for that matched user
                dists = [m[2] for m in dup_matches if m[0] and m[1] and (m[1]["role"] + "_" + str(m[1]["id"])) == matched_key]
                if dists and all(d <= config.DUPLICATE_FACE_THRESHOLD for d in dists):
                    self.cam.release()
                    self.notifier.show("Registration rejected: this face is already registered.", level="error")
                    return
                else:
                    self.cam.release()
                    self.notifier.show("Face could not be verified confidently. Please capture another image.", level="error")
                    return

            # No clear duplicate across majority of crops -> continue registration

            if self.role == "student":
                self.enrolled_user_id = self.db.register_student(
                    name, class_name, section, roll_number
                )
            else:
                self.enrolled_user_id = self.db.register_teacher(name, subject, uid)
        except ValueError as ve:
            self.cam.release()
            self.notifier.show(str(ve), level="error")
            return

        # Set user seed on virtual camera simulator (if active).
        user_seed = f"{self.role}_{self.enrolled_user_id}_{name}"
        self.cam.set_subject_seed(user_seed)

        self.is_capturing = True
        self.captured_crops = []
        self.last_capture_time = time.time()
        self.start_cam_btn.configure(state="disabled", text="Capturing Face Samples...")

        # Disable form entries during capture
        self._set_form_state("disabled")
        self.notifier.show("Webcam active! Follow on-screen pose instructions.", level="info")

        # Start frame loop
        self._process_camera_frame()

    def _set_form_state(self, state: str) -> None:
        """Enable or disable form inputs."""
        self.name_entry.configure(state=state)
        if self.role == "student":
            self.class_selector.configure(state=state)
            self.section_selector.configure(state=state)
            self.roll_entry.configure(state=state)
        else:
            self.subject_entry.configure(state=state)
            self.uid_entry.configure(state=state)

    def _determine_guidance(self, sample_idx: int) -> str:
        """Return directional pose and facial expression prompts."""
        if sample_idx < 5:
            return "1/5: Face Front — Neutral Expression"
        elif sample_idx < 10:
            return "2/5: Turn Head Slightly Left — Gentle Smile"
        elif sample_idx < 15:
            return "3/5: Turn Head Slightly Right — Normal / Open Eyes"
        elif sample_idx < 20:
            return "4/5: Tilt Chin Slightly Up — Broad Smile"
        else:
            return "5/5: Tilt Chin Down — Focused / Natural Expression"

    def _process_camera_frame(self) -> None:
        """Main camera acquisition and biometric extraction loop."""
        if not self.is_capturing:
            return

        ret, frame = self.cam.read_frame()
        if not ret or frame is None:
            self.after(30, self._process_camera_frame)
            return

        disp_frame = frame.copy()
        current_count = len(self.captured_crops)
        target_count = config.SAMPLES_PER_REGISTRATION

        # Detect faces in frame
        faces = self.detector.detect_faces(frame)
        detected_box = None

        if len(faces) == 0:
            self.current_guidance = "No face detected! Align face in center"
            self.expression_prompt_lbl.configure(text=f"⚠ {self.current_guidance}", text_color=config.COLOR_NEON_AMBER)
        elif len(faces) > 1:
            self.current_guidance = "Multiple faces detected! Only 1 person allowed"
            self.expression_prompt_lbl.configure(text=f"⚠ {self.current_guidance}", text_color=config.COLOR_NEON_RED)
        else:
            detected_box = faces[0]
            self.current_guidance = self._determine_guidance(current_count)
            self.expression_prompt_lbl.configure(text=f"📸 {self.current_guidance}", text_color=config.COLOR_NEON_CYAN)

            # Sample collection with timing interval to avoid identical redundant frames
            now = time.time()
            if (now - self.last_capture_time) * 1000 >= config.SAMPLE_CAPTURE_DELAY_MS:
                crop = self.detector.extract_preprocessed_face(frame, detected_box)
                if crop is not None:
                    gray = crop if len(crop.shape) == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                    mean_brightness = float(gray.mean())
                    if blur_var < config.REGISTRATION_BLUR_THRESHOLD:
                        self.current_guidance = "Image is too blurry; hold still"
                        self.expression_prompt_lbl.configure(
                            text=f"⚠ {self.current_guidance}",
                            text_color=config.COLOR_NEON_AMBER,
                        )
                    elif not (
                        config.REGISTRATION_BRIGHTNESS_MIN
                        <= mean_brightness
                        <= config.REGISTRATION_BRIGHTNESS_MAX
                    ):
                        self.current_guidance = "Adjust lighting before capture"
                        self.expression_prompt_lbl.configure(
                            text=f"⚠ {self.current_guidance}",
                            text_color=config.COLOR_NEON_AMBER,
                        )
                    else:
                        self.captured_crops.append(crop)
                        self.last_capture_time = now
                        current_count = len(self.captured_crops)
                        self.progress_lbl.configure(
                            text=f"Samples: {current_count} / {target_count}"
                        )

        # Draw futuristic registration guide HUD
        HolographicVisualizer.draw_registration_guide(
            disp_frame,
            sample_count=current_count,
            target_samples=target_count,
            guidance_text=self.current_guidance,
            detected_bbox=detected_box,
        )

        # Update Video Widget
        self.video_canvas.update_image(disp_frame)

        # Check if enrollment quota completed
        if current_count >= target_count:
            self._finalize_registration()
            return

        self.after(30, self._process_camera_frame)

    def _finalize_registration(self) -> None:
        """Save captured face crops, register paths in SQLite, and retrain recognizer."""
        self.is_capturing = False
        self.cam.release()

        self.video_canvas.show_message("Processing samples and training biometric model...")
        self.progress_lbl.configure(text="Finalizing enrollment...")

        user_dir = config.FACES_DIR / f"{self.role}_{self.enrolled_user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)

        sample_paths = []
        for idx, crop in enumerate(self.captured_crops):
            file_path = user_dir / f"sample_{idx + 1:02d}.jpg"
            cv2.imwrite(str(file_path), crop)
            sample_paths.append(str(file_path))

        # Save to SQLite
        self.db.save_face_samples(self.role, self.enrolled_user_id, sample_paths)

        # Retrain LBPH Recognizer Model
        trained_ok, train_msg = self.recognizer.train_from_database(self.db)
        if not trained_ok:
            self.notifier.show(f"Enrollment saved, but model training failed: {train_msg}", level="warning")
        else:
            self.notifier.show(
                f"✓ Registration complete! {len(sample_paths)} samples enrolled and biometric model updated.",
                level="success",
                duration_ms=6000,
            )

        # Show Completion Modal
        self._show_success_dialog()

    def _show_success_dialog(self) -> None:
        """Display stylish completion confirmation dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Registration Successful")
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        card = CardFrame(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        icon_lbl = ctk.CTkLabel(card, text="✓", font=ctk.CTkFont(size=44, weight="bold"), text_color=config.COLOR_NEON_GREEN)
        icon_lbl.pack(pady=(16, 4))

        title_lbl = ctk.CTkLabel(
            card,
            text="Biometric Profile Enrolled!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(pady=(0, 6))

        role_str = "Student" if self.role == "student" else "Teacher"
        detail_lbl = ctk.CTkLabel(
            card,
            text=f"{role_str} ID: #{self.enrolled_user_id}\nThe record and {len(self.captured_crops)} facial samples have been successfully recorded in the database.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
            wraplength=340,
        )
        detail_lbl.pack(pady=(0, 20), padx=20)

        ok_btn = ctk.CTkButton(
            card,
            text="Return to Role Menu",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            height=38,
            corner_radius=8,
            command=lambda: [dialog.destroy(), self.on_back()],
        )
        ok_btn.pack(fill="x", padx=30)

    def _on_cancel(self) -> None:
        """Handle cancellation, release camera and return to role menu."""
        self.is_capturing = False
        self.cam.release()
        self.on_back()
