"""Dialog for showing operation progress"""

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class ProgressWorker(QObject):
    """Worker for progress operations"""

    progress_updated = pyqtSignal(int, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, message
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._cancelled = False

    def cancel(self):
        """Cancel the operation"""
        self._cancelled = True
        self.cancelled.emit()

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return bool(self._cancelled)


class ProgressDialog(AnimatedDialog):
    """Dialog for showing operation progress"""

    cancellation_requested = pyqtSignal()

    def __init__(self, title: str = "Operação em Andamento", parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self._title = title
        self._was_cancelled = False
        self._finished = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle(self._title)
        self.preferred_width = 512
        self.setMinimumWidth(400)
        self.setModal(True)

        from winlink.ui.components import button_style, heading
        from winlink.ui.icons import symbol_icon

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        heading(layout, self._title)
        self.result_icon = QLabel()
        self.result_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_icon.setPixmap(symbol_icon("clock", "#3b82f6").pixmap(48, 48))
        layout.addWidget(self.result_icon)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Iniciando...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("margin: 10px 0;")
        layout.addWidget(self.status_label)

        # Details label
        self.details_label = QLabel()
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("margin: 5px 0;")
        self.details_label.setWordWrap(True)
        self.details_label.hide()
        layout.addWidget(self.details_label)

        layout.addSpacing(8)

        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = button_style(QPushButton("Interromper"), "close")
        self.cancel_btn.clicked.connect(self.cancel_operation)

        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def update_progress(self, progress: int, message: str = "", details: str = ""):
        """
        Update progress and status.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
            details: Additional details
        """
        self.progress_bar.setValue(progress)
        if message:
            self.status_label.setText(message)
        if details:
            self.details_label.setText(details)
            self.details_label.show()

    def set_operation_finished(self, success: bool, message: str = ""):
        """
        Mark operation as finished.

        Args:
            success: Whether operation succeeded
            message: Final message
        """
        from winlink.ui.icons import symbol_icon

        self.result_icon.setPixmap(
            symbol_icon(
                "check" if success else "warning" if self._was_cancelled else "error",
                "#16a34a" if success else "#d97706" if self._was_cancelled else "#ef4444",
            ).pixmap(56, 56)
        )
        self._finished = True
        self.cancel_btn.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Concluído!")
            self.cancel_btn.setText("Fechar")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.accept)
        else:
            self.status_label.setText(
                "Cancelado — dados preservados" if self._was_cancelled else "Falha na operação"
            )
            if message:
                self.details_label.setText(message)
                self.details_label.show()
            self.cancel_btn.setText("Fechar")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.reject)

    def cancel_operation(self):
        """Cancel the operation"""
        if self._finished or self._was_cancelled:
            return
        self._was_cancelled = True
        self.status_label.setText("Cancelando / preservando dados…")
        self.cancel_btn.setEnabled(False)
        self.cancellation_requested.emit()

    def was_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self._was_cancelled

    def reject(self):
        if self._finished:
            super().reject()
        else:
            self.cancel_operation()

    def accept(self):
        if self._finished:
            super().accept()

    def closeEvent(self, event):
        """Handle close event"""
        if not self._finished:
            # Still in progress
            event.ignore()
        else:
            event.accept()
