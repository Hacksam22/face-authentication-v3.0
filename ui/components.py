"""
Reusable UI Components and Widgets for EduAttend.
Provides styled banners, cards, video canvas displays, and metric badges
using CustomTkinter.
"""

import time
import datetime
from typing import Optional, Callable
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np

import config


class HeaderBar(ctk.CTkFrame):
    """Modern top header bar with breadcrumb path, system title, and live clock."""

    def __init__(self, master, on_home_click: Optional[Callable] = None, **kwargs):
        super().__init__(master, height=64, fg_color=config.COLOR_CARD_DARK, corner_radius=0, **kwargs)
        self.pack_propagate(False)

        # Left branding
        self.brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.brand_frame.pack(side="left", padx=24, fill="y")

        self.logo_label = ctk.CTkLabel(
            self.brand_frame,
            text="🎓 ANMS ATTENDANCE",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLOR_NEON_CYAN,
        )
        self.logo_label.pack(side="left", padx=(0, 12), pady=16)

        self.breadcrumb_label = ctk.CTkLabel(
            self.brand_frame,
            text="|  Dashboard",
            font=ctk.CTkFont(size=14),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.breadcrumb_label.pack(side="left", pady=16)

        # Right Live Clock & Status
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(side="right", padx=24, fill="y")

        self.sys_status_pill = ctk.CTkLabel(
            self.status_frame,
            text="● SYSTEM READY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.COLOR_NEON_GREEN,
            fg_color="#132E27",
            corner_radius=12,
            padx=10,
            pady=4,
        )
        self.sys_status_pill.pack(side="left", padx=12, pady=16)

        self.clock_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        self.clock_label.pack(side="left", pady=16)

        self._update_clock()

    def set_breadcrumb(self, text: str) -> None:
        """Update current navigation path."""
        self.breadcrumb_label.configure(text=f"|  {text}")

    def _update_clock(self) -> None:
        """Periodic clock updater."""
        now_str = datetime.datetime.now().strftime("%a, %d %b %Y  %I:%M:%S %p")
        self.clock_label.configure(text=now_str)
        self.after(1000, self._update_clock)


class VideoCanvas(ctk.CTkFrame):
    """Embeds an OpenCV video stream into CustomTkinter using PIL."""

    def __init__(self, master, width: int = 580, height: int = 420, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color="#050B14",
            corner_radius=12,
            border_width=2,
            border_color=config.COLOR_BORDER,
            **kwargs,
        )
        self.pack_propagate(False)
        self.canvas_w = width
        self.canvas_h = height

        self.display_label = ctk.CTkLabel(
            self,
            text="Initializing Camera Stream...",
            font=ctk.CTkFont(size=14),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.display_label.pack(expand=True, fill="both", padx=4, pady=4)
        self._current_photo: Optional[ImageTk.PhotoImage] = None

    def update_image(self, bgr_frame: np.ndarray) -> None:
        """Render a raw BGR OpenCV frame onto the CTk display label."""
        try:
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            # Resize while preserving aspect ratio
            img = Image.fromarray(rgb_frame)
            img = img.resize((self.canvas_w, self.canvas_h), Image.Resampling.BILINEAR)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self.canvas_w, self.canvas_h))
            self.display_label.configure(image=ctk_img, text="")
        except Exception:
            pass

    def show_message(self, message: str) -> None:
        """Display an informational text notice in place of video."""
        self.display_label.configure(image=None, text=message)


class CardFrame(ctk.CTkFrame):
    """Modern styled card container."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=config.COLOR_CARD_DARK,
            corner_radius=14,
            border_width=1,
            border_color=config.COLOR_BORDER,
            **kwargs,
        )


class NotificationBanner(ctk.CTkFrame):
    """Dismissable or timed notification banner."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=44, corner_radius=8, **kwargs)
        self.pack_propagate(False)

        self.label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
        )
        self.label.pack(side="left", padx=16, pady=10)

    def show(self, message: str, level: str = "info", duration_ms: int = 4000) -> None:
        """Display message with level-specific background color."""
        if level == "error":
            bg = "#DC2626"  # Red
        elif level == "success":
            bg = "#16A34A"  # Green
        elif level == "warning":
            bg = "#D97706"  # Amber
        else:
            bg = config.COLOR_PRIMARY

        self.configure(fg_color=bg)
        self.label.configure(text=message)
        self.pack(fill="x", padx=24, pady=(8, 0))

        if duration_ms > 0:
            self.after(duration_ms, self.hide)

    def hide(self) -> None:
        """Hide the notification banner."""
        self.pack_forget()
