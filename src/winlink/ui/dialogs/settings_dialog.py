"""Dialog for application settings"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from winlink.core.config import AppSettings, save_settings
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class SettingsDialog(AnimatedDialog):
    """Dialog for application settings"""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = settings

        self._scan_directories: list[str] = list(settings.scan_directories)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Configurações")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel("Configurações")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        # General section
        general_group = QGroupBox("Geral")
        general_layout = QVBoxLayout()

        # Theme
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema:")
        self.theme_combo = QComboBox()
        for label, mode in [("Seguir sistema", "auto"), ("Claro", "light"), ("Escuro", "dark")]:
            self.theme_combo.addItem(label, mode)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        general_layout.addLayout(theme_layout)

        self.default_type_combo = QComboBox()
        for label, value in [
            ("Junction", "junction"),
            ("Symlink (diretório)", "symlink_dir"),
            ("Symlink (arquivo)", "symlink_file"),
            ("Hard link", "hardlink"),
        ]:
            self.default_type_combo.addItem(label, value)
        general_layout.addWidget(QLabel("Tipo de link padrão"))
        general_layout.addWidget(self.default_type_combo)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Scan directories section
        scan_group = QGroupBox("Diretórios de descoberta")
        scan_layout = QVBoxLayout()

        self.scan_list = QListWidget()
        scan_layout.addWidget(self.scan_list)

        scan_buttons_layout = QHBoxLayout()
        self.add_scan_btn = QPushButton("Adicionar")
        self.add_scan_btn.clicked.connect(self.add_scan_directory)
        self.remove_scan_btn = QPushButton("Remover")
        self.remove_scan_btn.clicked.connect(self.remove_scan_directory)
        scan_buttons_layout.addWidget(self.add_scan_btn)
        scan_buttons_layout.addWidget(self.remove_scan_btn)
        scan_layout.addLayout(scan_buttons_layout)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # Operations section
        ops_group = QGroupBox("Operações")
        ops_layout = QVBoxLayout()

        self.confirm_checkbox = QCheckBox("Confirmar operações destrutivas (obrigatório)")
        self.confirm_checkbox.setEnabled(False)
        self.confirm_checkbox.setToolTip(
            "A prévia e a confirmação protegem os arquivos e permanecem obrigatórias."
        )
        ops_layout.addWidget(self.confirm_checkbox)

        self.backup_checkbox = QCheckBox("Criar backup automático antes de desfazer")
        ops_layout.addWidget(self.backup_checkbox)

        self.notify_checkbox = QCheckBox("Mostrar notificações de conclusão")
        ops_layout.addWidget(self.notify_checkbox)

        self.warn_nested_checkbox = QCheckBox("Avisar sobre junções aninhadas")
        warn_nested_desc = QLabel("(quando criar junção para pasta que já contém junções)")
        warn_nested_desc.setStyleSheet("font-size: 12px; margin-left: 20px;")
        ops_layout.addWidget(self.warn_nested_checkbox)
        ops_layout.addWidget(warn_nested_desc)

        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)

        # Logs section
        logs_group = QGroupBox("Logs")
        logs_layout = QVBoxLayout()

        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("Nível:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        logs_layout.addLayout(log_level_layout)

        self.open_logs_btn = QPushButton("Abrir pasta de logs")
        self.open_logs_btn.clicked.connect(self.open_logs_folder)
        logs_layout.addWidget(self.open_logs_btn)

        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self.defaults_btn = QPushButton("Restaurar padrões")
        self.defaults_btn.clicked.connect(self.restore_defaults)
        self.discard_btn = QPushButton("Descartar alterações")
        self.discard_btn.clicked.connect(self.discard_changes)
        button_layout.addWidget(self.defaults_btn)
        button_layout.addWidget(self.discard_btn)
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Salvar")
        self.save_btn.setProperty("primary", True)
        self.save_btn.clicked.connect(self.save_settings)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def restore_defaults(self):
        """Prepare visible preferences without changing persisted storage locations."""
        self.load_settings(AppSettings())

    def discard_changes(self):
        self.load_settings(self.settings)

    def load_settings(self, settings=None):
        """Load settings into UI"""
        settings = settings or self.settings
        self._scan_directories = list(settings.scan_directories)
        self.default_type_combo.setCurrentIndex(
            self.default_type_combo.findData(settings.default_link_type)
        )
        # Theme
        theme_index = self.theme_combo.findData(settings.theme_mode)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        # Scan directories
        self.scan_list.clear()
        for directory in self._scan_directories:
            self.scan_list.addItem(directory)

        # Operations
        self.confirm_checkbox.setChecked(True)
        self.backup_checkbox.setChecked(settings.auto_backup_before_undo)
        self.notify_checkbox.setChecked(settings.show_notifications)
        self.warn_nested_checkbox.setChecked(settings.warn_nested_junctions)

        # Logs
        log_level_index = self.log_level_combo.findText(settings.log_level)
        if log_level_index >= 0:
            self.log_level_combo.setCurrentIndex(log_level_index)

    def add_scan_directory(self):
        """Add a scan directory"""
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório", str(Path.home()))
        if directory:
            self._scan_directories.append(directory)
            self.scan_list.addItem(directory)

    def remove_scan_directory(self):
        """Remove selected scan directory"""
        current_row = self.scan_list.currentRow()
        if current_row >= 0:
            directory = self.scan_list.item(current_row).text()
            self._scan_directories.remove(directory)
            self.scan_list.takeItem(current_row)

    def open_logs_folder(self):
        """Open logs folder in file explorer"""
        import os
        import subprocess

        log_file = self.settings.log_file
        log_dir = log_file.parent

        if log_dir.exists():
            if os.name == "nt":  # Windows
                subprocess.run(["explorer", str(log_dir)])
            else:
                # Fallback for other platforms
                import webbrowser

                webbrowser.open(str(log_dir))
        else:
            QMessageBox.warning(self, "Aviso", "Pasta de logs não existe.")

    def save_settings(self):
        """Save settings"""
        # Validate
        if not self._scan_directories:
            QMessageBox.warning(
                self, "Aviso", "Pelo menos um diretório de escaneamento deve ser configurado."
            )
            return

        if any(not Path(path).is_absolute() for path in self._scan_directories):
            QMessageBox.warning(self, "Revise as preferências", "Use somente diretórios absolutos.")
            return
        candidate = self.settings.model_copy(deep=True)
        # Update settings
        candidate.default_link_type = self.default_type_combo.currentData()
        candidate.theme_mode = self.theme_combo.currentData()
        candidate.scan_directories = self._scan_directories
        candidate.confirm_before_destructive = self.confirm_checkbox.isChecked()
        candidate.auto_backup_before_undo = self.backup_checkbox.isChecked()
        candidate.show_notifications = self.notify_checkbox.isChecked()
        candidate.warn_nested_junctions = self.warn_nested_checkbox.isChecked()
        candidate.log_level = self.log_level_combo.currentText()

        try:
            save_settings(candidate)
        except OSError as exc:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar configurações: {exc}")
            return
        for name in type(self.settings).model_fields:
            setattr(self.settings, name, getattr(candidate, name))

        self.logger.info("Settings saved")
        self.accept()
