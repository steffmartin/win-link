"""Main window for WinLink application"""

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from winlink.core.config import get_settings
from winlink.core.history import HistoryManager
from winlink.core.models import Creator, Junction, JunctionStatus, UndoStrategy
from winlink.ui.dialogs import (
    CreateJunctionDialog,
    HistoryDialog,
    ProgressDialog,
    PropertiesDialog,
    SettingsDialog,
    UndoDialog,
)
from winlink.ui.junction_filter import JunctionFilterProxyModel
from winlink.ui.junction_model import JunctionTableModel
from winlink.ui.theme import ThemeManager
from winlink.utils.logger import get_logger


class ScanWorker(QThread):
    """Worker thread for scanning junctions"""

    finished = pyqtSignal(object)  # ScanResult
    error = pyqtSignal(str)

    def __init__(self, directories: list[Path]):
        super().__init__()
        self.directories = directories

    def run(self):
        """Run scan in background"""
        try:
            from winlink.core.scanner import scan_directories

            result = scan_directories(self.directories, recursive=True)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.settings = get_settings()
        self.history_manager = HistoryManager()

        # Theme manager
        self.theme_manager = ThemeManager()

        # Data models
        self.junction_model = JunctionTableModel()
        self.filter_model = JunctionFilterProxyModel()
        self.filter_model.setSourceModel(self.junction_model)

        # Scan worker
        self.scan_worker: ScanWorker | None = None

        self.init_ui()
        self.apply_theme()
        self.start_scan()

        self.logger.info("WinLink main window initialized")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("WinLink")
        self.setGeometry(100, 100, self.settings.window_width, self.settings.window_height)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create toolbar
        self.create_toolbar()

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 10, 10, 10)

        search_label = QLabel("Buscar:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar junções...")
        self.search_edit.textChanged.connect(self.on_search_changed)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)

        main_layout.addLayout(search_layout)

        # Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(10, 5, 10, 5)

        filter_label = QLabel("Filtros:")

        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos os Status")
        self.status_filter.addItem("Ativas")
        self.status_filter.addItem("Quebradas")
        self.status_filter.addItem("Inacessíveis")
        self.status_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.creator_filter = QComboBox()
        self.creator_filter.addItem("Todos os Criadores")
        self.creator_filter.addItem("App")
        self.creator_filter.addItem("Existente")
        self.creator_filter.addItem("Manual")
        self.creator_filter.currentIndexChanged.connect(self.on_filter_changed)

        self.clear_filter_btn = QPushButton("Limpar Filtros")
        self.clear_filter_btn.clicked.connect(self.clear_filters)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.creator_filter)
        filter_layout.addWidget(self.clear_filter_btn)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # Junction table
        self.table_view = QTableView()
        self.table_view.setModel(self.filter_model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.resizeColumnsToContents()

        main_layout.addWidget(self.table_view)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

        # Menu bar
        self.create_menu_bar()

    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Home action
        home_action = QAction("Home", self)
        home_action.setStatusTip("Atualizar lista e voltar ao estado inicial")
        home_action.triggered.connect(self.on_home)
        toolbar.addAction(home_action)

        toolbar.addSeparator()

        # New junction action
        new_action = QAction("Nova Junção", self)
        new_action.setStatusTip("Criar nova junção")
        new_action.triggered.connect(self.on_new_junction)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        # Settings action
        settings_action = QAction("Configurações", self)
        settings_action.setStatusTip("Abrir configurações")
        settings_action.triggered.connect(self.on_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        # History action
        history_action = QAction("Histórico", self)
        history_action.setStatusTip("Ver histórico de operações")
        history_action.triggered.connect(self.on_history)
        toolbar.addAction(history_action)

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&Arquivo")

        new_action = QAction("&Nova Junção", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new_junction)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        refresh_action = QAction("&Atualizar", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.start_scan)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("&Sair", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Editar")

        settings_action = QAction("&Configurações", self)
        settings_action.triggered.connect(self.on_settings)
        edit_menu.addAction(settings_action)

        # View menu
        view_menu = menubar.addMenu("&Exibir")

        history_action = QAction("&Histórico", self)
        history_action.triggered.connect(self.on_history)
        view_menu.addAction(history_action)

        # Help menu
        help_menu = menubar.addMenu("&Ajuda")

        about_action = QAction("&Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_theme(self):
        """Apply theme to application"""
        self.theme_manager.apply_theme(self.settings.theme_mode)
        self.setStyleSheet(self.theme_manager.get_stylesheet())

    def start_scan(self):
        """Start scanning for junctions"""
        self.status_bar.showMessage("Escaneando junções...")

        # Convert scan directories to Path objects
        directories = [Path(d) for d in self.settings.scan_directories]

        # Create and start worker
        self.scan_worker = ScanWorker(directories)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_scan_finished(self, result):
        """Handle scan completion"""
        self.junction_model.set_junctions(result.junctions)
        self.status_bar.showMessage(
            f"Escaneamento concluído: {len(result.junctions)} junções encontradas"
        )
        self.logger.info(f"Scan completed: {len(result.junctions)} junctions found")

    def on_scan_error(self, error: str):
        """Handle scan error"""
        self.status_bar.showMessage(f"Erro ao escanear: {error}")
        self.logger.error(f"Scan error: {error}")
        QMessageBox.critical(self, "Erro", f"Erro ao escanear junções: {error}")

    def on_search_changed(self, text: str):
        """Handle search text change"""
        self.filter_model.set_search_text(text)

    def on_filter_changed(self):
        """Handle filter change"""
        # Status filter
        status_index = self.status_filter.currentIndex()
        if status_index == 0:
            self.filter_model.set_filter_status(None)
        elif status_index == 1:
            self.filter_model.set_filter_status(JunctionStatus.ACTIVE)
        elif status_index == 2:
            self.filter_model.set_filter_status(JunctionStatus.BROKEN)
        elif status_index == 3:
            self.filter_model.set_filter_status(JunctionStatus.INACCESSIBLE)

        # Creator filter
        creator_index = self.creator_filter.currentIndex()
        if creator_index == 0:
            self.filter_model.set_filter_creator(None)
        elif creator_index == 1:
            self.filter_model.set_filter_creator(Creator.APP)
        elif creator_index == 2:
            self.filter_model.set_filter_creator(Creator.EXISTING)
        elif creator_index == 3:
            self.filter_model.set_filter_creator(Creator.MANUAL)

    def clear_filters(self):
        """Clear all filters"""
        self.status_filter.setCurrentIndex(0)
        self.creator_filter.setCurrentIndex(0)
        self.search_edit.clear()

    def on_home(self):
        """Handle home action"""
        self.clear_filters()
        self.start_scan()

    def on_new_junction(self):
        """Handle new junction action"""
        dialog = CreateJunctionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            target = dialog.get_target_path()
            source = dialog.get_source_path()

            if target and source:
                self.create_junction(target, source)

    def create_junction(self, target: Path, source: Path):
        """Create a junction"""
        # Validate
        from winlink.core.validators import validate_junction_creation
        from winlink.core.models import JunctionType

        validation = validate_junction_creation(source, target, JunctionType.JUNCTION)
        if not validation.is_valid:
            error_msg = "\n".join(validation.errors)
            QMessageBox.critical(self, "Erro de Validação", error_msg)
            return

        # Show warnings
        if validation.warnings:
            warning_msg = "\n".join(validation.warnings)
            reply = QMessageBox.warning(
                self,
                "Aviso",
                f"{warning_msg}\n\nDeseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Create progress dialog
        progress = ProgressDialog("Criando Junção", self)
        progress.show()

        # Perform operation
        try:
            from winlink.core.file_ops import copy_directory_with_metadata, delete_directory
            from winlink.core.operations import create_junction

            # Check if target exists
            if target.exists():
                progress.update_progress(10, "Copiando arquivos...")

                # Copy files from target to source
                copy_directory_with_metadata(target, source)

                progress.update_progress(50, "Removendo destino...")

                # Remove target
                delete_directory(target)

            progress.update_progress(80, "Criando junção...")

            # Create junction
            create_junction(source, target)

            progress.update_progress(100, "Concluído!")
            progress.set_operation_finished(True)

            # Add to history
            from winlink.core.models import OperationType

            self.history_manager.add_operation(
                operation_type=OperationType.CREATE_JUNCTION,
                source=source,
                target=target,
                success=True,
            )

            # Refresh scan
            self.start_scan()

            QMessageBox.information(self, "Sucesso", "Junção criada com sucesso!")

        except Exception as e:
            self.logger.error(f"Error creating junction: {e}")
            progress.set_operation_finished(False, str(e))
            QMessageBox.critical(self, "Erro", f"Erro ao criar junção: {e}")

            # Add to history
            from winlink.core.models import OperationType

            self.history_manager.add_operation(
                operation_type=OperationType.CREATE_JUNCTION,
                source=source,
                target=target,
                success=False,
                error_message=str(e),
            )

    def on_settings(self):
        """Handle settings action"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reapply theme if changed
            self.apply_theme()
            # Restart scan if directories changed
            self.start_scan()

    def on_history(self):
        """Handle history action"""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.exec()

    def show_context_menu(self, position):
        """Show context menu for selected junction"""
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        # Get actual junction from source model
        source_index = self.filter_model.mapToSource(index)
        junction = self.junction_model.get_junction(source_index)

        if not junction:
            return

        menu = QMenu(self)

        # Properties action
        properties_action = menu.addAction("Propriedades")
        properties_action.triggered.connect(lambda: self.show_properties(junction))

        menu.addSeparator()

        # Undo action (only for junctions created by app)
        if junction.creator == Creator.APP:
            undo_action = menu.addAction("Desfazer")
            undo_action.triggered.connect(lambda: self.undo_junction(junction))

        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def show_properties(self, junction: Junction):
        """Show junction properties dialog"""
        dialog = PropertiesDialog(junction, self)
        dialog.exec()

    def undo_junction(self, junction: Junction):
        """Undo a junction"""
        dialog = UndoDialog(junction.source, junction.target, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            strategy = dialog.get_strategy()
            keep_source = dialog.get_keep_source()

            # Create progress dialog
            progress = ProgressDialog("Desfazendo Junção", self)
            progress.show()

            try:
                from winlink.core.file_ops import (
                    copy_directory,
                    delete_directory,
                    move_directory,
                )
                from winlink.core.operations import remove_junction
                from winlink.core.file_ops import (
                    move_directory,
                    copy_directory_with_metadata,
                    delete_directory,
                )

                progress.update_progress(10, "Removendo junção...")

                # Remove junction
                remove_junction(junction.target)

                progress.update_progress(30, "Processando arquivos...")

                # Apply strategy
                if strategy == UndoStrategy.REMOVE_ONLY:
                    # Just remove junction, leave empty directory
                    pass

                elif strategy == UndoStrategy.MOVE_BACK:
                    # Move files back to target
                    if junction.source.exists():
                        move_directory(junction.source, junction.target)

                        if not keep_source:
                            delete_directory(junction.source)

                elif strategy == UndoStrategy.DUPLICATE:
                    # Copy files to target
                    if junction.source.exists():
                        copy_directory_with_metadata(junction.source, junction.target)

                progress.update_progress(100, "Concluído!")
                progress.set_operation_finished(True)

                # Add to history
                from winlink.core.models import OperationType

                self.history_manager.add_operation(
                    operation_type=OperationType.UNDO_OPERATION,
                    source=junction.source,
                    target=junction.target,
                    success=True,
                    metadata={"strategy": strategy.value, "keep_source": keep_source},
                )

                # Refresh scan
                self.start_scan()

                QMessageBox.information(self, "Sucesso", "Junção desfeita com sucesso!")

            except Exception as e:
                self.logger.error(f"Error undoing junction: {e}")
                progress.set_operation_finished(False, str(e))
                QMessageBox.critical(self, "Erro", f"Erro ao desfazer junção: {e}")

                # Add to history
                from winlink.core.models import OperationType

                self.history_manager.add_operation(
                    operation_type=OperationType.UNDO_OPERATION,
                    source=junction.source,
                    target=junction.target,
                    success=False,
                    error_message=str(e),
                )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Sobre WinLink",
            "WinLink - Gerenciador de Junções\n\n"
            "Versão 0.1.0\n\n"
            "Aplicativo Windows para gerenciamento de junções e links simbólicos "
            "com interface moderna compatível com Windows 11.",
        )

    def closeEvent(self, event):
        """Handle close event"""
        # Save window size if enabled
        if self.settings.remember_window_size:
            self.settings.window_width = self.width()
            self.settings.window_height = self.height()

        event.accept()
