"""Dialog for creating a new junction"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from winlink.core.models import JunctionType
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class CreateJunctionDialog(AnimatedDialog):
    """Dialog for creating a new junction"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()

        self._source_path: Path | None = None
        self._target_path: Path | None = None
        self._link_type: JunctionType = JunctionType.JUNCTION

        self.init_ui()
        from winlink.core.config import get_settings

        preference = getattr(getattr(parent, "settings", None), "default_link_type", None)
        preference = preference or get_settings().default_link_type
        self.type_combo.setCurrentIndex(
            {"junction": 0, "symlink_dir": 1, "symlink_file": 1, "hardlink": 2}[preference]
        )
        self.file_symlink.setChecked(preference == "symlink_file")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Criar Novo Link")
        self.setMinimumWidth(600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel("Criar Novo Link")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        # Grid layout for form
        form_layout = QGridLayout()

        # Link type selector
        type_label = QLabel("Tipo de Link:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("Junction (NTFS)", JunctionType.JUNCTION)
        self.type_combo.addItem("Symlink (Symbolic Link)", JunctionType.SYMLINK)
        self.type_combo.addItem("Hard Link (Arquivo)", JunctionType.HARDLINK)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)

        type_label.hide()
        self.type_combo.hide()
        form_layout.addWidget(type_label, 0, 0)
        form_layout.addWidget(self.type_combo, 0, 1, 1, 2)

        # Target (destination) field
        self.target_label = QLabel("Caminho do novo link:")
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Ex: C:\\Users\\steff\\.vscode")
        self.target_browse_btn = QPushButton("...")
        self.target_browse_btn.setMaximumWidth(40)
        self.target_browse_btn.clicked.connect(self.browse_target)

        form_layout.addWidget(self.target_label, 3, 0, 1, 3)
        form_layout.addWidget(self.target_edit, 4, 0, 1, 2)
        form_layout.addWidget(self.target_browse_btn, 4, 2)

        # Source field
        self.source_label = QLabel("Local dos dados:")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Ex: D:\\Cache\\.vscode")
        self.source_browse_btn = QPushButton("...")
        self.source_browse_btn.setMaximumWidth(40)
        self.source_browse_btn.clicked.connect(self.browse_source)

        form_layout.addWidget(self.source_label, 1, 0, 1, 3)
        form_layout.addWidget(self.source_edit, 2, 0, 1, 2)
        form_layout.addWidget(self.source_browse_btn, 2, 2)

        cards = QHBoxLayout()
        self.type_cards = []
        for title, index, file in [
            ("Junction", 0, False),
            ("Symlink (Dir)", 1, False),
            ("Symlink (File)", 1, True),
            ("Hardlink", 2, False),
        ]:
            button = QPushButton(title)
            button.setMinimumHeight(64)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index, f=file: self.select_type(i, f))
            cards.addWidget(button)
            self.type_cards.append(button)
        layout.addLayout(cards)
        layout.addLayout(form_layout)
        self.file_symlink = QCheckBox("Link simbólico de arquivo existente")
        self.file_symlink.toggled.connect(
            lambda: self.on_type_changed(self.type_combo.currentIndex())
        )
        layout.addWidget(self.file_symlink)

        # Info label
        self.info_label = QLabel(
            "ℹ️ Se o destino já existir, os arquivos serão copiados para a origem antes de criar a junção."
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-style: italic; margin: 10px 0;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.preview_btn = QPushButton("Prévia")
        self.preview_btn.clicked.connect(self.show_preview)
        self.preview_btn.setEnabled(False)

        self.create_btn = QPushButton("Criar Link")
        self.create_btn.clicked.connect(self.show_preview)
        self.create_btn.setEnabled(False)
        self.create_btn.setProperty("primary", True)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

        self.source_label.setBuddy(self.source_edit)
        self.target_label.setBuddy(self.target_edit)
        self.source_browse_btn.setAccessibleName("Selecionar local dos dados")
        self.target_browse_btn.setAccessibleName("Selecionar caminho do novo link")
        self.setTabOrder(self.source_edit, self.source_browse_btn)
        self.setTabOrder(self.source_browse_btn, self.target_edit)
        self.setTabOrder(self.target_edit, self.target_browse_btn)
        # Connect text changed signals
        self.target_edit.textChanged.connect(self.validate_inputs)
        self.source_edit.textChanged.connect(self.validate_inputs)

        # Initialize for default type
        self.on_type_changed(0)

    def select_type(self, index, file):
        self.type_combo.setCurrentIndex(index)
        self.file_symlink.setChecked(file)

    def on_type_changed(self, index: int):
        """Handle link type selection change"""
        link_type = self.type_combo.itemData(index)
        self._link_type = link_type

        self.file_symlink.hide()
        if link_type != JunctionType.SYMLINK:
            self.file_symlink.setChecked(False)
        if link_type == JunctionType.HARDLINK or (
            link_type == JunctionType.SYMLINK and self.file_symlink.isChecked()
        ):
            # Hard links are for files only
            self.target_label.setText("Caminho do novo link:")
            self.source_label.setText("Local dos dados (arquivo existente):")
            self.target_edit.setPlaceholderText("Ex: C:\\Users\\steff\\document.txt")
            self.source_edit.setPlaceholderText("Ex: D:\\Cache\\document.txt")
            self.info_label.setText(
                "Escolha um arquivo de origem existente e um novo caminho para o link. "
                "Hard links exigem o mesmo volume; symlinks podem exigir Modo de Desenvolvedor ou administrador."
            )
        else:
            # Junctions and symlinks are for directories
            self.target_label.setText("Caminho do novo link:")
            self.source_label.setText("Local dos dados:")
            self.target_edit.setPlaceholderText("Ex: C:\\Users\\steff\\.vscode")
            self.source_edit.setPlaceholderText("Ex: D:\\Cache\\.vscode")
            self.info_label.setText(
                "ℹ️ Se o destino já existir, os arquivos serão copiados para a origem antes de criar o link."
            )

        for card_index, card in enumerate(self.type_cards):
            selected = (
                (2 if self.file_symlink.isChecked() else 1)
                if link_type == JunctionType.SYMLINK
                else (3 if link_type == JunctionType.HARDLINK else 0)
            )
            card.setChecked(card_index == selected)
        self.validate_inputs()

    def browse_target(self):
        """Browse for target directory or file"""
        if self._link_type == JunctionType.HARDLINK or self.file_symlink.isChecked():
            # Browse for file
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Novo caminho do link", str(Path.home())
            )
            if file_path:
                self.target_edit.setText(file_path)
        else:
            # Browse for directory
            directory = QFileDialog.getExistingDirectory(
                self, "Selecionar Destino", str(Path.home())
            )
            if directory:
                self.target_edit.setText(directory)

    def browse_source(self):
        """Browse for source directory or file"""
        if self._link_type == JunctionType.HARDLINK or self.file_symlink.isChecked():
            # Browse for file
            file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Origem", str(Path.home()))
            if file_path:
                self.source_edit.setText(file_path)
        else:
            # Browse for directory
            directory = QFileDialog.getExistingDirectory(
                self, "Selecionar Origem", str(Path.home())
            )
            if directory:
                self.source_edit.setText(directory)

    def validate_inputs(self):
        """Validate input fields and enable/disable buttons"""
        target_text = self.target_edit.text().strip()
        source_text = self.source_edit.text().strip()

        is_valid = bool(
            target_text
            and source_text
            and Path(target_text).is_absolute()
            and Path(source_text).is_absolute()
            and Path(target_text) != Path(source_text)
        )

        # For hard links, check if source exists (it must exist)
        if (self._link_type == JunctionType.HARDLINK or self.file_symlink.isChecked()) and is_valid:
            source_path = Path(source_text)
            if not source_path.exists() or not source_path.is_file():
                is_valid = False

        self.preview_btn.setEnabled(is_valid)
        self.create_btn.setEnabled(is_valid)

    def show_preview(self):
        """Show preview dialog with operation details"""
        from winlink.ui.dialogs.preview_dialog import PreviewDialog

        target = Path(self.target_edit.text().strip())
        source = Path(self.source_edit.text().strip())

        dialog = PreviewDialog(target, source, self, link_type=self._link_type)
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

    def get_link_type(self) -> JunctionType:
        """Get link type"""
        return self._link_type

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
