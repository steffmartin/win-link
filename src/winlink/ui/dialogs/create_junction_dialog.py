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
        from PyQt6.QtWidgets import QSizePolicy, QWidget

        from winlink.ui.components import Columns, Panel, TypeButton, button_style, heading
        from winlink.ui.icons import symbol_icon

        self.setWindowTitle("Criar Novo Link")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        heading(layout, "Criar Novo Link")
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        form_layout.addWidget(QLabel("Tipo de Estrutura"))
        self.type_combo = QComboBox()
        for title, kind in [
            ("Junction", JunctionType.JUNCTION),
            ("Symlink", JunctionType.SYMLINK),
            ("Hardlink", JunctionType.HARDLINK),
        ]:
            self.type_combo.addItem(title, kind)
        self.type_combo.hide()
        form_layout.addWidget(self.type_combo)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        self.file_symlink = QCheckBox()
        self.file_symlink.hide()
        self.file_symlink.toggled.connect(
            lambda: self.on_type_changed(self.type_combo.currentIndex())
        )
        form_layout.addWidget(self.file_symlink)
        cards = QGridLayout()
        cards.setSpacing(12)
        self.type_cards = []
        for n, (title, desc, icon, index, file) in enumerate(
            [
                ("Junction", "Atalho de pasta local (padrão).", "folder", 0, False),
                (
                    "Symlink (Dir)",
                    "Pasta local ou de rede. Pode exigir permissões.",
                    "folder",
                    1,
                    False,
                ),
                ("Symlink (File)", "Atalho avançado de arquivo.", "file", 1, True),
                ("Hardlink", "Nomes equivalentes do mesmo arquivo e volume.", "file", 2, False),
            ]
        ):
            button = TypeButton(title, desc, icon)
            button.clicked.connect(lambda checked=False, i=index, f=file: self.select_type(i, f))
            cards.addWidget(button, n // 2, n % 2)
            self.type_cards.append(button)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        form_layout.addLayout(cards)
        form_layout.addSpacing(8)
        self.source_edit = QLineEdit()
        self.source_edit.setObjectName("pathInput")
        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        self.source_browse_btn = button_style(QPushButton("Procurar"), "folder")
        self.source_browse_btn.clicked.connect(self.browse_source)
        self.source_label = QLabel("1. Local dos dados (Origem)")
        self.source_label.setObjectName("fieldLabel")
        self.source_label.setBuddy(self.source_edit)
        form_layout.addWidget(self.source_label)
        source_row.addWidget(self.source_edit, 1)
        source_row.addWidget(self.source_browse_btn)
        form_layout.addLayout(source_row)
        form_layout.addSpacing(8)
        self.target_edit = QLineEdit()
        self.target_edit.setObjectName("pathInput")
        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        self.target_browse_btn = button_style(QPushButton("Procurar"), "folder")
        self.target_browse_btn.clicked.connect(self.browse_target)
        self.target_label = QLabel("2. Caminho do novo link (Destino)")
        self.target_label.setObjectName("fieldLabel")
        self.target_label.setBuddy(self.target_edit)
        form_layout.addWidget(self.target_label)
        target_row.addWidget(self.target_edit, 1)
        target_row.addWidget(self.target_browse_btn)
        form_layout.addLayout(target_row)
        self.info_label = QLabel()
        self.info_label.setObjectName("muted")
        self.info_label.setWordWrap(True)
        form_layout.addWidget(self.info_label)
        self.create_btn = button_style(QPushButton("Avançar"), "arrow", primary=True)
        self.create_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.create_btn.setMinimumHeight(46)
        self.create_btn.clicked.connect(self.show_preview)
        form_layout.addWidget(self.create_btn)
        self.cancel_btn = button_style(QPushButton("Cancelar"), "close")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.hide()
        self.preview_btn = QPushButton("Prévia")
        self.preview_btn.clicked.connect(self.show_preview)
        self.preview_btn.hide()
        form_layout.addWidget(self.preview_btn)
        form_layout.addWidget(self.cancel_btn)
        form_layout.addStretch()
        preview = Panel()
        preview.setObjectName("structurePanel")
        heading(
            preview.content,
            "Prévia Estrutural",
            "Visualização dos caminhos; a confirmação fará as verificações reais.",
        )
        preview.content.addStretch()
        nodes = QHBoxLayout()
        self.structure_target = QLabel("[Destino vazio]")
        self.structure_source = QLabel("[Origem vazia]")
        for label, title, icon in [
            (self.structure_target, "PONTO DE ACESSO", "link"),
            (self.structure_source, "DADOS FÍSICOS", "folder"),
        ]:
            node = Panel()
            node.setObjectName("structureNode")
            title_label = QLabel(title)
            title_label.setObjectName("muted")
            node.content.addWidget(title_label)
            artwork = QLabel()
            artwork.setPixmap(symbol_icon(icon, "#3b82f6").pixmap(32, 32))
            if label is self.structure_source:
                self.structure_source_icon = artwork
            node.content.addWidget(artwork)
            label.setWordWrap(True)
            label.setObjectName("pathText")
            node.content.addWidget(label)
            nodes.addWidget(node, 1)
            if label is self.structure_target:
                arrow = QLabel()
                arrow.setPixmap(symbol_icon("arrow", "#60a5fa").pixmap(28, 28))
                nodes.addWidget(arrow)
        preview.content.addLayout(nodes)
        preview.content.addStretch()
        self.structure_summary = QLabel()
        self.structure_summary.setWordWrap(True)
        self.structure_summary.setObjectName("infoBanner")
        preview.content.addWidget(self.structure_summary)
        self.creation_columns = Columns(form, preview)
        layout.addWidget(self.creation_columns)
        layout.addStretch()
        self.target_edit.textChanged.connect(self.validate_inputs)
        self.source_edit.textChanged.connect(self.validate_inputs)
        self.target_edit.textChanged.connect(self.update_structure)
        self.source_edit.textChanged.connect(self.update_structure)
        self.source_browse_btn.setAccessibleName("Selecionar local dos dados")
        self.target_browse_btn.setAccessibleName("Selecionar caminho do novo link")
        self.setTabOrder(self.source_edit, self.source_browse_btn)
        self.setTabOrder(self.source_browse_btn, self.target_edit)
        self.setTabOrder(self.target_edit, self.target_browse_btn)
        self.on_type_changed(0)

    def update_structure(self):
        from winlink.ui.icons import symbol_icon

        file = self._link_type == JunctionType.HARDLINK or self.file_symlink.isChecked()
        self.structure_source_icon.setPixmap(
            symbol_icon("file" if file else "folder", "#3b82f6").pixmap(32, 32)
        )
        self.structure_target.setText(self.target_edit.text() or "[Destino vazio]")
        self.structure_source.setText(self.source_edit.text() or "[Origem vazia]")
        self.structure_summary.setText(
            "Os dois nomes representarão o mesmo arquivo, no mesmo volume."
            if self._link_type == JunctionType.HARDLINK
            else "O novo caminho permitirá acessar os dados no local indicado. A prévia confirma espaço, conflitos e preservação dos arquivos antes de executar."
        )

    def select_type(self, index, file):
        self.type_combo.setCurrentIndex(index)
        self.file_symlink.setChecked(file)
        self.on_type_changed(index)

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
            self.target_label.setText("2. Caminho do novo link (Destino)")
            self.source_label.setText("1. Local dos dados (arquivo existente)")
            self.target_edit.setPlaceholderText("Ex: C:\\Users\\steff\\document.txt")
            self.source_edit.setPlaceholderText("Ex: D:\\Cache\\document.txt")
            self.info_label.setText(
                "Escolha um arquivo de origem existente e um novo caminho para o link. "
                "Hard links exigem o mesmo volume; symlinks podem exigir Modo de Desenvolvedor ou administrador."
            )
        else:
            # Junctions and symlinks are for directories
            self.target_label.setText("2. Caminho do novo link (Destino)")
            self.source_label.setText("1. Local dos dados (Origem)")
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
        self.update_structure()
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
