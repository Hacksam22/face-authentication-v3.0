"""
Instant Face Attendance View.
Zero-form automatic attendance marking: Users simply look into the camera.
Identifies faces in real-time via 1:N LBPH matching, renders interactive floating
hover details (Name, Roll, Class, Section) adjacent to the face, and automatically
records attendance in SQLite without duplicate entries.
"""

import time
import datetime
from typing import Callable, Optional, Dict, Any, List
import cv2
import numpy as np
import customtkinter as ctk

import config
from utils.logger import get_logger
from ui.components import CardFrame, VideoCanvas, NotificationBanner
from ui.student_options import STUDENT_CLASSES, STUDENT_SECTIONS
from face_recognition.visualizer import HolographicVisualizer

logger = get_logger(__name__)

class AttendanceView(ctk.CTkFrame):
    """Automatic facial recognition attendance kiosk with live hover cards and activity ticker."""

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
        self.role = role.lower()  # "student", "teacher", or "all"
        self.db = db_manager
        self.detector = face_detector
        self.recognizer = face_recognizer
        self.cam = camera_manager
        self.on_back = on_back

        # Camera loop state
        self.is_camera_active = False

        # Debounce and recognition cache to prevent repeated redundant DB writes
        self._user_cooldowns: Dict[str, float] = {}
        self._cached_profiles: Dict[str, Dict[str, Any]] = {}
        self._already_marked_cache: Dict[str, bool] = {}
        self._verified_student: Optional[Dict[str, Any]] = None
        self._student_lookup_job = None

        self._build_ui()
        if self.role != "student":
            self._start_camera_feed()

    def _user_key(self, role: str, user_id: int) -> str:
        return f"{role}_{user_id}"

    def _build_ui(self) -> None:
        """Construct the attendance interface with camera canvas and live activity sidebar."""
        is_student = self.role == "student"
        is_teacher = self.role == "teacher"
        if is_student:
            role_label = "Student Attendance"
            theme_color = config.COLOR_PRIMARY
        elif is_teacher:
            role_label = "Teacher Attendance"
            theme_color = "#0D9488"
        else:
            role_label = "School-wide Attendance"
            theme_color = config.COLOR_NEON_GREEN

        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=32, pady=(20, 10))

        title_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_frame.pack(side="left")

        title_lbl = ctk.CTkLabel(
            title_frame,
            text=f"📸 {role_label} — Live Face Recognition",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_frame,
            text=(
                "Select class, section, and roll number to verify a registered student"
                if is_student
                else "Automatic Attendance Marking  •  Simply face the camera  •  No manual credentials needed"
            ),
            font=ctk.CTkFont(size=12),
            text_color=config.COLOR_NEON_CYAN,
        )
        sub_lbl.pack(anchor="w")

        back_btn = ctk.CTkButton(
            top_bar,
            text="⬅ Return to Menu",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#334155",
            height=38,
            corner_radius=8,
            command=self._on_close,
        )
        back_btn.pack(side="right")

        # Notification Banner
        self.notifier = NotificationBanner(self)

        if is_student:
            self._build_student_verification_form()

        # Main Workspace Container
        content_box = ctk.CTkFrame(self, fg_color="transparent")
        content_box.pack(fill="both", expand=True, padx=32, pady=10)
        content_box.grid_columnconfigure(0, weight=7)  # Camera column
        content_box.grid_columnconfigure(1, weight=3)  # Recent activity ticker

        # -------------------------------------------------------------
        # LEFT COLUMN: Live Camera Feed with Hover Details
        # -------------------------------------------------------------
        cam_card = CardFrame(content_box)
        cam_card.grid(row=0, column=0, padx=(0, 14), pady=0, sticky="nsew")

        c_header = ctk.CTkFrame(cam_card, fg_color="transparent")
        c_header.pack(fill="x", padx=20, pady=(14, 8))

        self.stream_status_pill = ctk.CTkLabel(
            c_header,
            text="● SCANNER LOCKED" if is_student else "● SCANNER ONLINE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.COLOR_NEON_AMBER if is_student else config.COLOR_NEON_GREEN,
            fg_color="#332A16" if is_student else "#132E27",
            corner_radius=10,
            padx=10,
            pady=3,
        )
        self.stream_status_pill.pack(side="left")

        ctk.CTkLabel(
            c_header,
            text=(
                "Face verification starts after the registered student is found"
                if is_student
                else "Look into camera to automatically log attendance with real-time hover details"
            ),
            font=ctk.CTkFont(size=12),
            text_color=config.COLOR_TEXT_SECONDARY,
        ).pack(side="left", padx=12)

        # Video Canvas
        self.video_canvas = VideoCanvas(
            cam_card, width=640, height=320 if is_student else 440
        )
        self.video_canvas.pack(padx=20, pady=(0, 10))
        if is_student:
            self.video_canvas.show_message(
                "Enter a registered student's class, section, and roll number first."
            )

        # Bottom scanner status
        self.status_bar_lbl = ctk.CTkLabel(
            cam_card,
            text=(
                "Complete the student details and fetch the registered name."
                if is_student
                else "Scanning camera feed... Position face within the frame."
            ),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_NEON_CYAN,
        )
        self.status_bar_lbl.pack(pady=(0, 14))

        # -------------------------------------------------------------
        # RIGHT COLUMN: Live Real-Time Check-In Activity
        # -------------------------------------------------------------
        ticker_card = CardFrame(content_box)
        ticker_card.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="nsew")

        t_hdr = ctk.CTkFrame(ticker_card, fg_color="transparent")
        t_hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            t_hdr,
            text="Recent Check-Ins",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.today_counter_lbl = ctk.CTkLabel(
            t_hdr,
            text="Today: 0",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.COLOR_NEON_GREEN,
            fg_color="#132E27",
            corner_radius=10,
            padx=8,
            pady=2,
        )
        self.today_counter_lbl.pack(side="right")

        # Scrollable Activity Feed
        self.activity_scroll = ctk.CTkScrollableFrame(
            ticker_card,
            fg_color="#0F172A",
            corner_radius=8,
            border_width=1,
            border_color=config.COLOR_BORDER,
        )
        self.activity_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Pre-populate activity feed with today's logged attendees
        self._refresh_activity_feed()

    def _build_student_verification_form(self) -> None:
        """Create the student identity lookup gate shown before face verification."""
        form = CardFrame(self)
        form.pack(fill="x", padx=32, pady=(0, 4))
        for column in range(4):
            form.grid_columnconfigure(column, weight=1)

        fields = (
            ("Class *", 0),
            ("Section *", 1),
            ("Roll Number *", 2),
            ("Registered Student Name", 3),
        )
        for label_text, column in fields:
            ctk.CTkLabel(
                form,
                text=label_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=config.COLOR_TEXT_SECONDARY,
            ).grid(row=0, column=column, sticky="w", padx=12, pady=(10, 2))

        self.class_selector = ctk.CTkOptionMenu(
            form,
            values=list(STUDENT_CLASSES),
            command=self._on_student_class_change,
            height=34,
        )
        self.class_selector.set("Select class")
        self.class_selector.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.section_selector = ctk.CTkOptionMenu(
            form,
            values=["Select class first"],
            command=lambda _value: self._schedule_student_lookup(),
            height=34,
            state="disabled",
        )
        self.section_selector.set("Select section")
        self.section_selector.grid(row=1, column=1, sticky="ew", padx=12, pady=(0, 8))

        self.roll_entry = ctk.CTkEntry(
            form,
            placeholder_text="Enter roll number",
            height=34,
        )
        self.roll_entry.grid(row=1, column=2, sticky="ew", padx=12, pady=(0, 8))
        self.roll_entry.bind("<KeyRelease>", lambda _event: self._schedule_student_lookup())

        self.student_name_entry = ctk.CTkEntry(
            form,
            placeholder_text="Fetched from registration database",
            height=34,
            state="disabled",
        )
        self.student_name_entry.grid(row=1, column=3, sticky="ew", padx=12, pady=(0, 8))

        self.lookup_status_lbl = ctk.CTkLabel(
            form,
            text="Choose a class, then section and roll number.",
            font=ctk.CTkFont(size=11),
            text_color=config.COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self.lookup_status_lbl.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 10))

        self.verify_face_btn = ctk.CTkButton(
            form,
            text="Start Face Verification",
            command=self._start_camera_feed,
            state="disabled",
            height=34,
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_PRIMARY_HOVER,
        )
        self.verify_face_btn.grid(row=2, column=3, sticky="ew", padx=12, pady=(0, 10))

    def _on_student_class_change(self, class_name: str) -> None:
        """Update available sections and invalidate any previous student match."""
        sections = STUDENT_SECTIONS.get(class_name, ())
        self.section_selector.configure(
            values=list(sections) if sections else ["Select class first"],
            state="normal" if sections else "disabled",
        )
        self.section_selector.set("Select section")
        self._schedule_student_lookup()

    def _set_student_name(self, name: str = "") -> None:
        self.student_name_entry.configure(state="normal")
        self.student_name_entry.delete(0, "end")
        if name:
            self.student_name_entry.insert(0, name)
        self.student_name_entry.configure(state="disabled")

    def _schedule_student_lookup(self) -> None:
        """Debounce roll-number typing and clear stale lookup results immediately."""
        if self._student_lookup_job is not None:
            self.after_cancel(self._student_lookup_job)
            self._student_lookup_job = None

        self._verified_student = None
        self._set_student_name()
        self.verify_face_btn.configure(state="disabled")

        class_name = self.class_selector.get()
        section = self.section_selector.get()
        roll_number = self.roll_entry.get().strip()
        if class_name not in STUDENT_SECTIONS:
            self.lookup_status_lbl.configure(text="Choose a valid class.", text_color=config.COLOR_TEXT_SECONDARY)
            return
        if section not in STUDENT_SECTIONS[class_name]:
            self.lookup_status_lbl.configure(text="Choose a section for the selected class.", text_color=config.COLOR_TEXT_SECONDARY)
            return
        if not roll_number:
            self.lookup_status_lbl.configure(text="Enter a roll number to fetch the student name.", text_color=config.COLOR_TEXT_SECONDARY)
            return

        self.lookup_status_lbl.configure(text="Looking up registered student...", text_color=config.COLOR_NEON_CYAN)
        self._student_lookup_job = self.after(300, self._lookup_registered_student)

    def _lookup_registered_student(self) -> None:
        """Fetch and display the registered student matching the selected fields."""
        self._student_lookup_job = None
        class_name = self.class_selector.get()
        section = self.section_selector.get()
        roll_number = self.roll_entry.get().strip()
        try:
            student = self.db.get_student_by_class_section_roll(
                class_name, section, roll_number
            )
        except Exception:
            logger.exception("Student lookup failed during attendance verification.")
            self.lookup_status_lbl.configure(
                text="Student lookup failed. Please try again.",
                text_color=config.COLOR_NEON_RED,
            )
            return

        if not student:
            self.lookup_status_lbl.configure(
                text="No registered student matches these details.",
                text_color=config.COLOR_NEON_RED,
            )
            return

        self._verified_student = student
        self._set_student_name(student["name"])
        self.lookup_status_lbl.configure(
            text="Student found. Start face verification when ready.",
            text_color=config.COLOR_NEON_GREEN,
        )
        self.verify_face_btn.configure(state="normal")

    def _start_camera_feed(self) -> None:
        """Initialize camera and begin continuous real-time recognition loop."""
        if self.is_camera_active:
            return
        if self.role == "student":
            if not self._verified_student:
                return
            user_key = self._user_key("student", self._verified_student["id"])
            self._cached_profiles[user_key] = self._verified_student

        cam_ok = self.cam.start()
        if not cam_ok:
            self.video_canvas.show_message("Unable to access camera device.")
            self.notifier.show("Physical camera failed to start.", level="error")
            return

        self.is_camera_active = True
        if self.role == "student":
            self.stream_status_pill.configure(
                text="● SCANNER ONLINE",
                text_color=config.COLOR_NEON_GREEN,
                fg_color="#132E27",
            )
            self.class_selector.configure(state="disabled")
            self.section_selector.configure(state="disabled")
            self.roll_entry.configure(state="disabled")
            self.verify_face_btn.configure(state="disabled", text="Verifying Face...")
            self.status_bar_lbl.configure(
                text=f"Verifying face for {self._verified_student['name']}...",
                text_color=config.COLOR_NEON_CYAN,
            )
        self.after(30, self._process_stream)

    def _process_stream(self) -> None:
        """Main recognition and automatic marking loop."""
        if not self.is_camera_active:
            return

        ret, frame = self.cam.read_frame()
        if not ret or frame is None:
            self.after(30, self._process_stream)
            return

        disp_frame = frame.copy()
        faces = self.detector.detect_faces(frame)

        if len(faces) == 0:
            self.status_bar_lbl.configure(
                text="Awaiting face... Stand in front of camera",
                text_color=config.COLOR_TEXT_SECONDARY,
            )
            HolographicVisualizer.draw_scanning_hud(
                disp_frame, bbox=None, status_text="AWAITING FACE...", is_error=False
            )
        else:
            identity_text = (
                f" — verifying {self._verified_student['name']}"
                if self.role == "student" and self._verified_student
                else " — identifying biometrics"
            )
            self.status_bar_lbl.configure(
                text=f"Detected {len(faces)} face(s){identity_text}...",
                text_color=config.COLOR_NEON_CYAN,
            )

            # Process each detected face independently to avoid result reuse.
            face_results = []  # collect per-face outcomes for clearer logging and rendering
            for bbox in faces:
                crop = self.detector.extract_preprocessed_face(frame, bbox)
                if crop is None:
                    HolographicVisualizer.draw_unrecognized_hover(
                        disp_frame, bbox=bbox, status_text="FACE POOR QUALITY"
                    )
                    logger.debug(f"Face bbox={bbox} poor quality - skipped")
                    continue
                    continue

                # Per-face recognition
                if self.role == "student":
                    student = self._verified_student
                    if not student:
                        continue
                    is_recognized, distance, _message = self.recognizer.verify_user_face(
                        crop, target_role="student", target_user_id=student["id"]
                    )
                    # Ensure strict acceptance by distance
                    if not is_recognized or distance > config.RECOGNITION_ACCEPT_THRESHOLD:
                        is_recognized = False
                        user_ref = None
                    else:
                        user_ref = {"role": "student", "id": student["id"]}
                else:
                    # 1:N Facial Identification for teacher and school-wide attendance.
                    is_recognized, user_ref, distance = self.recognizer.identify_face(
                        crop, role_filter=self.role
                    )
                    # Apply stricter per-face acceptance threshold
                    if not is_recognized or distance > config.RECOGNITION_ACCEPT_THRESHOLD:
                        is_recognized = False
                        user_ref = None

                # Record the result for this bbox
                face_results.append({
                    "bbox": bbox,
                    "is_recognized": bool(is_recognized),
                    "user_ref": user_ref,
                    "distance": float(distance) if 'distance' in locals() else None,
                })

            # Debug-log all per-face predictions for this frame
            for fr in face_results:
                logger.info(
                    f"Face result: bbox={fr['bbox']} recognized={fr['is_recognized']} user_ref={fr['user_ref']} distance={fr['distance']}"
                )

            # Now render and act on each face result independently
            for fr in face_results:
                bbox = fr["bbox"]
                is_recognized = fr["is_recognized"]
                user_ref = fr["user_ref"]
                distance = fr["distance"]

                if is_recognized and user_ref:
                    user_role = user_ref["role"]
                    user_id = user_ref["id"]
                    user_key = self._user_key(user_role, user_id)

                    # Fetch user record (cached for speed)
                    if user_key not in self._cached_profiles:
                        profile = self.db.get_user_by_role_and_id(user_role, user_id)
                        if profile:
                            self._cached_profiles[user_key] = profile
                    user_info = self._cached_profiles.get(user_key)

                    if user_info:
                        now = time.time()
                        last_action_time = self._user_cooldowns.get(user_key, 0.0)

                        # Check if already marked today
                        if user_key not in self._already_marked_cache:
                            already_marked, _ = self.db.is_attendance_marked_today(
                                user_role, user_id
                            )
                            self._already_marked_cache[user_key] = already_marked
                        is_already_marked = self._already_marked_cache[user_key]

                        # If not marked today and cooldown expired (or first detection):
                        if not is_already_marked and (now - last_action_time >= 4.0):
                            # Mark attendance automatically in SQLite!
                            success, msg, rec = self.db.mark_attendance(
                                user_id=user_id,
                                user_role=user_role,
                                name=user_info["name"],
                                confidence=distance,
                            )
                            if success:
                                self._already_marked_cache[user_key] = True
                                self._user_cooldowns[user_key] = now
                                self.notifier.show(
                                    f"✓ Attendance auto-marked for {user_info['name']}!",
                                    level="success",
                                    duration_ms=4000,
                                )
                                self._add_activity_entry(user_info, user_role, rec.get("time"))
                                self._update_today_count()
                            else:
                                self._already_marked_cache[user_key] = True

                        # Draw the floating holographic hover details card right beside the face!
                        HolographicVisualizer.draw_hover_card(
                            disp_frame,
                            bbox=bbox,
                            user_info=user_info,
                            user_role=user_role,
                            is_already_marked=self._already_marked_cache.get(user_key, False),
                        )
                else:
                    # Unrecognized face: Draw cyber alert box and floating badge
                    HolographicVisualizer.draw_unrecognized_hover(
                        disp_frame, bbox=bbox, status_text="UNRECOGNIZED PERSON"
                    )

        self.video_canvas.update_image(disp_frame)
        self.after(30, self._process_stream)

    def _add_activity_entry(
        self, user_info: Dict[str, Any], user_role: str, time_str: Optional[str]
    ) -> None:
        """Prepend a fresh check-in card to the real-time activity feed."""
        row_frame = ctk.CTkFrame(
            self.activity_scroll, fg_color="#1E293B", corner_radius=6, height=54
        )
        # Prepend to top
        row_frame.pack(fill="x", pady=3, padx=2, side="top")
        row_frame.pack_propagate(False)

        left_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        left_box.pack(side="left", padx=10, fill="y", pady=6)

        name_lbl = ctk.CTkLabel(
            left_box,
            text=user_info.get("name", "Unknown"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        name_lbl.pack(anchor="w")

        if str(user_role).lower() == "student":
            sub_text = f"Roll: {user_info.get('roll_number')} | Class: {user_info.get('class_name')}-{user_info.get('section')}"
        else:
            sub_text = f"UID: {user_info.get('teacher_uid')} | {user_info.get('subject')}"

        sub_lbl = ctk.CTkLabel(
            left_box,
            text=sub_text,
            font=ctk.CTkFont(size=10),
            text_color=config.COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        sub_lbl.pack(anchor="w")

        right_box = ctk.CTkFrame(row_frame, fg_color="transparent")
        right_box.pack(side="right", padx=10, pady=6)

        t_str = time_str or datetime.datetime.now().strftime("%H:%M:%S")
        time_lbl = ctk.CTkLabel(
            right_box,
            text=t_str,
            font=ctk.CTkFont(size=10),
            text_color=config.COLOR_TEXT_MUTED,
        )
        time_lbl.pack()

        badge_lbl = ctk.CTkLabel(
            right_box,
            text="✓ Present",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=config.COLOR_NEON_GREEN,
        )
        badge_lbl.pack()

    def _refresh_activity_feed(self) -> None:
        """Populate the activity feed with attendance records already logged today."""
        for w in self.activity_scroll.winfo_children():
            w.destroy()

        today_date = datetime.date.today().isoformat()
        role_param = None if self.role == "all" else self.role
        records = self.db.get_attendance_records(role=role_param, date_str=today_date, limit=20)

        self.today_counter_lbl.configure(text=f"Today: {len(records)}")

        if not records:
            empty_lbl = ctk.CTkLabel(
                self.activity_scroll,
                text="No check-ins logged yet today.\nStand in front of the camera to check in.",
                font=ctk.CTkFont(size=11),
                text_color=config.COLOR_TEXT_SECONDARY,
                justify="center",
            )
            empty_lbl.pack(pady=30)
            return

        for rec in records:
            profile = self.db.get_user_by_role_and_id(rec["user_role"], rec["user_id"])
            info = profile if profile else {"name": rec["name"]}
            self._add_activity_entry(info, rec["user_role"], rec["time"])

    def _update_today_count(self) -> None:
        """Increment today's attendance count badge."""
        today_date = datetime.date.today().isoformat()
        role_param = None if self.role == "all" else self.role
        records = self.db.get_attendance_records(role=role_param, date_str=today_date, limit=500)
        self.today_counter_lbl.configure(text=f"Today: {len(records)}")

    def _on_close(self) -> None:
        """Release camera and return to prior view."""
        self.is_camera_active = False
        if self._student_lookup_job is not None:
            self.after_cancel(self._student_lookup_job)
            self._student_lookup_job = None
        self.cam.release()
        self.on_back()
