"""Dialog for application settings"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from winlink.core.config import AppSettings, save_settings
from winlink.core.scanner import discovery_path, is_discovery_excluded
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class SettingsDialog(AnimatedDialog):
    """Dialog for application settings"""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = settings

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        from PyQt6.QtWidgets import QWidget

        from winlink.ui.components import (
            ActionRow,
            Columns,
            FieldGrid,
            Panel,
            button_style,
            heading,
            help_row,
        )

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
        self.link_view_combo = QComboBox()
        self.link_view_combo.addItem("Normal", "normal")
        self.link_view_combo.addItem("Compacta", "compact")
        self.default_type_combo = QComboBox()
        for label, value in [
            ("Pasta - Junção", "junction"),
            ("Pasta - Symlink", "symlink_dir"),
            ("Arquivo - Hardlink", "hardlink"),
            ("Arquivo - Symlink", "symlink_file"),
        ]:
            self.default_type_combo.addItem(label, value)
        fields.addWidget(
            FieldGrid(
                [
                    ("Tema", self.theme_combo),
                    ("Apresentação de Meus Links", self.link_view_combo),
                    ("Tipo de link padrão", self.default_type_combo),
                ]
            )
        )
        fields.addSpacing(8)
        self.scan_list = QListWidget()
        self.excluded_list = QListWidget()
        directories = []
        for title, listing, add, remove in (
            (
                "Pastas incluídas",
                self.scan_list,
                self.add_scan_directory,
                self.remove_scan_directory,
            ),
            (
                "Pastas excluídas",
                self.excluded_list,
                self.add_excluded_directory,
                self.remove_excluded_directory,
            ),
        ):
            panel = Panel()
            panel.content.setContentsMargins(16, 16, 16, 16)
            label = QLabel(title)
            label.setBuddy(listing)
            panel.content.addWidget(label)
            listing.setAccessibleName(title)
            listing.setMinimumHeight(96)
            listing.setMaximumHeight(160)
            panel.content.addWidget(listing)
            add_button = button_style(QPushButton("Adicionar pasta"), "plus")
            add_button.clicked.connect(add)
            remove_button = button_style(QPushButton("Remover selecionada"), "trash")
            remove_button.clicked.connect(remove)
            panel.content.addWidget(ActionRow([add_button, remove_button]))
            directories.append(panel)
        fields.addWidget(Columns(*directories))
        self.discovery_notice = QLabel()
        self.discovery_notice.setWordWrap(True)
        self.discovery_notice.setObjectName("muted")
        fields.addWidget(self.discovery_notice)
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
        self.calculate_storage_checkbox = QCheckBox("Calcular armazenamento automaticamente")
        self.backup_checkbox = QCheckBox("Criar backup antes de desfazer")
        self.notify_checkbox = QCheckBox("Exibir notificações")
        self.warn_nested_checkbox = QCheckBox("Avisar sobre links aninhados")
        for checkbox in [
            self.calculate_storage_checkbox,
            self.backup_checkbox,
            self.notify_checkbox,
            self.warn_nested_checkbox,
        ]:
            descriptions = {
                self.calculate_storage_checkbox: (
                    "Controla as estimativas automáticas de armazenamento na criação, prévia, "
                    "abertura de Propriedades e reversão. Não desativa as demais validações nem "
                    "o botão Recalcular manual em Propriedades."
                ),
                self.backup_checkbox: "Pré-seleciona a preservação dos Dados Físicos como backup ao desfazer um link de diretório. Confira a estratégia na confirmação.",
                self.notify_checkbox: "Controla avisos adicionais de sucesso quando disponíveis. Progresso, erros, confirmação e avisos de recuperação continuam visíveis.",
                self.warn_nested_checkbox: "Na prévia, avisa se os Dados Físicos contêm outros links. Não altera esses links.",
            }
            fields.addWidget(help_row(checkbox, checkbox.text(), descriptions[checkbox]))
        fields.addSpacing(8)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_label = QLabel("Nível de logs")
        log_label.setObjectName("fieldLabel")
        log_label.setBuddy(self.log_level_combo)
        fields.addWidget(log_label)
        self.open_logs_btn = button_style(QPushButton("Abrir pasta de logs"), "folder")
        self.open_logs_btn.clicked.connect(self.open_logs_folder)
        fields.addWidget(ActionRow([self.log_level_combo, self.open_logs_btn]))
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
        self._excluded_directories = list(settings.scan_excluded_directories)
        self.default_type_combo.setCurrentIndex(
            self.default_type_combo.findData(settings.default_link_type)
        )
        # Theme
        theme_index = self.theme_combo.findData(settings.theme_mode)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

        self.link_view_combo.setCurrentIndex(self.link_view_combo.findData(settings.link_view_mode))

        # Scan directories
        self.scan_list.clear()
        for directory in self._scan_directories:
            self.scan_list.addItem(directory)

        self.excluded_list.clear()
        self.excluded_list.addItems(self._excluded_directories)
        self.update_discovery_notice()

        # Operations
        self.confirm_checkbox.setChecked(True)
        self.calculate_storage_checkbox.setChecked(settings.calculate_storage_automatically)
        self.backup_checkbox.setChecked(settings.auto_backup_before_undo)
        self.notify_checkbox.setChecked(settings.show_notifications)
        self.warn_nested_checkbox.setChecked(settings.warn_nested_junctions)

        # Logs
        log_level_index = self.log_level_combo.findText(settings.log_level)
        if log_level_index >= 0:
            self.log_level_combo.setCurrentIndex(log_level_index)

    def update_discovery_notice(self):
        exclusions = tuple(discovery_path(Path(path)) for path in self._excluded_directories)
        conflicts = [
            path for path in self._scan_directories if is_discovery_excluded(Path(path), exclusions)
        ]
        self.discovery_notice.setText(
            "Pastas incluídas que serão ignoradas: " + ", ".join(conflicts) if conflicts else ""
        )
        self.discovery_notice.setVisible(bool(conflicts))

    def add_scan_directory(self):
        self.add_discovery_directory(self.scan_list, self._scan_directories)

    def add_excluded_directory(self):
        self.add_discovery_directory(self.excluded_list, self._excluded_directories)

    def add_discovery_directory(self, listing, paths):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório", str(Path.home()))
        if not directory:
            return
        path = discovery_path(Path(directory))
        if not path.is_absolute():
            QMessageBox.warning(self, "Revise as preferências", "Use somente diretórios absolutos.")
            return
        if path in {discovery_path(Path(item)) for item in paths}:
            QMessageBox.warning(self, "Revise as preferências", "Esta pasta já está na lista.")
            return
        paths.append(str(path))
        listing.addItem(str(path))
        self.update_discovery_notice()

    def remove_scan_directory(self):
        self.remove_discovery_directory(self.scan_list, self._scan_directories)

    def remove_excluded_directory(self):
        self.remove_discovery_directory(self.excluded_list, self._excluded_directories)

    def remove_discovery_directory(self, listing, paths):
        row = listing.currentRow()
        if row >= 0:
            paths.pop(row)
            listing.takeItem(row)
            self.update_discovery_notice()

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

        if any(
            not Path(path).is_absolute()
            for path in self._scan_directories + self._excluded_directories
        ):
            QMessageBox.warning(self, "Revise as preferências", "Use somente diretórios absolutos.")
            return
        candidate = self.settings.model_copy(deep=True)
        # Update settings
        candidate.default_link_type = self.default_type_combo.currentData()
        candidate.theme_mode = self.theme_combo.currentData()
        candidate.link_view_mode = self.link_view_combo.currentData()
        candidate.scan_directories = self._scan_directories
        candidate.scan_excluded_directories = self._excluded_directories
        candidate.confirm_before_destructive = self.confirm_checkbox.isChecked()
        candidate.calculate_storage_automatically = self.calculate_storage_checkbox.isChecked()
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
