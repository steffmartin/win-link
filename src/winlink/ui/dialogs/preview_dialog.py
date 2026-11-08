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

    def __init__(
        self,
        target: Path,
        source: Path,
        parent=None,
        link_type=None,
        *,
        is_directory: bool | None = None,
        calculate_storage: bool | None = None,
    ):
        super().__init__(parent)
        self.logger = get_logger()
        self.target = target
        self.source = source
        self.link_type = link_type
        self.is_directory = is_directory
        if calculate_storage is None:
            from winlink.core.config import get_settings

            calculate_storage = get_settings().calculate_storage_automatically
        self.calculate_storage = calculate_storage

        self.init_ui()
        self.calculate_preview()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Prévia da Operação")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)

        from winlink.ui.components import button_style, heading

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        heading(
            layout,
            "Confirmar Criação de Link",
            "Revise os caminhos e as etapas antes de iniciar.",
            icon="shield",
        )

        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(240)
        self.preview_text.setPlainText("Calculando prévia...")
        layout.addWidget(self.preview_text)
        info_row = QHBoxLayout()
        from winlink.ui.icons import set_label_icon

        info_icon = QLabel()
        set_label_icon(info_icon, "info", 18)
        info_icon.setStyleSheet("background: transparent;")
        info_row.addWidget(info_icon)
        info_text = QLabel("Confira os dois caminhos antes de confirmar.")
        info_text.setWordWrap(True)
        info_row.addWidget(info_text, 1)
        layout.addLayout(info_row)

        # Space info
        self.space_label = QLabel()
        self.space_label.setObjectName("spaceLabel")
        self.space_label.hide()
        layout.addWidget(self.space_label)

        # Warning label
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setObjectName("warningText")
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = button_style(QPushButton("Cancelar"), "close")
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = button_style(QPushButton("Confirmar e Iniciar"), "check", primary=True)
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
                    build_preview(
                        self.target,
                        self.source,
                        is_directory=self.is_directory,
                        calculate_storage=self.calculate_storage,
                    )
                    if self.link_type is None
                    else build_preview(
                        self.target,
                        self.source,
                        self.link_type,
                        is_directory=self.is_directory,
                        calculate_storage=self.calculate_storage,
                    )
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
        self.space_label.setVisible(bool(message))

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


def build_preview(
    target: Path,
    source: Path,
    link_type=None,
    *,
    is_directory: bool | None = None,
    calculate_storage: bool | None = None,
) -> tuple[str, bool]:
    """Collect preview information without accessing widgets."""
    logger = get_logger()
    from winlink.core.config import get_settings
    from winlink.core.models import JunctionType
    from winlink.core.validators import validate_junction_creation

    if link_type is None:
        link_type = JunctionType.JUNCTION
    if calculate_storage is None:
        calculate_storage = get_settings().calculate_storage_automatically

    valid = False
    validation = validate_junction_creation(
        source,
        target,
        link_type,
        is_directory=is_directory,
        calculate_storage=calculate_storage,
    )
    if not validation.is_valid:
        return "\n".join(validation.errors), False
    valid = True
    preview_lines = []
    preview_lines.append(f"Ponto de Acesso: {target}\nDados Físicos: {source}\n")
    preview_lines.append("O que será feito:")
    preview_lines.append("")

    # Check if target exists
    target_exists = target.exists()
    source_exists = source.exists()

    if link_type == JunctionType.SYMLINK and (
        is_directory is False or (is_directory is None and source.is_file())
    ):
        from winlink.ui.type_labels import link_type_label

        return (
            f"Ponto de Acesso: {target}\nDados Físicos: {source}\nCriar {link_type_label(link_type, False)}: {target} -> {source}\nO arquivo original será preservado.",
            True,
        )

    # Handle hard links differently
    if link_type == JunctionType.HARDLINK:
        if not source_exists:
            return "⚠️ O arquivo de Dados Físicos deve existir para criar hard links.", False

        if target_exists:
            return (
                "⚠️ O Ponto de Acesso já existe. Hard links não podem substituir arquivos existentes.",
                False,
            )

        preview_lines.append(f"✓ Criar hard link: {target} -> {source}")
        preview_lines.append("")
        preview_lines.append("Ambos caminhos apontarão para os mesmos dados no disco.")
        preview_lines.append("Alterações em um caminho serão refletidas no outro.")
        preview_lines.append("Hard links funcionam apenas no mesmo volume.")

        return "\n".join(preview_lines), valid

    # Junctions and symlinks (directories)
    if source_exists:
        preview_lines.append(f"Dados Físicos já existentes: {source}")
    else:
        preview_lines.append(f"Criar pasta de Dados Físicos: {source}")

    if target_exists:
        preview_lines.append(f"Ponto de Acesso contém a pasta a migrar: {target}")
        preview_lines.append(f"✓ Copiar arquivos de {target}")
        if calculate_storage:
            from winlink.core.file_ops import (
                calculate_directory_size_recursive,
                get_available_disk_space,
            )

            try:
                size = calculate_directory_size_recursive(target)
                size_str = PreviewDialog.format_size(size)
                preview_lines[-1] += f"\n  para {source} ({size_str})"
                disk_path = source
                while not disk_path.exists() and disk_path != disk_path.parent:
                    disk_path = disk_path.parent
                available = get_available_disk_space(disk_path)
                preview_lines.append("")
                if available >= size:
                    available_str = PreviewDialog.format_size(available)
                    preview_lines.append(f"Espaço necessário: {size_str}")
                    preview_lines.append(f"Espaço disponível: {available_str}")
                else:
                    preview_lines.append("⚠️ Espaço insuficiente no disco!")
                    valid = False
            except Exception as e:
                logger.error(f"Error calculating directory size: {e}")
                preview_lines.append(f"⚠️ Erro ao calcular tamanho: {e}")
                valid = False
        else:
            preview_lines.append("  Armazenamento não calculado automaticamente.")
            preview_lines.append(f"  para {source}")
        preview_lines.append(
            f"Remover a pasta em {target} somente após preservar os arquivos em {source}"
        )
    else:
        preview_lines.append(f"Ponto de Acesso ainda não existe: {target}")

    preview_lines.append("")
    from winlink.ui.type_labels import link_type_label

    preview_lines.append(
        f"✓ Criar {link_type_label(link_type, is_directory is not False)}: {target} -> {source}"
    )

    # Check for nested junctions
    from winlink.core.config import get_settings
    from winlink.core.scanner import scan_directory

    if source_exists and get_settings().warn_nested_junctions:
        try:
            scan_result = scan_directory(source, recursive=True)

            # scan_directory returns a list of Junction objects
            if isinstance(scan_result, list) and scan_result:
                preview_lines.append("")
                preview_lines.append("⚠️ Aviso: A pasta de Dados Físicos contém junções:")

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
                valid = False
                preview_lines.append("")
                preview_lines.append("⚠️ Certifique-se de fechar os seguintes processos:")
                for proc in processes:
                    preview_lines.append(f"   • {proc}")
        except Exception as e:
            logger.warning(f"Error checking for blocking processes: {e}")

    return "\n".join(preview_lines), valid
