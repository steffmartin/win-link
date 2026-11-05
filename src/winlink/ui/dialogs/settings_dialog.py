"""Dialog for application settings"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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
        from PyQt6.QtWidgets import QWidget

        from winlink.ui.components import ActionRow, Panel, button_style, field, heading, help_row

        self.setWindowTitle("Configurações do WinLink")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        heading(
            layout,
            "Configurações do WinLink",
            "Salve para aplicar. Restaurar padrões prepara os campos e também exige salvar.",
        )
        content = QWidget()
        content.setObjectName("settingsContent")
        fields = QVBoxLayout(content)
        fields.setContentsMargins(0, 0, 0, 0)
        fields.setSpacing(12)
        self.theme_combo = QComboBox()
        for label, mode in [("Seguir sistema", "auto"), ("Claro", "light"), ("Escuro", "dark")]:
            self.theme_combo.addItem(label, mode)
        field(fields, "Tema", self.theme_combo)
        self.default_type_combo = QComboBox()
        for label, value in [
            ("Junction", "junction"),
            ("Symlink (Dir)", "symlink_dir"),
            ("Symlink (File)", "symlink_file"),
            ("Hardlink", "hardlink"),
        ]:
            self.default_type_combo.addItem(label, value)
        fields.addWidget(
            help_row(
                QLabel("Tipo de link padrão"),
                "Tipo de link padrão",
                "Escolhe o tipo pré-selecionado ao iniciar uma criação com formulário vazio. Não altera links existentes.",
            )
        )
        fields.addWidget(self.default_type_combo)
        fields.addSpacing(8)
        directories = Panel()
        directories.content.setContentsMargins(16, 16, 16, 16)
        top = QHBoxLayout()
        top.addWidget(QLabel("Diretórios configurados"), 1)
        self.add_scan_btn = button_style(QPushButton("Adicionar diretório"), "plus")
        self.add_scan_btn.clicked.connect(self.add_scan_directory)
        top.addWidget(self.add_scan_btn)
        directories.content.addLayout(top)
        self.scan_list = QListWidget()
        self.scan_list.setMinimumHeight(96)
        self.scan_list.setMaximumHeight(160)
        directories.content.addWidget(self.scan_list)
        self.remove_scan_btn = button_style(QPushButton("Remover selecionado"), "trash")
        self.remove_scan_btn.clicked.connect(self.remove_scan_directory)
        directories.content.addWidget(self.remove_scan_btn, 0, Qt.AlignmentFlag.AlignLeft)
        fields.addWidget(directories)
        fields.addSpacing(8)
        self.confirm_checkbox = QCheckBox("Confirmar operações destrutivas (obrigatório)")
        self.confirm_checkbox.setEnabled(False)
        fields.addWidget(
            help_row(
                self.confirm_checkbox,
                "Confirmação obrigatória",
                "A prévia e a confirmação de operações destrutivas são sempre obrigatórias e não podem ser desativadas.",
            )
        )
        note = QLabel("A prévia e a confirmação permanecem obrigatórias para proteger os dados.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        fields.addWidget(note)
        self.backup_checkbox = QCheckBox("Criar backup antes de desfazer")
        self.notify_checkbox = QCheckBox("Exibir notificações")
        self.warn_nested_checkbox = QCheckBox("Avisar sobre links aninhados")
        for checkbox in [self.backup_checkbox, self.notify_checkbox, self.warn_nested_checkbox]:
            descriptions = {
                self.backup_checkbox: "Pré-seleciona a preservação dos Dados Físicos como backup ao desfazer um link de diretório. Confira a estratégia na confirmação.",
                self.notify_checkbox: "Controla avisos adicionais de sucesso quando disponíveis. Progresso, erros, confirmação e avisos de recuperação continuam visíveis.",
                self.warn_nested_checkbox: "Na prévia, avisa se os Dados Físicos contêm outros links. Não altera esses links.",
            }
            fields.addWidget(help_row(checkbox, checkbox.text(), descriptions[checkbox]))
        fields.addSpacing(8)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        field(fields, "Nível de logs", self.log_level_combo)
        self.open_logs_btn = button_style(QPushButton("Abrir pasta de logs"), "folder")
        self.open_logs_btn.clicked.connect(self.open_logs_folder)
        fields.addWidget(self.open_logs_btn, 0, Qt.AlignmentFlag.AlignLeft)
        fields.addSpacing(12)
        self.defaults_btn = button_style(QPushButton("Restaurar Padrões"), "refresh")
        self.defaults_btn.clicked.connect(self.restore_defaults)
        self.discard_btn = button_style(QPushButton("Descartar alterações"), "undo")
        self.discard_btn.clicked.connect(self.discard_changes)
        self.save_btn = button_style(QPushButton("Salvar Alterações"), "save", primary=True)
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = button_style(QPushButton("Cancelar"), "close")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.hide()
        fields.addWidget(ActionRow([self.defaults_btn, self.discard_btn, self.save_btn]))
        fields.addWidget(self.cancel_btn)
        layout.addWidget(content)
        layout.addStretch()

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
