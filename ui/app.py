"""
Main Application Container Module.
Initializes the CustomTkinter root window, instantiates database and vision services,
and manages screen transitions between Main Menu, Role Portals, Registration,
Attendance, and Audit Records.
"""

from typing import Optional
import customtkinter as ctk
import os
import sys

import config
from utils.logger import get_logger
from utils.camera import CameraManager
from database.db_manager import DatabaseManager
from face_recognition.detector import FaceDetector
from face_recognition.recognizer import FaceRecognizerManager
from ui.components import HeaderBar
from ui.main_menu import MainMenuView
from ui.role_menu import RoleMenuView
from ui.registration_view import RegistrationView
from ui.attendance_view import AttendanceView
from ui.records_view import RecordsView
from ui.users_view import UsersView

logger = get_logger(__name__)


class AttendanceApp(ctk.CTk):
    """Root Application Window with modular view navigation."""

    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title(config.APP_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(980, 640)
        self.configure(fg_color=config.COLOR_BG_DARK)
        try:
            self.iconbitmap(str(config.APP_ICON_PATH))
        except Exception as e:
            logger.warning(f"Could not set application icon: {e}")

        # Initialize core singletons
        logger.info("Initializing core system services...")
        self.db = DatabaseManager()
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizerManager()
        self.camera_manager = CameraManager()

        # Top Header Bar
        self.header = HeaderBar(self)
        self.header.pack(fill="x", side="top")

        # Dynamic Viewport Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.current_view: Optional[ctk.CTkFrame] = None

        # Protocol for clean window exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bring window to foreground on macOS.
        self.lift()
        self.attributes('-topmost', True)
        self.after(300, lambda: self.attributes('-topmost', False))
        self.focus_force()
        if sys.platform == "darwin":
            os.system(f"""/usr/bin/osascript -e 'tell application "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true' 2>/dev/null &""")

        # Show initial landing view
        self.show_main_menu()

    def _switch_view(self, new_view: ctk.CTkFrame, breadcrumb: str) -> None:
        """Helper to cleanly transition views and update breadcrumb."""
        if self.current_view is not None:
            # If current view has camera active, ensure camera is released
            if hasattr(self.current_view, "cam"):
                self.current_view.cam.release()
            self.current_view.destroy()

        self.header.set_breadcrumb(breadcrumb)
        self.current_view = new_view
        self.current_view.pack(fill="both", expand=True)

    def show_main_menu(self) -> None:
        """Display Main Dashboard."""
        view = MainMenuView(
            self.container,
            on_select_student=lambda: self.show_role_menu("student"),
            on_select_teacher=lambda: self.show_role_menu("teacher"),
            on_view_records=self.show_records,
            on_view_users=self.show_users,
            on_exit=self.on_closing,
            get_summary_stats=self.db.get_system_summary,
            on_instant_attendance=lambda: self.show_attendance("all"),
        )
        self._switch_view(view, "Main Dashboard")

    def show_role_menu(self, role: str) -> None:
        """Display Role Portal Sub-menu (Student or Teacher)."""
        role_cap = role.capitalize()
        view = RoleMenuView(
            self.container,
            role=role,
            on_register=self.show_registration,
            on_attendance=self.show_attendance,
            on_back=self.show_main_menu,
        )
        self._switch_view(view, f"{role_cap} Portal")

    def show_registration(self, role: str) -> None:
        """Display Registration and Biometric Enrollment View."""
        role_cap = role.capitalize()
        view = RegistrationView(
            self.container,
            role=role,
            db_manager=self.db,
            face_detector=self.detector,
            face_recognizer=self.recognizer,
            camera_manager=self.camera_manager,
            on_back=lambda: self.show_role_menu(role),
        )
        self._switch_view(view, f"{role_cap} Portal  ➔  Registration")

    def show_attendance(self, role: str) -> None:
        """Display Instant Face Attendance View."""
        if role == "all":
            breadcrumb = "Instant Face Attendance (All Roles)"
            back_callback = self.show_main_menu
        else:
            role_cap = role.capitalize()
            breadcrumb = f"{role_cap} Portal  ➔  Mark Attendance"
            back_callback = lambda: self.show_role_menu(role)

        view = AttendanceView(
            self.container,
            role=role,
            db_manager=self.db,
            face_detector=self.detector,
            face_recognizer=self.recognizer,
            camera_manager=self.camera_manager,
            on_back=back_callback,
        )
        self._switch_view(view, breadcrumb)

    def show_records(self) -> None:
        """Display Attendance Logs and Audit Explorer."""
        view = RecordsView(
            self.container,
            db_manager=self.db,
            on_back=self.show_main_menu,
            face_recognizer=self.recognizer,
        )
        self._switch_view(view, "Attendance Records & Logs")

    def show_users(self) -> None:
        """Display all registered students and teachers."""
        view = UsersView(
            self.container,
            db_manager=self.db,
            on_back=self.show_main_menu,
            face_recognizer=self.recognizer,
        )
        self._switch_view(view, "Registered Users")

    def on_closing(self) -> None:
        """Safely release camera hardware and terminate application."""
        logger.info("Application shutdown initiated.")
        try:
            if hasattr(self, "camera_manager") and self.camera_manager:
                self.camera_manager.release()
        except Exception as e:
            logger.warning(f"Error releasing camera on close: {e}")
        self.destroy()
