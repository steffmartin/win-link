"""Dialog for displaying junction properties"""

import os
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from winlink.core.models import Junction
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class PropertiesDialog(AnimatedDialog):
    """Dialog for displaying junction properties"""

    cancellation_requested = pyqtSignal()
    undo_requested = pyqtSignal(object)

    def __init__(self, junction: Junction, parent=None, history_manager=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.junction = junction
        self.history_manager = history_manager

        self.init_ui()
        self.load_junction_data()

    def init_ui(self):
        from PyQt6.QtCore import Qt

        from winlink.ui.components import ActionRow, Panel, button_style, field, heading
        from winlink.ui.icons import symbol_icon

        self.setWindowTitle("Propriedades do Link")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        top = heading(layout, "Propriedades do Link")
        self.close_btn = button_style(QPushButton("Fechar"), "close")
        self.close_btn.clicked.connect(self.accept)
        top.addWidget(self.close_btn)
        panel = Panel()
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(
            symbol_icon("folder" if self.junction.is_directory else "file", "#3b82f6").pixmap(
                32, 32
            )
        )
        header.addWidget(icon)
        name = QLabel(self.junction.target.name)
        name.setWordWrap(True)
        name.setObjectName("sectionTitle")
        header.addWidget(name, 1)
        self.status_label = QLabel()
        header.addWidget(self.status_label)
        panel.content.addLayout(header)
        metadata = QFormLayout()
        metadata.setVerticalSpacing(12)
        self.type_label = QLabel()
        self.creator_label = QLabel()
        self.created_at_label = QLabel()
        metadata.addRow("Tipo:", self.type_label)
        metadata.addRow("Criador:", self.creator_label)
        metadata.addRow("Data de criação:", self.created_at_label)
        panel.content.addLayout(metadata)
        self.target_label = QLabel()
        self.source_label = QLabel()
        for title, label in [
            ("Ponto de Acesso (Destino)", self.target_label),
            ("Alvo / Local dos dados (Origem)", self.source_label),
        ]:
            label.setWordWrap(True)
            label.setObjectName("pathBlock")
            field(panel.content, title, label)
        statistics = QFormLayout()
        statistics.setVerticalSpacing(12)
        self.size_label = QLabel()
        self.file_count_label = QLabel()
        self.folder_count_label = QLabel()
        statistics.addRow("Tamanho total:", self.size_label)
        statistics.addRow("Arquivos:", self.file_count_label)
        statistics.addRow("Pastas:", self.folder_count_label)
        panel.content.addLayout(statistics)
        self.source_button = button_style(QPushButton("Abrir origem"), "folder")
        self.source_button.clicked.connect(self.open_source)
        self.target_button = button_style(QPushButton("Abrir destino"), "external")
        self.target_button.clicked.connect(self.open_target)
        self.recalculate_btn = button_style(QPushButton("Recalcular"), "refresh")
        self.recalculate_btn.clicked.connect(self.recalculate)
        panel.content.addWidget(
            ActionRow([self.source_button, self.target_button, self.recalculate_btn])
        )
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
            self.load_junction_data()

    def load_junction_data(self):
        """Load junction data into UI"""
        # Type
        type_text = self.get_type_display(self.junction.junction_type)
        if self.junction.junction_type.value == "SYMLINK":
            type_text += " (diretório)" if self.junction.is_directory else " (arquivo)"
        self.type_label.setText(type_text)

        # Status
        status_text = self.get_status_display(self.junction.status)
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"color: {self.get_status_color(self.junction.status)}; font-weight: bold;"
        )

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
        self.source_label.setText(str(self.junction.source.absolute()))
        self.target_label.setText(str(self.junction.target.absolute()))

        # Statistics
        if self.junction.size_bytes is not None:
            size_text = self.format_size(self.junction.size_bytes)
        else:
            size_text = "Desconhecido"
        self.size_label.setText(size_text)

        from winlink.ui.operation_worker import run_operation

        counts = []
        self._calculating = True
        self.show()
        try:

            def collect(context):
                counts.append(count_entries(self.junction.source))
                if self.junction.size_bytes is None:
                    from winlink.core.scanner import calculate_directory_size

                    self.junction.size_bytes = calculate_directory_size(self.junction.source)

            run_operation(collect, self)
            files, folders = counts[0]
            if self.junction.size_bytes is not None:
                self.size_label.setText(self.format_size(self.junction.size_bytes))
            self.file_count_label.setText(str(files))
            self.folder_count_label.setText(str(folders))
        except OSError:
            self.size_label.setText("Indisponível")
            self.file_count_label.setText("Indisponível")
            self.folder_count_label.setText("Indisponível")
        finally:
            self._calculating = False

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
        if not getattr(self, "_calculating", False):
            super().done(result)

    def closeEvent(self, event):
        if getattr(self, "_calculating", False):
            event.ignore()
        else:
            event.accept()

    def get_type_display(self, junction_type) -> str:
        """Get display text for junction type"""
        from winlink.core.models import JunctionType

        if junction_type == JunctionType.JUNCTION:
            return "Junção (Junction)"
        elif junction_type == JunctionType.SYMLINK:
            return "Link Simbólico (Symlink)"
        elif junction_type == JunctionType.HARDLINK:
            return "Hard Link"
        return str(junction_type.value)

    def get_status_display(self, status) -> str:
        """Get display text for status"""
        from winlink.core.models import JunctionStatus

        if status == JunctionStatus.ACTIVE:
            return "✓ Ativo"
        elif status == JunctionStatus.BROKEN:
            return "⚠ Quebrado"
        elif status == JunctionStatus.INACCESSIBLE:
            return "🔒 Inacessível"
        return str(status.value)

    def get_status_color(self, status) -> str:
        """Get color for status"""
        from winlink.core.models import JunctionStatus

        if status == JunctionStatus.ACTIVE:
            return "#107C10"  # Green
        elif status == JunctionStatus.BROKEN:
            return "#9B8F06"  # Yellow/Orange
        elif status == JunctionStatus.INACCESSIBLE:
            return "#C42B1A"  # Red
        return "#1A1A1A"

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

        if path.exists():
            if os.name == "nt":  # Windows
                subprocess.run(["explorer", str(path.absolute())])
            else:
                # Fallback for other platforms
                import webbrowser

                webbrowser.open(str(path.absolute()))
        else:
            QMessageBox.warning(self, "Aviso", f"O diretório não existe: {path}")


def count_entries(source: Path) -> tuple[int, int]:
    """Read statistics outside the GUI thread, without following nested links."""
    if source.is_file():
        return 1, 0
    if not source.is_dir():
        raise OSError("Origem indisponível")
    files = folders = 0
    for root, directories, filenames in os.walk(source):
        folders += len(directories)
        directories[:] = [
            name
            for name in directories
            if not (Path(root) / name).is_symlink() and not (Path(root) / name).is_junction()
        ]
        files += len(filenames)
    return files, folders
