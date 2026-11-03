"""Main entry point for WinLink application"""

import sys

from PyQt6.QtWidgets import QApplication

from winlink.core.config import get_settings
from winlink.ui.main_window import MainWindow
from winlink.utils.logger import setup_logger


def main():
    """Main application entry point"""
    # Setup configuration
    settings = get_settings()

    # Setup logging
    logger = setup_logger(
        name="winlink",
        log_file=settings.log_file,
        log_to_console=settings.log_to_console,
    )
    logger.info("WinLink starting...")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("WinLink")
    app.setApplicationVersion("0.1.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("WinLink window shown")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
