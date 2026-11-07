"""Main entry point for WinLink application"""

import hashlib
import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from winlink.core.config import get_settings, settings_path
from winlink.ui.main_window import MainWindow
from winlink.utils.logger import setup_logger


def _instance_name() -> str:
    """Scope the single-instance channel to this user's WinLink data folder."""
    scope = hashlib.sha1(str(settings_path().parent).lower().encode()).hexdigest()[:12]
    return f"WinLink-{scope}"


def _acquire_instance(name: str):
    """Return a QLocalServer when this process owns the instance, 'secondary' when
    another instance must be activated instead, or None when unavailable."""
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket

    def activate_remote() -> bool:
        socket = QLocalSocket()
        socket.connectToServer(name)
        if not socket.waitForConnected(400):
            return False
        socket.write(b"activate")
        socket.flush()
        socket.waitForBytesWritten(400)
        socket.disconnectFromServer()
        return True

    if activate_remote():
        return "secondary"

    server = QLocalServer()
    if server.listen(name):
        return server
    # Stale socket from an instance that exited unexpectedly.
    QLocalServer.removeServer(name)
    if server.listen(name):
        return server
    if activate_remote():
        return "secondary"
    return None


def _raise_window(window: MainWindow) -> None:
    """Restore and focus the existing window for a secondary launch."""
    state = window.windowState()
    if state & Qt.WindowState.WindowMinimized:
        window.setWindowState(state & ~Qt.WindowState.WindowMinimized)
    window.show()
    window.raise_()
    window.activateWindow()


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
    app.setApplicationVersion("0.1.8")

    instance_server = None
    if "--smoke-test" not in sys.argv:
        instance = _acquire_instance(_instance_name())
        if instance == "secondary":
            logger.info("Another WinLink instance is running; activating it.")
            return
        instance_server = instance

    # Create and show main window
    window = MainWindow()
    window.show()

    if instance_server is not None:

        def on_connection():
            while instance_server.hasPendingConnections():
                connection = instance_server.nextPendingConnection()
                connection.disconnected.connect(connection.deleteLater)
            _raise_window(window)

        instance_server.newConnection.connect(on_connection)
        if instance_server.hasPendingConnections():
            on_connection()

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
