"""Dialog for displaying junction properties"""

import os
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from winlink.core.models import Junction
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class PropertiesDialog(AnimatedDialog):
    """Dialog for displaying junction properties"""

    cancellation_requested = pyqtSignal()
    undo_requested = pyqtSignal(object)
    tags_changed = pyqtSignal(object)

    def __init__(
        self,
        junction: Junction,
        parent=None,
        history_manager=None,
        *,
        tag_manager=None,
        calculate_storage: bool | None = None,
    ):
        super().__init__(parent)
        self.logger = get_logger()
        self.junction = junction
        self.history_manager = history_manager
        if tag_manager is None:
            from winlink.core.tags import LinkTagManager

            tag_manager = LinkTagManager()
        self.tag_manager = tag_manager
        if calculate_storage is None:
            from winlink.core.config import get_settings

            calculate_storage = get_settings().calculate_storage_automatically
        self.calculate_storage = calculate_storage
        self._manual_recalculate = False
        self._dismissed = False

        self.init_ui()
        self.load_junction_data()

    def init_ui(self):
        from PyQt6.QtCore import Qt

        from winlink.ui.components import Panel, button_style, heading
        from winlink.ui.icons import set_label_icon

        self.setWindowTitle("Propriedades do Link")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        top = heading(layout, "Propriedades do Link")
        self.close_btn = button_style(QPushButton("Fechar"), "close")
        self.close_btn.clicked.connect(self.accept)
        top.addWidget(self.close_btn)
        panel = Panel()
        panel.content.setContentsMargins(18, 18, 18, 18)
        panel.content.setSpacing(10)
        header = QHBoxLayout()
        icon = QLabel()
        set_label_icon(icon, "folder" if self.junction.is_directory else "file", 32)
        header.addWidget(icon)
        name = QLabel(self.junction.target.name)
        name.setWordWrap(True)
        name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        name.setToolTip(self.junction.target.name)
        name.setObjectName("sectionTitle")
        header.addWidget(name, 1)
        self.status_icon = QLabel()
        header.addWidget(self.status_icon)
        self.status_label = QLabel()
        header.addWidget(self.status_label)
        panel.content.addLayout(header)
        metadata = QGridLayout()
        metadata.setHorizontalSpacing(18)
        metadata.setVerticalSpacing(6)
        self.type_label = QLabel()
        self.creator_label = QLabel()
        self.created_at_label = QLabel()
        self.size_label = QLabel()
        self.file_count_label = QLabel()
        self.folder_count_label = QLabel()
        metadata_rows = [
            ("Tipo:", self.type_label, "Tamanho total:", self.size_label),
            ("Criador:", self.creator_label, "Arquivos:", self.file_count_label),
            ("Data de criação:", self.created_at_label, "Pastas:", self.folder_count_label),
        ]
        for row, (left_title, left_value, right_title, right_value) in enumerate(metadata_rows):
            metadata.addWidget(QLabel(left_title), row, 0)
            metadata.addWidget(left_value, row, 1)
            metadata.addWidget(QLabel(right_title), row, 2)
            metadata.addWidget(right_value, row, 3)
        metadata.setColumnStretch(1, 1)
        metadata.setColumnStretch(3, 1)
        panel.content.addLayout(metadata)
        self.target_label = QPlainTextEdit()
        self.source_label = QPlainTextEdit()

        def _make_open_btn(accessible_name: str, tooltip: str, icon: str):
            """Create a compact icon-only open button matching the header style."""
            from PyQt6.QtWidgets import QToolButton

            from winlink.ui.icons import set_button_icon

            btn = QToolButton()
            btn.setObjectName("headerIcon")
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn.setAccessibleName(accessible_name)
            btn.setToolTip(tooltip)
            set_button_icon(btn, icon)
            return btn

        self.target_button = _make_open_btn(
            "Abrir Ponto de Acesso", "Abrir Ponto de Acesso no Explorer", "external"
        )
        self.target_button.clicked.connect(self.open_target)

        self.source_button = _make_open_btn(
            "Abrir Dados Físicos",
            "Abrir Dados Físicos no Explorer",
            "folder" if self.junction.is_directory else "file",
        )
        self.source_button.clicked.connect(self.open_source)

        for title, text_widget, open_btn in [
            ("Ponto de Acesso", self.target_label, self.target_button),
            ("Dados Físicos", self.source_label, self.source_button),
        ]:
            from PyQt6.QtGui import QTextOption

            text_widget.setReadOnly(True)
            text_widget.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
            text_widget.setMinimumWidth(0)
            text_widget.setObjectName("pathBlock")
            text_widget.setFixedHeight(text_widget.fontMetrics().lineSpacing() * 2 + 28)
            field_label = QLabel(title)
            field_label.setObjectName("fieldLabel")
            field_label.setBuddy(text_widget)
            panel.content.addWidget(field_label)
            path_row = QHBoxLayout()
            path_row.setSpacing(6)
            path_row.addWidget(text_widget, 1)
            path_row.addWidget(open_btn)
            panel.content.addLayout(path_row)

        self.tags_edit = QLineEdit()
        self.tags_edit.setAccessibleName("Tags do link")
        tags_label = QLabel("Tags (separadas por vírgula)")
        tags_label.setObjectName("fieldLabel")
        tags_label.setBuddy(self.tags_edit)
        panel.content.addWidget(tags_label)
        self.save_tags_btn = button_style(QPushButton("Salvar tags"), "save")
        self.save_tags_btn.clicked.connect(self.save_tags)
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        tags_row.addWidget(self.tags_edit, 1)
        tags_row.addWidget(self.save_tags_btn)
        panel.content.addLayout(tags_row)
        # Botão Recalcular desativado — comentado para fácil recuperação futura
        # self.recalculate_btn = button_style(QPushButton("Recalcular"), "refresh")
        # self.recalculate_btn.clicked.connect(self.recalculate)
        heading(panel.content, "Histórico deste link")
        self.history_label = QLabel()
        self.history_label.setObjectName("muted")
        self.history_label.setWordWrap(True)
        panel.content.addWidget(self.history_label)
        self.undo_btn = button_style(QPushButton("Reverter (Desfazer Link)"), "trash", danger=True)
        self.undo_btn.clicked.connect(self.request_undo)
        panel.content.addWidget(self.undo_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(panel)

    def request_undo(self):
        if not getattr(self, "_calculating", False):
            self.undo_requested.emit(self.junction)

    def recalculate(self):
        if not getattr(self, "_calculating", False):
            self.junction.size_bytes = None
            self._manual_recalculate = True
            self.load_junction_data()

    def save_tags(self):
        from winlink.core.tags import parse_tags

        try:
            self.tag_manager.set_tags(self.junction, parse_tags(self.tags_edit.text()))
        except (OSError, ValueError) as exc:
            self.logger.error("Could not save tags for %s: %s", self.junction.target, exc)
            QMessageBox.warning(self, "Tags", f"Não foi possível salvar as tags: {exc}")
            return
        self.tags_edit.setText(", ".join(self.junction.tags))
        self.tags_changed.emit(self.junction)

    def load_junction_data(self):
        """Load junction data into UI"""
        # Type
        self.type_label.setText(
            self.get_type_display(self.junction.junction_type, self.junction.is_directory)
        )

        # Status
        from winlink.ui.icons import status_icon
        from winlink.ui.theme import junction_status_color

        status_color = junction_status_color(self.junction.status)
        self.status_icon.setPixmap(
            status_icon(self.junction.status, status_color.name()).pixmap(16, 16)
        )
        self.status_label.setText(self.get_status_display(self.junction.status))
        self.status_label.setStyleSheet(f"color: {status_color.name()}; font-weight: bold;")

        # Creator
        creator_text = self.get_creator_display(self.junction.creator)
        self.creator_label.setText(creator_text)

        # Created at
        if self.junction.created_at:
            created_at_text = self.junction.created_at.strftime("%d/%m/%Y %H:%M")
        else:
            created_at_text = "Desconhecido"
        self.created_at_label.setText(created_at_text)

        # Paths
        self.source_label.setPlainText(str(self.junction.source.absolute()))
        self.target_label.setPlainText(str(self.junction.target.absolute()))
        self.tags_edit.setText(", ".join(self.junction.tags))

        # Statistics
        should_calculate_storage = self.calculate_storage or self._manual_recalculate
        if self.junction.size_bytes is not None:
            size_text = self.format_size(self.junction.size_bytes)
        else:
            size_text = "Desconhecido" if should_calculate_storage else "Não calculado"
        self.size_label.setText(size_text)

        from winlink.ui.operation_worker import run_operation

        counts = []
        self._calculating = True
        self.show()
        try:
            from winlink.ui.operation_worker import OperationCancelledError

            def check_cancelled():
                if self._dismissed:
                    raise OperationCancelledError("Operação cancelada")

            def collect(context):
                def boundary():
                    check_cancelled()
                    context.check_cancelled()

                context.check_cancelled()
                counts.append(count_entries(self.junction.source, cancel_check=boundary))
                if self.junction.size_bytes is None and should_calculate_storage:
                    from winlink.core.scanner import calculate_directory_size

                    self.junction.size_bytes = calculate_directory_size(
                        self.junction.source, cancel_check=boundary
                    )

            run_operation(collect, self)
            if counts and not self._dismissed:
                files, folders = counts[0]
                if self.junction.size_bytes is not None:
                    self.size_label.setText(self.format_size(self.junction.size_bytes))
                self.file_count_label.setText(str(files))
                self.folder_count_label.setText(str(folders))
        except OSError:
            if not self._dismissed:
                self.size_label.setText("Indisponível")
                self.file_count_label.setText("Indisponível")
                self.folder_count_label.setText("Indisponível")
        finally:
            self._calculating = False
            self._manual_recalculate = False
        if self._dismissed:
            return

        # History
        if self.junction.creator.value == "APP":
            self.history_label.setText(f"Criada via WinLink em {created_at_text}")
        else:
            self.history_label.setText("Criada fora do WinLink")
        if self.history_manager is not None:
            related = [
                record
                for record in self.history_manager.get_history()
                if record.target == self.junction.target
            ]
            if related:
                self.history_label.setText(
                    "\n".join(
                        f"{record.timestamp:%d/%m/%Y %H:%M} — {record.operation_type.value} "
                        f"({'Sucesso' if record.success else 'Falha'})"
                        for record in related
                    )
                )

    def update_progress(self, value, message):
        pass

    def done(self, result):
        if getattr(self, "_calculating", False):
            self.cancellation_requested.emit()
            self._dismissed = True
        super().done(result)

    def closeEvent(self, event):
        if getattr(self, "_calculating", False):
            self.cancellation_requested.emit()
            self._dismissed = True
        event.accept()

    def get_type_display(self, junction_type, is_directory: bool = True) -> str:
        """Get display text for junction type"""
        from winlink.ui.type_labels import link_type_label

        return link_type_label(junction_type, is_directory)

    def get_status_display(self, status) -> str:
        """Get display text for status"""
        from winlink.core.models import JunctionStatus

        if status == JunctionStatus.ACTIVE:
            return "Ativo"
        elif status == JunctionStatus.BROKEN:
            return "Quebrado"
        elif status == JunctionStatus.INACCESSIBLE:
            return "Inacessível"
        return str(status.value)

    def get_status_color(self, status) -> str:
        """Get color for status"""
        from winlink.ui.theme import junction_status_color

        return str(junction_status_color(status).name())

    def get_creator_display(self, creator) -> str:
        """Get display text for creator"""
        from winlink.core.models import Creator

        if creator == Creator.APP:
            return "App"
        elif creator == Creator.EXISTING:
            return "Existente"
        elif creator == Creator.MANUAL:
            return "Manual"
        return str(creator.value)

    def format_size(self, size_bytes: float) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def open_source(self):
        """Open source directory in file explorer"""
        self.open_directory(self.junction.source)

    def open_target(self):
        """Open target directory in file explorer"""
        self.open_directory(self.junction.target)

    def open_directory(self, path: Path):
        """Open directory in file explorer"""
        import os
        import subprocess

        try:
            exists = path.exists()
        except OSError:
            exists = False
        if not exists:
            QMessageBox.warning(self, "Aviso", f"O diretório não existe: {path}")
            return
        try:
            if os.name == "nt":  # Windows
                subprocess.run(["explorer", str(path.absolute())], check=False)
            else:
                # Fallback for other platforms
                import webbrowser

                webbrowser.open(str(path.absolute()))
        except (OSError, subprocess.SubprocessError) as exc:
            self.logger.error(f"Could not open {path}: {exc}")
            QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o destino: {path}")


def count_entries(source: Path, *, cancel_check=None) -> tuple[int, int]:
    """Read statistics outside the GUI thread, without following nested links."""
    if source.is_file():
        return 1, 0
    if not source.is_dir():
        raise OSError("Dados Físicos indisponíveis")
    files = folders = 0
    for root, directories, filenames in os.walk(source):
        if cancel_check is not None:
            cancel_check()
        folders += len(directories)
        directories[:] = [
            name
            for name in directories
            if not (Path(root) / name).is_symlink() and not (Path(root) / name).is_junction()
        ]
        files += len(filenames)
    return files, folders
