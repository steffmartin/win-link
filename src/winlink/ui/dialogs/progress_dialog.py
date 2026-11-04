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
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

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
        layout.addWidget(self.details_label)

        layout.addStretch()

        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
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

    def set_operation_finished(self, success: bool, message: str = ""):
        """
        Mark operation as finished.

        Args:
            success: Whether operation succeeded
            message: Final message
        """
        self._finished = True
        self.cancel_btn.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Concluído!")
            self.cancel_btn.setText("Fechar")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.accept)
        else:
            self.status_label.setText("Erro")
            if message:
                self.details_label.setText(message)
            self.cancel_btn.setText("Fechar")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.reject)

    def cancel_operation(self):
        """Cancel the operation"""
        if self._finished or self._was_cancelled:
            return
        self._was_cancelled = True
        self.status_label.setText("Cancelando...")
        self.cancel_btn.setEnabled(False)
        self.cancellation_requested.emit()

    def was_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self._was_cancelled

    def closeEvent(self, event):
        """Handle close event"""
        if not self._finished:
            # Still in progress
            event.ignore()
        else:
            event.accept()
