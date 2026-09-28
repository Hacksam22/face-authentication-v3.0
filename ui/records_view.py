"""
Attendance Records View.
Provides an administrative tabular view of verified attendance logs,
search/filtering by role and date, and CSV export capabilities.
"""

import csv
import datetime
from pathlib import Path
from typing import Callable, List, Dict, Any
import customtkinter as ctk

import config
from tkinter import messagebox, simpledialog
from ui.components import CardFrame, NotificationBanner
from utils.logger import get_logger

logger = get_logger(__name__)


class RecordsView(ctk.CTkFrame):
    """Administrative records explorer and report exporter."""

    def __init__(self, master, db_manager, on_back: Callable[[], None], face_recognizer=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_back = on_back
        self.recognizer = face_recognizer

        self.current_role_filter: str = "All"
        self._build_ui()
        self.load_records()

    def _build_ui(self) -> None:
        """Construct the records layout."""
        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=32, pady=(20, 12))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="📋 Attendance Records & Audit Log",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        back_btn = ctk.CTkButton(
            top_bar,
            text="⬅ Back to Dashboard",
            font=ctk.CTkFont(size=13),
            fg_color=config.COLOR_SECONDARY,
            hover_color="#334155",
            height=36,
            corner_radius=8,
            command=self.on_back,
        )
        back_btn.pack(side="right")

        self.notifier = NotificationBanner(self)

        # Filters Toolbar Card
        filter_card = CardFrame(self)
        filter_card.pack(fill="x", padx=32, pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=12)

        # Search Box
        self.search_entry = ctk.CTkEntry(
            f_row,
            placeholder_text="Search by candidate name...",
            width=260,
            height=36,
            corner_radius=8,
            fg_color="#0F172A",
            border_color=config.COLOR_BORDER,
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<Return>", lambda e: self.load_records())

        # Role Filter Segmented Button
        self.role_filter = ctk.CTkSegmentedButton(
            f_row,
            values=["All", "Students", "Teachers"],
            command=self._on_filter_changed,
            height=36,
            corner_radius=8,
        )
        self.role_filter.set("All")
        self.role_filter.pack(side="left", padx=(0, 12))

        # Search Button
        search_btn = ctk.CTkButton(
            f_row,
            text="Filter",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=config.COLOR_PRIMARY,
            hover_color=config.COLOR_PRIMARY_HOVER,
            width=80,
            height=36,
            corner_radius=8,
            command=self.load_records,
        )
        search_btn.pack(side="left", padx=(0, 8))

        # Export CSV Button
        export_btn = ctk.CTkButton(
            f_row,
            text="📥 Export CSV Report",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=36,
            corner_radius=8,
            command=self._export_csv,
        )
        export_btn.pack(side="right")

        # Admin: delete student by ID
        delete_btn = ctk.CTkButton(
            f_row,
            text="🗑️ Delete Student",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#B91C1C",
            hover_color="#991B1B",
            height=36,
            corner_radius=8,
            command=self._on_delete_student,
        )
        delete_btn.pack(side="right", padx=(0, 8))

        # Admin: delete teacher by ID
        delete_teacher_btn = ctk.CTkButton(
            f_row,
            text="🗑️ Delete Teacher",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#B91C1C",
            hover_color="#991B1B",
            height=36,
            corner_radius=8,
            command=self._on_delete_teacher,
        )
        delete_teacher_btn.pack(side="right", padx=(0, 8))

        # Table Header
        header_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8, height=38)
        header_card.pack(fill="x", padx=32, pady=(0, 4))
        header_card.pack_propagate(False)

        cols = [
            ("ID", 60),
            ("Role", 100),
            ("Candidate Name", 240),
            ("Date", 120),
            ("Time", 110),
            ("Status", 100),
            ("Confidence", 120),
        ]
        for name, width in cols:
            lbl = ctk.CTkLabel(
                header_card,
                text=name,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.COLOR_NEON_CYAN,
                width=width,
                anchor="w",
            )
            lbl.pack(side="left", padx=10)

        # Scrollable Record Container
        self.scroll_table = ctk.CTkScrollableFrame(
            self,
            fg_color=config.COLOR_CARD_DARK,
            corner_radius=10,
            border_width=1,
            border_color=config.COLOR_BORDER,
        )
        self.scroll_table.pack(fill="both", expand=True, padx=32, pady=(0, 20))

    def _on_filter_changed(self, value: str) -> None:
        """Handle role filter button toggle."""
        self.load_records()

    def load_records(self) -> None:
        """Fetch and populate records from database."""
        for w in self.scroll_table.winfo_children():
            w.destroy()

        filter_val = self.role_filter.get()
        role_param = None
        if filter_val == "Students":
            role_param = "student"
        elif filter_val == "Teachers":
            role_param = "teacher"

        search_q = self.search_entry.get().strip() or None

        records = self.db.get_attendance_records(
            role=role_param,
            search_query=search_q,
            limit=250,
        )

        if not records:
            empty_lbl = ctk.CTkLabel(
                self.scroll_table,
                text="No attendance records found matching criteria.",
                font=ctk.CTkFont(size=14),
                text_color=config.COLOR_TEXT_SECONDARY,
            )
            empty_lbl.pack(pady=40)
            return

        for idx, rec in enumerate(records):
            row_bg = "#1E293B" if idx % 2 == 0 else "#192231"
            row_frame = ctk.CTkFrame(self.scroll_table, fg_color=row_bg, corner_radius=6, height=36)
            row_frame.pack(fill="x", pady=2, padx=4)
            row_frame.pack_propagate(False)

            is_student = rec["user_role"] == "student"
            role_badge_col = "#38BDF8" if is_student else "#2DD4BF"

            # Col: ID
            ctk.CTkLabel(
                row_frame, text=f"#{rec['id']}", font=ctk.CTkFont(size=12), text_color=config.COLOR_TEXT_MUTED, width=60, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Role
            ctk.CTkLabel(
                row_frame, text=rec["user_role"].upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color=role_badge_col, width=100, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Name
            ctk.CTkLabel(
                row_frame, text=rec["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color=config.COLOR_TEXT_PRIMARY, width=240, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Date
            ctk.CTkLabel(
                row_frame, text=rec["date"], font=ctk.CTkFont(size=12), text_color=config.COLOR_TEXT_SECONDARY, width=120, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Time
            ctk.CTkLabel(
                row_frame, text=rec["time"], font=ctk.CTkFont(size=12), text_color=config.COLOR_TEXT_SECONDARY, width=110, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Status
            ctk.CTkLabel(
                row_frame, text=f"✓ {rec['status']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLOR_NEON_GREEN, width=100, anchor="w"
            ).pack(side="left", padx=10)

            # Col: Confidence
            conf = rec.get("confidence")
            conf_str = f"Dist: {conf:.1f}" if conf is not None else "Verified"
            ctk.CTkLabel(
                row_frame, text=conf_str, font=ctk.CTkFont(size=11), text_color=config.COLOR_TEXT_MUTED, width=120, anchor="w"
            ).pack(side="left", padx=10)

    def _export_csv(self) -> None:
        """Export all current attendance records to CSV file."""
        records = self.db.get_attendance_records(limit=1000)
        if not records:
            self.notifier.show("No records available to export.", level="warning")
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = config.DATA_DIR / f"attendance_report_{ts}.csv"

        try:
            with open(export_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "User Role", "User ID", "Name", "Date", "Time", "Status", "Distance Metric"])
                for r in records:
                    writer.writerow([
                        r["id"],
                        r["user_role"],
                        r["user_id"],
                        r["name"],
                        r["date"],
                        r["time"],
                        r["status"],
                        r.get("confidence", ""),
                    ])

            self.notifier.show(f"✓ Report exported to: {export_file.name}", level="success", duration_ms=6000)
            logger.info(f"Attendance report exported to {export_file}")
        except Exception as e:
            self.notifier.show(f"Failed to export CSV: {e}", level="error")
            logger.error(f"CSV export error: {e}", exc_info=True)

    def _on_delete_student(self) -> None:
        """Prompt for a student ID and delete the student and related data."""
        try:
            sid = simpledialog.askinteger("Delete Student", "Enter Student ID to delete:", parent=self)
            if sid is None:
                return

            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Permanently delete student ID {sid} and all associated face samples and attendance records?",
                parent=self,
            )
            if not confirm:
                return

            success, msg = self.db.delete_student(int(sid))
            if success:
                self.notifier.show(msg, level="success", duration_ms=4000)
                logger.info(msg)
                # Retrain recognizer to purge deleted user's labels
                try:
                    if self.recognizer:
                        tsucc, tmsg = self.recognizer.train_from_database(self.db)
                        if tsucc:
                            self.notifier.show("Recognizer retrained after deletion.", level="success", duration_ms=3000)
                            logger.info(f"Recognizer retrained: {tmsg}")
                        else:
                            logger.warning(f"Recognizer retrain failed: {tmsg}")
                except Exception:
                    logger.exception("Failed to retrain recognizer after student deletion")
                # Refresh records and stats
                self.load_records()
            else:
                self.notifier.show(msg, level="error")
                logger.error(msg)
        except Exception as e:
            self.notifier.show(f"Error deleting student: {e}", level="error")
            logger.exception("_on_delete_student failed")

    def _on_delete_teacher(self) -> None:
        """Prompt for a teacher ID and delete the teacher and related data."""
        try:
            tid = simpledialog.askinteger("Delete Teacher", "Enter Teacher ID to delete:", parent=self)
            if tid is None:
                return

            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Permanently delete teacher ID {tid} and all associated face samples and attendance records?",
                parent=self,
            )
            if not confirm:
                return

            success, msg = self.db.delete_teacher(int(tid))
            if success:
                self.notifier.show(msg, level="success", duration_ms=4000)
                logger.info(msg)
                # Retrain recognizer to purge deleted teacher's labels
                try:
                    if self.recognizer:
                        tsucc, tmsg = self.recognizer.train_from_database(self.db)
                        if tsucc:
                            self.notifier.show("Recognizer retrained after deletion.", level="success", duration_ms=3000)
                            logger.info(f"Recognizer retrained: {tmsg}")
                        else:
                            logger.warning(f"Recognizer retrain failed: {tmsg}")
                except Exception:
                    logger.exception("Failed to retrain recognizer after teacher deletion")
                # Refresh records and stats
                self.load_records()
            else:
                self.notifier.show(msg, level="error")
                logger.error(msg)
        except Exception as e:
            self.notifier.show(f"Error deleting teacher: {e}", level="error")
            logger.exception("_on_delete_teacher failed")
