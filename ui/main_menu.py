"""
Main Menu View.
Provides the primary landing dashboard with Student, Teacher, and Exit options,
along with quick administrative stats.
"""

from typing import Callable
import customtkinter as ctk

import config
from ui.components import CardFrame


class MainMenuView(ctk.CTkFrame):
    """Main Menu Screen displaying Student, Teacher, and Exit navigation."""

    def __init__(
        self,
        master,
        on_select_student: Callable[[], None],
        on_select_teacher: Callable[[], None],
        on_view_records: Callable[[], None],
        on_exit: Callable[[], None],
        get_summary_stats: Callable[[], dict],
        on_instant_attendance: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_select_student = on_select_student
        self.on_select_teacher = on_select_teacher
        self.on_view_records = on_view_records
        self.on_exit = on_exit
        self.get_summary_stats = get_summary_stats
        self.on_instant_attendance = on_instant_attendance

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct dashboard components."""
        # Hero Welcome Banner Card
        hero_card = CardFrame(self)
        hero_card.pack(fill="x", padx=32, pady=(24, 20))

        school_name_lbl = ctk.CTkLabel(
            hero_card,
            text="Authpur National Model Higher Secondary School",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=config.COLOR_NEON_CYAN,
        )
        school_name_lbl.pack(pady=(20, 2))

        title_lbl = ctk.CTkLabel(
            hero_card,
            text="School Attendance Management System",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(pady=(0, 6))

        subtitle_lbl = ctk.CTkLabel(
            hero_card,
            text="Autonomous OpenCV Face Detection & Biometric Verification Engine",
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        subtitle_lbl.pack(pady=(0, 18))

        # Main Action Portal Cards Grid
        portal_container = ctk.CTkFrame(self, fg_color="transparent")
        portal_container.pack(fill="x", padx=32, pady=10)
        portal_container.grid_columnconfigure((0, 1), weight=1, uniform="portal")

        # 1. Student Portal Card
        student_card = CardFrame(portal_container)
        student_card.grid(row=0, column=0, padx=(0, 12), pady=0, sticky="nsew")

        s_icon = ctk.CTkLabel(student_card, text="👨‍🎓", font=ctk.CTkFont(size=44))
        s_icon.pack(pady=(24, 8))

        s_title = ctk.CTkLabel(
            student_card,
            text="Student Portal",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        s_title.pack(pady=(0, 6))

        s_desc = ctk.CTkLabel(
            student_card,
            text="Register new student profiles and verify daily classroom attendance.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
            wraplength=340,
        )
        s_desc.pack(pady=(0, 20), padx=20)

        s_btn = ctk.CTkButton(
            student_card,
            text="Enter Student Portal  ➔",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_PRIMARY_HOVER,
            height=44,
            corner_radius=10,
            command=self.on_select_student,
        )
        s_btn.pack(fill="x", padx=24, pady=(0, 24))

        # 2. Teacher Portal Card
        teacher_card = CardFrame(portal_container)
        teacher_card.grid(row=0, column=1, padx=(12, 0), pady=0, sticky="nsew")

        t_icon = ctk.CTkLabel(teacher_card, text="👨‍🏫", font=ctk.CTkFont(size=44))
        t_icon.pack(pady=(24, 8))

        t_title = ctk.CTkLabel(
            teacher_card,
            text="Teacher Portal",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        t_title.pack(pady=(0, 6))

        t_desc = ctk.CTkLabel(
            teacher_card,
            text="Staff biometric registration and faculty duty check-in management.",
            font=ctk.CTkFont(size=13),
            text_color=config.COLOR_TEXT_SECONDARY,
            wraplength=340,
        )
        t_desc.pack(pady=(0, 20), padx=20)

        t_btn = ctk.CTkButton(
            teacher_card,
            text="Enter Teacher Portal  ➔",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0D9488",  # Teal 600
            hover_color="#0F766E",
            height=44,
            corner_radius=10,
            command=self.on_select_teacher,
        )
        t_btn.pack(fill="x", padx=24, pady=(0, 24))

        # Secondary Actions Container (Records & Exit)
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=32, pady=(18, 12))

        records_btn = ctk.CTkButton(
            bottom_bar,
            text="📋 View Attendance Records",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=config.COLOR_CARD_DARK,
            hover_color=config.COLOR_CARD_HOVER,
            border_width=1,
            border_color=config.COLOR_BORDER,
            height=40,
            corner_radius=8,
            command=self.on_view_records,
        )
        records_btn.pack(side="left")

        if self.on_instant_attendance:
            instant_btn = ctk.CTkButton(
                bottom_bar,
                text="⚡ Instant Face Attendance (All Roles)",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#059669",
                hover_color="#047857",
                height=40,
                corner_radius=8,
                command=self.on_instant_attendance,
            )
            instant_btn.pack(side="left", padx=12)

        exit_btn = ctk.CTkButton(
            bottom_bar,
            text="🚪 Exit Application",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#331A1E",
            text_color="#F87171",
            hover_color="#451D22",
            border_width=1,
            border_color="#7F1D1D",
            height=40,
            corner_radius=8,
            command=self.on_exit,
        )
        exit_btn.pack(side="right")

        # Stats Summary Footer
        self.stats_card = CardFrame(self)
        self.stats_card.pack(fill="x", padx=32, pady=(6, 20))
        self._build_stats_content()

    def _build_stats_content(self) -> None:
        """Render live database summary metrics."""
        for widget in self.stats_card.winfo_children():
            widget.destroy()

        stats = self.get_summary_stats()
        metrics = [
            ("Students Enrolled", str(stats.get("total_students", 0)), "#38BDF8"),
            ("Teachers Registered", str(stats.get("total_teachers", 0)), "#2DD4BF"),
            ("Biometrics Trained", str(stats.get("biometric_enrolled", 0)), "#A78BFA"),
            ("Today's Attendance", str(stats.get("today_attendance", 0)), config.COLOR_NEON_GREEN),
        ]

        self.stats_card.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        for idx, (label, val, color) in enumerate(metrics):
            item_frame = ctk.CTkFrame(self.stats_card, fg_color="transparent")
            item_frame.grid(row=0, column=idx, padx=16, pady=14, sticky="nsew")

            val_lbl = ctk.CTkLabel(
                item_frame,
                text=val,
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=color,
            )
            val_lbl.pack()

            txt_lbl = ctk.CTkLabel(
                item_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color=config.COLOR_TEXT_SECONDARY,
            )
            txt_lbl.pack()

    def refresh(self) -> None:
        """Refresh dynamic stats upon returning to main menu."""
        self._build_stats_content()
