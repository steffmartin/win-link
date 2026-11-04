"""Main window for WinLink application"""

import logging
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
from winlink.core.models import (
    Creator,
    Junction,
    JunctionStatus,
    JunctionType,
    OperationType,
    UndoStrategy,
)
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

    result_ready = pyqtSignal(object)  # ScanResult
    error = pyqtSignal(str)

    def __init__(
        self,
        directories: list[Path],
        known_junctions: set[Path] | None = None,
        use_cache: bool = False,
        cache_max_age_seconds: float = 3600,
    ):
        super().__init__()
        self.directories = directories
        self.known_junctions = known_junctions or set()
        self.use_cache = use_cache
        self.cache_max_age_seconds = cache_max_age_seconds

    def run(self):
        """Run scan in background"""
        try:
            from winlink.core.scanner import scan_directories

            result = scan_directories(
                self.directories,
                recursive=True,
                known_junctions=self.known_junctions,
            )
            self.result_ready.emit(result)
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
        self._operation_active = False
        self._scan_pending = False
        self.init_ui()
        self.apply_theme()
        from winlink.core.cache import CacheManager

        cached = CacheManager().load()
        if cached and cached.scan_directories == self.settings.scan_directories:
            self.junction_model.set_junctions(cached.to_junctions())
        self.start_scan()
        self.logger.info("WinLink main window initialized")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("WinLink")
        from winlink.ui.icons import application_icon

        self.setWindowIcon(application_icon())
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
        self.type_filter = QComboBox()
        self.type_filter.addItem("Todos os Tipos", None)
        for link_type in JunctionType:
            self.type_filter.addItem(link_type.value, link_type)
        self.type_filter.currentIndexChanged.connect(self.on_filter_changed)
        self.clear_filter_btn = QPushButton("Limpar Filtros")
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.creator_filter)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.clear_filter_btn)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        # Junction table
        self.table_view = QTableView()
        self.table_view.setModel(self.filter_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setResizeContentsPrecision(100)
        self.table_view.resizeColumnsToContents()
        for column, width in enumerate((300, 300, 110, 120, 100)):
            self.table_view.setColumnWidth(column, width)
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
        from PyQt6.QtWidgets import QStyle

        home_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        toolbar.addAction(home_action)
        toolbar.addSeparator()
        # New junction action
        new_action = QAction("Nova Junção", self)
        new_action.setStatusTip("Criar nova junção")
        new_action.triggered.connect(self.on_new_junction)
        new_action.setIcon(self.windowIcon())
        toolbar.addAction(new_action)
        toolbar.addSeparator()
        # Settings action
        settings_action = QAction("Configurações", self)
        settings_action.setStatusTip("Abrir configurações")
        settings_action.triggered.connect(self.on_settings)
        settings_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        toolbar.addAction(settings_action)
        toolbar.addSeparator()
        # History action
        history_action = QAction("Histórico", self)
        history_action.setStatusTip("Ver histórico de operações")
        history_action.triggered.connect(self.on_history)
        history_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
        )
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
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.on_settings)
        edit_menu.addAction(settings_action)
        # View menu
        view_menu = menubar.addMenu("&Exibir")
        history_action = QAction("&Histórico", self)
        history_action.setShortcut("Ctrl+H")
        history_action.triggered.connect(self.on_history)
        view_menu.addAction(history_action)
        search_action = QAction("&Buscar", self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.search_edit.setFocus)
        view_menu.addAction(search_action)
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
        if self._operation_active is True:
            return
        if self.scan_worker is not None and self.scan_worker.isRunning():
            self._scan_pending = True
            return
        self._scan_pending = False
        self.status_bar.showMessage("Escaneando junções...")
        # Convert scan directories to Path objects
        directories = [Path(d) for d in self.settings.scan_directories]
        # Create and start worker
        known_junctions = set()
        for record in reversed(self.history_manager.get_history()):
            if not record.success or record.target is None:
                continue
            if record.operation_type in (
                OperationType.CREATE_JUNCTION,
                OperationType.CREATE_SYMLINK,
                OperationType.CREATE_HARDLINK,
            ):
                known_junctions.add(record.target)
            elif record.operation_type in (
                OperationType.REMOVE_JUNCTION,
                OperationType.UNDO_OPERATION,
            ):
                known_junctions.discard(record.target)
        self.scan_worker = ScanWorker(
            directories,
            known_junctions,
            use_cache=False,
            cache_max_age_seconds=3600,  # 1 hour
        )
        self.scan_worker.result_ready.connect(self.on_scan_finished)
        self.scan_worker.finished.connect(self.on_scan_thread_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_scan_thread_finished(self):
        """Run a refresh requested while the preceding scan was still active."""
        if self._scan_pending:
            self.start_scan()

    def on_scan_finished(self, result):
        """Handle scan completion"""
        from winlink.core.cache import CacheManager

        if not result.errors:
            CacheManager().save(result)
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
        self.filter_model.set_filter_type(self.type_filter.currentData())
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
        self.type_filter.setCurrentIndex(0)
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
            link_type = dialog.get_link_type()
            if target and source:
                self.create_link(target, source, link_type)

    def create_junction(self, target: Path, source: Path):
        """Compatibility entry point for directory junction creation."""
        MainWindow.create_link(self, target, source, JunctionType.JUNCTION)

    def create_link(self, target: Path, source: Path, link_type: JunctionType):
        """Create a link (junction, symlink, or hardlink)"""
        if self._operation_active is True:
            return
        # Validate
        from winlink.core.validators import validate_junction_creation
        from winlink.ui.operation_worker import evaluate_in_background

        self._operation_active = True
        try:
            validation = evaluate_in_background(
                lambda: validate_junction_creation(source, target, link_type)
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro de validação", str(exc))
            return
        finally:
            self._operation_active = False
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

        # Handle hard links separately (simpler flow)
        if link_type == JunctionType.HARDLINK:
            MainWindow.create_hard_link(self, target, source)
            return

        if link_type == JunctionType.SYMLINK and source.is_file():
            MainWindow.create_file_link(self, target, source, link_type)
            return

        # Junctions and symlinks
        MainWindow.create_directory_link(self, target, source, link_type)

    def create_hard_link(self, target: Path, source: Path):
        """Create an additional name for an existing file."""
        MainWindow.create_file_link(self, target, source, JunctionType.HARDLINK)

    def create_file_link(self, target: Path, source: Path, link_type: JunctionType):
        from winlink.core.operations import create_hard_link, create_symbolic_link
        from winlink.ui.operation_worker import run_operation

        progress = ProgressDialog("Criando link de arquivo", self)
        progress.show()
        operation_type = (
            OperationType.CREATE_HARDLINK
            if link_type == JunctionType.HARDLINK
            else OperationType.CREATE_SYMLINK
        )
        success, error = False, None
        self._operation_active = True
        try:

            def perform(context):
                context.check_cancelled()
                context.report(50, "Criando link de arquivo...")
                created = (
                    create_hard_link(source, target)
                    if link_type == JunctionType.HARDLINK
                    else create_symbolic_link(source, target, is_directory=False)
                )
                if not created:
                    raise OSError(
                        "Não foi possível criar o link. Verifique as permissões e o volume."
                    )

            run_operation(perform, progress)
            success = True
        except Exception as exc:
            error = str(exc)
            self.logger.error(f"Error creating file link: {exc}")
            QMessageBox.critical(self, "Erro", error)
        finally:
            self._operation_active = False
            progress.close()
        if (
            self.history_manager.add_operation(
                operation_type, source, target, success=success, error_message=error
            )
            is False
        ):
            QMessageBox.warning(self, "Histórico", "Não foi possível salvar o histórico.")
        if success:
            self.start_scan()
            if self.settings.show_notifications is not False:
                QMessageBox.information(self, "Sucesso", "Link de arquivo criado com sucesso!")

    def create_directory_link(self, target: Path, source: Path, link_type: JunctionType):
        """Create a directory link (junction or symlink)"""
        # Create progress dialog
        progress = ProgressDialog("Criando Link", self)
        progress.show()
        # Perform operation
        try:
            from winlink.core.file_ops import (
                copy_directory_with_metadata,
                delete_directory,
                tree_signature,
            )
            from winlink.core.operations import create_junction, create_symbolic_link
            from winlink.ui.operation_worker import run_operation

            preserved_backups = []

            def perform(context):
                from uuid import uuid4

                backup = None
                original_signature = None
                context.check_cancelled()
                if target.is_junction() or target.is_symlink():
                    raise OSError("O destino foi substituído por um link. Atualize a lista.")
                if target.exists():
                    original_signature = tree_signature(target)
                    context.report(10, "Copiando arquivos...")
                    if not copy_directory_with_metadata(
                        target, source, check_cancelled=context.check_cancelled
                    ):
                        raise OSError("Falha na cópia; o destino foi preservado.")
                    context.check_cancelled()
                    if tree_signature(target) != original_signature:
                        raise OSError(
                            "Os arquivos foram alterados durante a cópia. O destino original foi preservado."
                        )
                    context.report(50, "Preservando destino original...")
                    backup = target.with_name(f"{target.name}.winlink-backup-{uuid4().hex}")
                    target.rename(backup)
                try:
                    context.report(
                        80,
                        f"Criando {'symlink' if link_type == JunctionType.SYMLINK else 'junção'}...",
                    )
                    source.mkdir(parents=True, exist_ok=True)
                    if link_type == JunctionType.SYMLINK:
                        if not create_symbolic_link(source, target, is_directory=True):
                            raise OSError("Não foi possível criar o symlink.")
                    else:
                        if not create_junction(source, target):
                            raise OSError("Não foi possível criar a junção.")
                except Exception:
                    if backup is not None:
                        import os

                        if not os.path.lexists(target):
                            try:
                                backup.rename(target)
                            except OSError as rollback_error:
                                raise OSError(
                                    f"Falha na restauração; arquivos originais preservados em {backup}"
                                ) from rollback_error
                        else:
                            raise OSError(
                                f"Falha na criação; destino original preservado em {backup}"
                            ) from None
                    raise
                if backup is not None:
                    if tree_signature(backup) != original_signature or not delete_directory(backup):
                        preserved_backups.append(str(backup))

            self._operation_active = True
            try:
                run_operation(perform, progress)
            finally:
                self._operation_active = False
            progress.update_progress(100, "Concluído!")
            progress.set_operation_finished(True)
            # Add to history
            op_type = (
                OperationType.CREATE_SYMLINK
                if link_type == JunctionType.SYMLINK
                else OperationType.CREATE_JUNCTION
            )

            if (
                self.history_manager.add_operation(
                    operation_type=op_type,
                    source=source,
                    target=target,
                    success=True,
                    metadata={"preserved_backups": preserved_backups},
                )
                is False
            ):
                QMessageBox.warning(
                    self,
                    "Historico",
                    "Nao foi possivel salvar o historico. Consulte o log antes de continuar.",
                )
            # Refresh scan
            self.start_scan()
            if preserved_backups:
                QMessageBox.warning(
                    self,
                    "Backup preservado",
                    "Link criado. Não foi possível limpar o backup:\n"
                    + "\n".join(preserved_backups),
                )
            if self.settings.show_notifications is not False:
                link_name = "Symlink" if link_type == JunctionType.SYMLINK else "Junção"
                QMessageBox.information(self, "Sucesso", f"{link_name} criado com sucesso!")
        except Exception as e:
            self.logger.error(f"Error creating link: {e}")
            progress.set_operation_finished(False, str(e))
            QMessageBox.critical(self, "Erro", f"Erro ao criar link: {e}")
            # Add to history
            op_type = (
                OperationType.CREATE_SYMLINK
                if link_type == JunctionType.SYMLINK
                else OperationType.CREATE_JUNCTION
            )

            if (
                self.history_manager.add_operation(
                    operation_type=op_type,
                    source=source,
                    target=target,
                    success=False,
                    error_message=str(e),
                )
                is False
            ):
                QMessageBox.warning(
                    self,
                    "Historico",
                    "Nao foi possivel salvar o historico. Consulte o log antes de continuar.",
                )

    def on_settings(self):
        """Handle settings action"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reapply theme if changed
            self.apply_theme()
            from winlink.utils.logger import setup_logger

            self.logger = setup_logger(
                level=getattr(logging, self.settings.log_level),
                log_file=self.settings.log_file,
                log_to_console=self.settings.log_to_console,
            )
            # Restart scan if directories changed
            self.start_scan()

    def on_history(self):
        """Handle history action"""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.undo_requested.connect(self.undo_junction)
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
        undo_action = menu.addAction("Desfazer")
        undo_action.triggered.connect(lambda: self.undo_junction(junction))
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def show_properties(self, junction: Junction):
        """Show junction properties dialog"""
        dialog = PropertiesDialog(junction, self, history_manager=self.history_manager)
        dialog.exec()

    def undo_junction(self, junction: Junction):
        """Undo a junction"""
        if self._operation_active is True:
            return
        if junction.is_directory is False:
            MainWindow.remove_file_link(self, junction)
            return
        dialog = UndoDialog(junction.source, junction.target, self)
        dialog.keep_source_checkbox.setChecked(self.settings.auto_backup_before_undo)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            strategy = dialog.get_strategy()
            keep_source = dialog.get_keep_source()
            # Create progress dialog
            progress = ProgressDialog("Desfazendo Junção", self)
            progress.show()
            try:
                from uuid import uuid4

                from winlink.core.file_ops import (
                    copy_directory_with_metadata,
                    delete_directory,
                    tree_signature,
                )
                from winlink.core.operations import recreate_junction, remove_junction
                from winlink.ui.operation_worker import run_operation

                def perform(context):
                    context.check_cancelled()
                    if strategy == UndoStrategy.REMOVE_ONLY:
                        if not remove_junction(junction.target):
                            raise OSError("Não foi possível remover a junção.")
                        junction.target.mkdir(parents=True, exist_ok=True)
                        return
                    if junction.source.resolve() == junction.source.resolve().parent:
                        raise OSError("Não é permitido migrar a raiz de um volume.")
                    if not junction.source.is_dir():
                        raise OSError("A origem não está disponível para restaurar os arquivos.")
                    if junction.target.is_junction() or junction.target.is_symlink():
                        if not junction.source.samefile(junction.target):
                            raise OSError(
                                "A junção foi alterada. Atualize a lista antes de desfazer."
                            )
                    from winlink.core.file_ops import calculate_disk_space_required
                    from winlink.core.validators import validate_disk_space

                    space = validate_disk_space(
                        junction.target.parent, calculate_disk_space_required(junction.source)
                    )
                    if not space.is_valid:
                        raise OSError("\n".join(space.errors))
                    staging = junction.target.with_name(
                        f"{junction.target.name}.winlink-restore-{uuid4().hex}"
                    )
                    source_signature = tree_signature(junction.source)
                    context.report(10, "Preparando restauração...")
                    try:
                        if not copy_directory_with_metadata(
                            junction.source, staging, check_cancelled=context.check_cancelled
                        ):
                            raise OSError("Falha na cópia; a junção original foi preservada.")
                        context.check_cancelled()
                        if tree_signature(junction.source) != source_signature:
                            raise OSError(
                                "A origem foi alterada durante a cópia. O link e a origem foram preservados."
                            )
                        if not remove_junction(junction.target):
                            raise OSError("Não foi possível remover a junção.")
                        try:
                            staging.rename(junction.target)
                        except OSError:
                            recreate_junction(junction)
                            raise
                        if strategy == UndoStrategy.MOVE_BACK and not keep_source:
                            if tree_signature(junction.source) != source_signature:
                                raise OSError(
                                    "Arquivos restaurados; origem preservada porque houve alterações externas."
                                )
                            if not delete_directory(junction.source):
                                raise OSError(
                                    "Arquivos restaurados; origem preservada porque a limpeza falhou."
                                )
                    finally:
                        if staging.exists():
                            delete_directory(staging)

                self._operation_active = True
                try:
                    run_operation(perform, progress)
                finally:
                    self._operation_active = False
                progress.update_progress(100, "Concluído!")
                progress.set_operation_finished(True)
                # Add to history
                from winlink.core.models import OperationType

                if (
                    self.history_manager.add_operation(
                        operation_type=OperationType.UNDO_OPERATION,
                        source=junction.source,
                        target=junction.target,
                        success=True,
                        metadata={"strategy": strategy.value, "keep_source": keep_source},
                    )
                    is False
                ):
                    QMessageBox.warning(
                        self,
                        "Historico",
                        "Nao foi possivel salvar o historico. Consulte o log antes de continuar.",
                    )
                # Refresh scan
                self.start_scan()
                if self.settings.show_notifications is not False:
                    QMessageBox.information(self, "Sucesso", "Junção desfeita com sucesso!")
            except Exception as e:
                self.logger.error(f"Error undoing junction: {e}")
                progress.set_operation_finished(False, str(e))
                QMessageBox.critical(self, "Erro", f"Erro ao desfazer junção: {e}")
                # Add to history
                from winlink.core.models import OperationType

                if (
                    self.history_manager.add_operation(
                        operation_type=OperationType.UNDO_OPERATION,
                        source=junction.source,
                        target=junction.target,
                        success=False,
                        error_message=str(e),
                    )
                    is False
                ):
                    QMessageBox.warning(
                        self,
                        "Historico",
                        "Nao foi possivel salvar o historico. Consulte o log antes de continuar.",
                    )

    def remove_file_link(self, junction: Junction):
        """Remove only the selected name after rechecking its identity."""
        reply = QMessageBox.question(
            self,
            "Remover link de arquivo",
            f"Remover apenas {junction.target}? O arquivo de origem será preservado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from winlink.core.operations import verify_junction_integrity

            if junction.source == junction.target or not verify_junction_integrity(junction):
                raise OSError(
                    "O link foi alterado ou a origem não está disponível. Atualize a lista."
                )
            junction.target.unlink()
        except OSError as exc:
            QMessageBox.critical(self, "Erro", str(exc))
            return
        if (
            self.history_manager.add_operation(
                OperationType.UNDO_OPERATION, junction.source, junction.target, success=True
            )
            is False
        ):
            QMessageBox.warning(self, "Histórico", "Não foi possível salvar o histórico.")
        self.start_scan()

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
        if self._operation_active:
            event.ignore()
            return
        if self.scan_worker is not None and self.scan_worker.isRunning():
            self.status_bar.showMessage("Aguarde o término do escaneamento para fechar.")
            event.ignore()
            return
        # Save window size if enabled
        if self.settings.remember_window_size:
            self.settings.window_width = self.width()
            self.settings.window_height = self.height()
            from winlink.core.config import save_settings

            try:
                save_settings(self.settings)
            except OSError as exc:
                self.logger.error(f"Could not save window preferences: {exc}")
        event.accept()
