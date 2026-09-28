"""
Role Menu View.
Handles the role-specific options for Student and Teacher portals:
1. Register / Login
2. Sign In / Mark Attendance
3. Back
"""

from typing import Callable
import customtkinter as ctk

import config
from ui.components import CardFrame


class RoleMenuView(ctk.CTkFrame):
    """Sub-menu for a specific role (Student or Teacher)."""

    def __init__(
        self,
        master,
        role: str,
        on_register: Callable[[str], None],
        on_attendance: Callable[[str], None],
        on_back: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.role = role.lower()  # "student" or "teacher"
        self.on_register = on_register
        self.on_attendance = on_attendance
        self.on_back = on_back

        self._build_ui()

    def _build_ui(self) -> None:
        """Render role menu options."""
        is_student = self.role == "student"
        role_title = "Student Operations" if is_student else "Teacher Operations"
        role_icon = "👨‍🎓" if is_student else "👨‍🏫"
        role_badge = "STUDENT PORTAL" if is_student else "TEACHER PORTAL"
        theme_color = config.COLOR_PRIMARY if is_student else "#0D9488"

        # Top Header Card
        header_card = CardFrame(self)
        header_card.pack(fill="x", padx=32, pady=(24, 24))

        top_row = ctk.CTkFrame(header_card, fg_color="transparent")
        top_row.pack(fill="x", padx=24, pady=16)

        icon_lbl = ctk.CTkLabel(top_row, text=role_icon, font=ctk.CTkFont(size=36))
        icon_lbl.pack(side="left", padx=(0, 16))

        text_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        text_frame.pack(side="left")

        title_lbl = ctk.CTkLabel(
            text_frame,
            text=role_title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(anchor="w")

        badge_lbl = ctk.CTkLabel(
            text_frame,
            text=role_badge,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=theme_color,
        )
        badge_lbl.pack(anchor="w")

        # Back Button in Header
        back_btn = ctk.CTkButton(
            top_row,
            text="⬅ Back to Main Menu",
            font=ctk.CTkFont(size=13),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#334155",
            height=36,
            corner_radius=8,
            command=self.on_back,
        )
        back_btn.pack(side="right")

        # Two Main Operations Cards
        ops_container = ctk.CTkFrame(self, fg_color="transparent")
        ops_container.pack(fill="x", padx=32, pady=10)
        ops_container.grid_columnconfigure((0, 1), weight=1, uniform="ops")

        # Option 1: Register / Login
        reg_card = CardFrame(ops_container)
        reg_card.grid(row=0, column=0, padx=(0, 12), pady=0, sticky="nsew")

        reg_icon = ctk.CTkLabel(reg_card, text="📝", font=ctk.CTkFont(size=40))
        reg_icon.pack(pady=(28, 10))

        reg_title = ctk.CTkLabel(
            reg_card,
            text="Register / Login",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        reg_title.pack(pady=(0, 6))

        reg_desc_text = (
            "Enroll student credentials (Name, Class, Section, Roll No) and "
            "capture multi-angle biometric face samples."
            if is_student
            else "Enroll teacher profile (Name, Subject, Unique UID) and "
            "capture high-definition biometric face samples."
        )
        reg_desc = ctk.CTkLabel(
            reg_card,
            text=reg_desc_text,
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
            wraplength=340,
        )
        reg_desc.pack(pady=(0, 24), padx=20)

        reg_action_btn = ctk.CTkButton(
            reg_card,
            text="Start Registration  ➔",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=theme_color,
            hover_color=config.COLOR_PRIMARY_HOVER if is_student else "#0F766E",
            height=44,
            corner_radius=10,
            command=lambda: self.on_register(self.role),
        )
        reg_action_btn.pack(fill="x", padx=28, pady=(0, 28))

        # Option 2: Sign In / Mark Attendance
        att_card = CardFrame(ops_container)
        att_card.grid(row=0, column=1, padx=(12, 0), pady=0, sticky="nsew")

        att_icon = ctk.CTkLabel(att_card, text="📸", font=ctk.CTkFont(size=40))
        att_icon.pack(pady=(28, 10))

        att_title = ctk.CTkLabel(
            att_card,
            text="Sign In / Mark Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        att_title.pack(pady=(0, 6))

        att_desc_text = (
            "Instant automated face recognition: Simply look into the camera! "
            "Attendance is marked automatically with real-time hover details (Name, Roll, Class, Sec)."
            if is_student
            else "Instant faculty face recognition: Look into the camera! "
            "Attendance is logged automatically with real-time hover details (Name, UID, Subject)."
        )
        att_desc = ctk.CTkLabel(
            att_card,
            text=att_desc_text,
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
            wraplength=340,
        )
        att_desc.pack(pady=(0, 24), padx=20)

        att_action_btn = ctk.CTkButton(
            att_card,
            text="Mark Attendance  ➔",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",  # Emerald 600
            hover_color="#047857",
            height=44,
            corner_radius=10,
            command=lambda: self.on_attendance(self.role),
        )
        att_action_btn.pack(fill="x", padx=28, pady=(0, 28))
