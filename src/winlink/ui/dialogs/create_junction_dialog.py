"""Dialog for creating a new junction"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from winlink.utils.logger import get_logger


class CreateJunctionDialog(QDialog):
    """Dialog for creating a new junction"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()

        self._source_path: Path | None = None
        self._target_path: Path | None = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Criar Nova Junção")
        self.setMinimumWidth(600)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Grid layout for form
        form_layout = QGridLayout()

        # Target (destination) field
        target_label = QLabel("Destino (pasta que será linkada):")
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Ex: C:\\Users\\steff\\.vscode")
        self.target_browse_btn = QPushButton("...")
        self.target_browse_btn.setMaximumWidth(40)
        self.target_browse_btn.clicked.connect(self.browse_target)

        form_layout.addWidget(target_label, 0, 0, 1, 3)
        form_layout.addWidget(self.target_edit, 1, 0, 1, 2)
        form_layout.addWidget(self.target_browse_btn, 1, 2)

        # Source field
        source_label = QLabel("Origem (onde os arquivos ficarão):")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Ex: D:\\Cache\\.vscode")
        self.source_browse_btn = QPushButton("...")
        self.source_browse_btn.setMaximumWidth(40)
        self.source_browse_btn.clicked.connect(self.browse_source)

        form_layout.addWidget(source_label, 2, 0, 1, 3)
        form_layout.addWidget(self.source_edit, 3, 0, 1, 2)
        form_layout.addWidget(self.source_browse_btn, 3, 2)

        layout.addLayout(form_layout)

        # Info label
        info_label = QLabel(
            "ℹ️ Se o destino já existir, os arquivos serão copiados para a origem antes de criar a junção."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #5C5C5C; font-style: italic; margin: 10px 0;")
        layout.addWidget(info_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.preview_btn = QPushButton("Prévia")
        self.preview_btn.clicked.connect(self.show_preview)
        self.preview_btn.setEnabled(False)

        self.create_btn = QPushButton("Criar Junção")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setEnabled(False)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

        # Connect text changed signals
        self.target_edit.textChanged.connect(self.validate_inputs)
        self.source_edit.textChanged.connect(self.validate_inputs)

    def browse_target(self):
        """Browse for target directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Destino", str(Path.home())
        )
        if directory:
            self.target_edit.setText(directory)

    def browse_source(self):
        """Browse for source directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Origem", str(Path.home())
        )
        if directory:
            self.source_edit.setText(directory)

    def validate_inputs(self):
        """Validate input fields and enable/disable buttons"""
        target_text = self.target_edit.text().strip()
        source_text = self.source_edit.text().strip()

        is_valid = bool(target_text and source_text)

        # Additional validation could be added here
        # For now, just check if both fields are non-empty

        self.preview_btn.setEnabled(is_valid)
        self.create_btn.setEnabled(is_valid)

    def show_preview(self):
        """Show preview dialog with operation details"""
        from winlink.ui.dialogs.preview_dialog import PreviewDialog

        target = Path(self.target_edit.text().strip())
        source = Path(self.source_edit.text().strip())

        dialog = PreviewDialog(target, source, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User confirmed preview, proceed with creation
            self.accept()

    def get_target_path(self) -> Path | None:
        """Get target path"""
        target_text = self.target_edit.text().strip()
        return Path(target_text) if target_text else None

    def get_source_path(self) -> Path | None:
        """Get source path"""
        source_text = self.source_edit.text().strip()
        return Path(source_text) if source_text else None

    def accept(self):
        """Override accept to validate before closing"""
        target = self.get_target_path()
        source = self.get_source_path()

        if not target or not source:
            QMessageBox.warning(self, "Aviso", "Preencha ambos os campos (origem e destino).")
            return

        # Validate paths are different
        if target == source:
            QMessageBox.warning(self, "Aviso", "Origem e destino não podem ser iguais.")
            return

        # Validate paths are absolute
        if not target.is_absolute():
            QMessageBox.warning(self, "Aviso", "O destino deve ser um caminho absoluto.")
            return

        if not source.is_absolute():
            QMessageBox.warning(self, "Aviso", "A origem deve ser um caminho absoluto.")
            return

        self.logger.info(f"Creating junction: {target} -> {source}")
        super().accept()
