"""Dialog for previewing junction creation operation"""

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class PreviewDialog(AnimatedDialog):
    """Dialog for previewing junction creation operation"""

    cancellation_requested = pyqtSignal()

    def __init__(self, target: Path, source: Path, parent=None, link_type=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.target = target
        self.source = source
        self.link_type = link_type

        self.init_ui()
        self.calculate_preview()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Prévia da Operação")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("Calculando prévia...")
        layout.addWidget(self.preview_text)

        # Space info
        self.space_label = QLabel()
        self.space_label.setStyleSheet("margin: 10px 0;")
        layout.addWidget(self.space_label)

        # Warning label
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #9B8F06; margin: 10px 0;")
        layout.addWidget(self.warning_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("Confirmar e Criar")
        self.confirm_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

    def calculate_preview(self):
        """Compute the preview off the UI thread and apply its result on the UI thread."""
        from winlink.ui.operation_worker import run_operation

        self.confirm_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self._calculating = True
        self.show()
        result = []
        try:
            run_operation(
                lambda context: result.append(
                    build_preview(self.target, self.source)
                    if self.link_type is None
                    else build_preview(self.target, self.source, self.link_type)
                ),
                self,
            )
            text, valid = result[0]
            self.preview_text.setPlainText(text)
            self.confirm_btn.setEnabled(valid)
        except Exception as exc:
            self.preview_text.setPlainText(str(exc))
        finally:
            self._calculating = False
            self.cancel_btn.setEnabled(True)

    def update_progress(self, value, message):
        self.space_label.setText(message)

    def reject(self):
        if not getattr(self, "_calculating", False):
            super().reject()

    def closeEvent(self, event):
        if getattr(self, "_calculating", False):
            event.ignore()
        else:
            event.accept()

    @staticmethod
    def format_size(size_bytes: float) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


def build_preview(target: Path, source: Path, link_type=None) -> tuple[str, bool]:
    """Collect preview information without accessing widgets."""
    logger = get_logger()
    from winlink.core.models import JunctionType
    from winlink.core.validators import validate_junction_creation

    if link_type is None:
        link_type = JunctionType.JUNCTION

    valid = False
    validation = validate_junction_creation(source, target, link_type)
    if not validation.is_valid:
        return "\n".join(validation.errors), False
    valid = True
    preview_lines = []
    preview_lines.append("O que será feito:")
    preview_lines.append("")

    # Check if target exists
    target_exists = target.exists()
    source_exists = source.exists()

    if link_type == JunctionType.SYMLINK and source.is_file():
        return (
            f"Criar link simbólico de arquivo: {target} -> {source}\nO arquivo original será preservado.",
            True,
        )

    # Handle hard links differently
    if link_type == JunctionType.HARDLINK:
        if not source_exists:
            return "⚠️ O arquivo de origem deve existir para criar hard links.", False

        if target_exists:
            return (
                "⚠️ O destino já existe. Hard links não podem substituir arquivos existentes.",
                False,
            )

        preview_lines.append(f"✓ Criar hard link: {target} -> {source}")
        preview_lines.append("")
        preview_lines.append("ℹ️ Ambos caminhos apontarão para os mesmos dados no disco.")
        preview_lines.append("ℹ️ Alterações em um caminho serão refletidas no outro.")
        preview_lines.append("ℹ️ Hard links funcionam apenas no mesmo volume.")

        return "\n".join(preview_lines), valid

    # Junctions and symlinks (directories)
    if source_exists:
        preview_lines.append(f"✓ Diretório de origem já existe: {source}")
    else:
        preview_lines.append(f"✓ Criar diretório de origem: {source}")

    if target_exists:
        # Target exists, need to copy files
        from winlink.core.file_ops import (
            calculate_directory_size_recursive,
            get_available_disk_space,
        )

        try:
            size = calculate_directory_size_recursive(target)
            size_str = PreviewDialog.format_size(size)

            preview_lines.append(f"✓ Copiar arquivos de {target}")
            preview_lines.append(f"  para {source} ({size_str})")
            preview_lines.append(f"✓ Remover {target}")

            # Check disk space
            disk_path = source
            while not disk_path.exists() and disk_path != disk_path.parent:
                disk_path = disk_path.parent
            available = get_available_disk_space(disk_path)
            if available >= size:
                available_str = PreviewDialog.format_size(available)
                preview_lines.append("")
                preview_lines.append(f"Espaço necessário: {size_str}")
                preview_lines.append(f"Espaço disponível: {available_str}")
            else:
                preview_lines.append("")
                preview_lines.append("⚠️ Espaço insuficiente no disco!")

                valid = False
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")
            preview_lines.append(f"⚠️ Erro ao calcular tamanho: {e}")
            valid = False
    else:
        preview_lines.append(f"✓ Criar diretório de origem vazio: {source}")
        preview_lines.append(
            f"✓ Criar {'symlink' if link_type == JunctionType.SYMLINK else 'junção'}: {target} -> {source}"
        )

    preview_lines.append("")
    preview_lines.append(
        f"✓ Criar {'symlink' if link_type == JunctionType.SYMLINK else 'junção'}: {target} -> {source}"
    )

    # Check for nested junctions
    from winlink.core.scanner import scan_directory

    if source_exists:
        try:
            scan_result = scan_directory(source, recursive=True)

            # scan_directory returns a list of Junction objects
            if isinstance(scan_result, list) and scan_result:
                preview_lines.append("")
                preview_lines.append("⚠️ Aviso: A pasta de origem contém junções:")

                for junction in scan_result:
                    preview_lines.append(f"   • {junction.target.name} -> {junction.source}")

                preview_lines.append("")
                preview_lines.append(
                    "   Windows redirecionará corretamente, mas isso pode causar confusão."
                )
                preview_lines.append("   Considere usar as junções originais diretamente.")
        except Exception as e:
            logger.warning(f"Error scanning for nested junctions: {e}")

    # Check for processes blocking files
    from winlink.core.process_manager import get_processes_using_directory

    if target_exists:
        try:
            processes = get_processes_using_directory(target)
            if processes:
                preview_lines.append("")
                preview_lines.append("⚠️ Certifique-se de fechar os seguintes processos:")
                for proc in processes:
                    preview_lines.append(f"   • {proc}")
        except Exception as e:
            logger.warning(f"Error checking for blocking processes: {e}")

    return "\n".join(preview_lines), valid
