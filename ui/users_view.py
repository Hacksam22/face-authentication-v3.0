"""Registered student and teacher list with ID-based deletion."""

from typing import Callable, Dict, Any, List
import customtkinter as ctk
from tkinter import messagebox

import config
from ui.components import NotificationBanner
from utils.logger import get_logger

logger = get_logger(__name__)


class UsersView(ctk.CTkFrame):
    """Browse registered users and delete them by their stable database ID."""

    def __init__(self, master, db_manager, on_back: Callable[[], None], face_recognizer=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_back = on_back
        self.recognizer = face_recognizer
        self._build_ui()
        self.load_users()

    def _build_ui(self) -> None:
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=32, pady=(20, 12))

        ctk.CTkLabel(
            top_bar,
            text="Registered Students & Teachers",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            top_bar,
            text="Back to Dashboard",
            font=ctk.CTkFont(size=13),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#334155",
            height=36,
            command=self.on_back,
        ).pack(side="right")

        self.notifier = NotificationBanner(self)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=32, pady=(0, 10))
        self.role_filter = ctk.CTkSegmentedButton(
            controls,
            values=["All", "Students", "Teachers"],
            command=lambda _value: self.load_users(),
        )
        self.role_filter.set("All")
        self.role_filter.pack(side="left")

        header = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8, height=38)
        header.pack(fill="x", padx=32, pady=(0, 4))
        header.pack_propagate(False)
        for label, width in (("User ID", 90), ("Role", 100), ("Name", 220), ("Registration Details", 360), ("Registered", 160), ("", 110)):
            ctk.CTkLabel(
                header,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.COLOR_NEON_CYAN,
                width=width,
                anchor="w",
            ).pack(side="left", padx=8)

        self.user_table = ctk.CTkScrollableFrame(
            self,
            fg_color=config.COLOR_CARD_DARK,
            corner_radius=10,
            border_width=1,
            border_color=config.COLOR_BORDER,
        )
        self.user_table.pack(fill="both", expand=True, padx=32, pady=(0, 20))

    def load_users(self) -> None:
        for widget in self.user_table.winfo_children():
            widget.destroy()

        selected_role = self.role_filter.get()
        users: List[Dict[str, Any]] = []
        if selected_role in ("All", "Students"):
            for student in self.db.get_all_students():
                users.append({
                    **student,
                    "role": "student",
                    "details": f"Class {student['class_name']} / Section {student['section']} / Roll {student['roll_number']}",
                })
        if selected_role in ("All", "Teachers"):
            for teacher in self.db.get_all_teachers():
                users.append({
                    **teacher,
                    "role": "teacher",
                    "details": f"Subject {teacher['subject']} / UID {teacher['teacher_uid']}",
                })
        users.sort(key=lambda user: (user["role"], user["name"].casefold(), user["id"]))

        if not users:
            ctk.CTkLabel(
                self.user_table,
                text="No registered users found.",
                font=ctk.CTkFont(size=14),
                text_color=config.COLOR_TEXT_SECONDARY,
            ).pack(pady=40)
            return

        for index, user in enumerate(users):
            role = user["role"]
            row = ctk.CTkFrame(
                self.user_table,
                fg_color="#1E293B" if index % 2 == 0 else "#192231",
                corner_radius=6,
                height=42,
            )
            row.pack(fill="x", pady=2, padx=4)
            row.pack_propagate(False)

            values = (
                (f"#{user['id']}", 90, config.COLOR_TEXT_PRIMARY),
                (role.upper(), 100, "#38BDF8" if role == "student" else "#2DD4BF"),
                (user["name"], 220, config.COLOR_TEXT_PRIMARY),
                (user["details"], 360, config.COLOR_TEXT_SECONDARY),
                (str(user.get("created_at", "")), 160, config.COLOR_TEXT_MUTED),
            )
            for text, width, color in values:
                ctk.CTkLabel(
                    row,
                    text=text,
                    font=ctk.CTkFont(size=12, weight="bold" if text == f"#{user['id']}" else "normal"),
                    text_color=color,
                    width=width,
                    anchor="w",
                ).pack(side="left", padx=8)

            ctk.CTkButton(
                row,
                text="Delete",
                width=94,
                height=30,
                fg_color="#B91C1C",
                hover_color="#991B1B",
                command=lambda selected_role=role, selected_id=user["id"], selected_name=user["name"]: self._delete_user(
                    selected_role, selected_id, selected_name
                ),
            ).pack(side="left", padx=8)

    def _delete_user(self, role: str, user_id: int, name: str) -> None:
        role_label = "student" if role == "student" else "teacher"
        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Permanently delete {role_label} {name} (ID #{user_id}) and all associated face samples and attendance records?",
            parent=self,
        )
        if not confirmed:
            return

        success, message = (
            self.db.delete_student(user_id)
            if role == "student"
            else self.db.delete_teacher(user_id)
        )
        if not success:
            self.notifier.show(message, level="error")
            logger.error(message)
            return

        self.notifier.show(message, level="success", duration_ms=4000)
        logger.info(message)
        if self.recognizer:
            try:
                trained, training_message = self.recognizer.train_from_database(self.db)
                if not trained:
                    logger.warning(f"Recognizer retraining after deletion failed: {training_message}")
            except Exception:
                logger.exception("Failed to retrain recognizer after user deletion")
        self.load_users()