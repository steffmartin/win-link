"""Dialog for previewing junction creation operation"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from winlink.utils.logger import get_logger


class PreviewDialog(QDialog):
    """Dialog for previewing junction creation operation"""

    def __init__(self, target: Path, source: Path, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.target = target
        self.source = source

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
        """Calculate and display preview of the operation"""
        preview_lines = []
        preview_lines.append("O que será feito:")
        preview_lines.append("")

        # Check if target exists
        target_exists = self.target.exists()
        source_exists = self.source.exists()

        if source_exists:
            preview_lines.append(f"✓ Diretório de origem já existe: {self.source}")
        else:
            preview_lines.append(f"✓ Criar diretório de origem: {self.source}")

        if target_exists:
            # Target exists, need to copy files
            from winlink.core.file_ops import calculate_directory_size_recursive, has_sufficient_disk_space

            try:
                size = calculate_directory_size_recursive(self.target)
                size_str = self.format_size(size)

                preview_lines.append(f"✓ Copiar arquivos de {self.target}")
                preview_lines.append(f"  para {self.source} ({size_str})")
                preview_lines.append(f"✓ Remover {self.target}")

                # Check disk space
                if has_sufficient_disk_space(self.source.parent, size):
                    available = self.source.parent.stat().st_dev
                    available_str = self.format_size(available)
                    preview_lines.append("")
                    preview_lines.append(f"Espaço necessário: {size_str}")
                    preview_lines.append(f"Espaço disponível: {available_str}")
                else:
                    preview_lines.append("")
                    preview_lines.append("⚠️ Espaço insuficiente no disco!")

                    self.confirm_btn.setEnabled(False)
            except Exception as e:
                self.logger.error(f"Error calculating directory size: {e}")
                preview_lines.append(f"⚠️ Erro ao calcular tamanho: {e}")
                self.confirm_btn.setEnabled(False)
        else:
            preview_lines.append(f"✓ Criar diretório de origem vazio: {self.source}")
            preview_lines.append(f"✓ Criar junção: {self.target} -> {self.source}")

        preview_lines.append("")
        preview_lines.append(f"✓ Criar junção: {self.target} -> {self.source}")

        # Check for nested junctions
        from winlink.core.scanner import scan_directory

        if source_exists:
            try:
                scan_result = scan_directory(self.source, recursive=True)

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
                self.logger.warning(f"Error scanning for nested junctions: {e}")

        # Check for processes blocking files
        from winlink.core.process_manager import get_processes_using_directory

        if target_exists:
            try:
                processes = get_processes_using_directory(self.target)
                if processes:
                    preview_lines.append("")
                    preview_lines.append("⚠️ Certifique-se de fechar os seguintes processos:")
                    for proc in processes:
                        preview_lines.append(f"   • {proc}")
            except Exception as e:
                self.logger.warning(f"Error checking for blocking processes: {e}")

        self.preview_text.setPlainText("\n".join(preview_lines))

    def format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
