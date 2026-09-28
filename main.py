"""
Main Entry Point for the School Attendance Management System.
Initializes runtime directories, validates environment dependencies,
and launches the CustomTkinter GUI application.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from utils.logger import get_logger
from ui.app import AttendanceApp

logger = get_logger("ANMS ATTENDANCE")


def main() -> None:
    """Initialize system and start GUI event loop."""
    logger.info("=" * 60)
    logger.info(f"Starting {config.APP_TITLE}")
    logger.info(f"Python Version: {sys.version.split()[0]}")
    logger.info(f"Database Path : {config.DB_PATH}")
    logger.info("=" * 60)

    try:
        app = AttendanceApp()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user. Exiting cleanly.")
    except Exception as e:
        logger.critical(f"Unhandled application exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
