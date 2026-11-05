"""Main entry point for WinLink application"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from winlink.core.config import get_settings
from winlink.ui.main_window import MainWindow
from winlink.utils.logger import setup_logger


def main():
    """Main application entry point"""
    smoke_output = None
    if "--smoke-test" in sys.argv:
        from pathlib import Path

        smoke_output = Path(sys.argv[sys.argv.index("--smoke-test") + 1])

    # Setup configuration
    settings = get_settings()

    # Setup logging
    logger = setup_logger(
        name="winlink",
        level=getattr(logging, settings.log_level, logging.INFO),
        log_file=settings.log_file,
        log_to_console=settings.log_to_console,
    )
    logger.info("WinLink starting...")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("WinLink")
    app.setApplicationVersion("0.1.2")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("WinLink window shown")

    if smoke_output is not None:
        import json

        from PyQt6.QtCore import QTimer

        def finish_smoke():
            if window.scan_worker is not None and window.scan_worker.isRunning():
                QTimer.singleShot(50, finish_smoke)
                return
            window.grab().save(str(smoke_output.with_suffix(".png")))
            smoke_output.write_text(
                json.dumps(
                    {
                        "frozen": bool(getattr(sys, "frozen", False)),
                        "window": window.windowTitle(),
                        "icon_loaded": not window.windowIcon().isNull(),
                        "rows": window.junction_model.rowCount(),
                        "navigation_icons": all(
                            not window.navigation.item(i).icon().isNull() for i in range(4)
                        ),
                        "creation_icon": not window.create_page.create_btn.icon().isNull(),
                        "status": window.status_bar.currentMessage(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            app.quit()

        QTimer.singleShot(100, finish_smoke)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
