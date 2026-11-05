"""Main window for WinLink application"""

import logging
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QTableView,
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
    ProgressDialog,
    PropertiesDialog,
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
        self.theme_manager.setParent(self)
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
        self.theme_manager.theme_changed.connect(self.refresh_presentation)
        from winlink.core.cache import CacheManager

        cached = CacheManager().load()
        if cached and cached.scan_directories == self.settings.scan_directories:
            self.junction_model.set_junctions(cached.to_junctions())
        self.start_scan()
        self.logger.info("WinLink main window initialized")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("WinLink")
        from winlink.ui.components import ActionRow, button_style
        from winlink.ui.icons import application_icon, symbol_icon

        self.setWindowIcon(application_icon())
        self.setGeometry(100, 100, self.settings.window_width, self.settings.window_height)
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Main layout
        shell = QVBoxLayout(central_widget)
        shell.setContentsMargins(0, 0, 0, 0)
        from PyQt6.QtWidgets import QFrame, QToolButton

        header_frame = QFrame()
        header_frame.setObjectName("header")
        header = QHBoxLayout(header_frame)
        header.setContentsMargins(16, 14, 16, 14)
        header.setSpacing(12)
        logo = QLabel()
        logo.setObjectName("brandIcon")
        logo.setPixmap(symbol_icon("link", "#ffffff").pixmap(20, 20))
        logo.setFixedSize(32, 32)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo)
        brand = QLabel(
            'WinLink <span style="font-size:14px;font-weight:400;color:#6b7280">Manager</span>'
        )
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.about_button = QToolButton()
        self.about_button.setObjectName("headerIcon")
        self.about_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.about_button.setAccessibleName("Sobre WinLink")
        self.about_button.setToolTip("Sobre WinLink")
        self.about_button.clicked.connect(self.show_about)
        header.addWidget(self.about_button)
        self.quick_theme = QComboBox()
        for label, value in [("Seguir sistema", "auto"), ("Claro", "light"), ("Escuro", "dark")]:
            self.quick_theme.addItem(label, value)
        self.quick_theme.setCurrentIndex(self.quick_theme.findData(self.settings.theme_mode))
        self.quick_theme.currentIndexChanged.connect(self.change_theme)
        self.quick_theme.setAccessibleName("Tema")
        self.quick_theme.hide()
        header.addWidget(self.quick_theme)
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("headerIcon")
        self.theme_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.theme_button.clicked.connect(self.cycle_theme)
        header.addWidget(self.theme_button)
        shell.addWidget(header_frame)
        body = QHBoxLayout()
        body.setSpacing(0)
        from winlink.ui.components import NavigationList

        self.navigation = NavigationList()
        self.navigation.setObjectName("navigation")
        self.navigation.addItems(["Meus Links", "Criar Novo", "Histórico", "Configurações"])
        self.navigation.setIconSize(QSize(18, 18))
        for i in range(4):
            self.navigation.item(i).setSizeHint(QSize(160, 48))
        self.navigation.setSpacing(4)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.navigation_host = QFrame()
        self.navigation_host.setObjectName("sidebar")
        self.navigation_host.setFixedWidth(256)
        nav_box = QVBoxLayout(self.navigation_host)
        nav_box.setContentsMargins(8, 16, 8, 16)
        nav_box.setSpacing(16)
        nav_box.addWidget(self.navigation, 1)
        footer = QLabel("⌨  Navegável via teclado\n    Tab / Enter")
        footer.setObjectName("sidebarFooter")
        footer.setWordWrap(True)
        nav_box.addWidget(footer)
        body.addWidget(self.navigation_host)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        shell.addLayout(body, 1)
        list_page = QWidget()
        list_area = QScrollArea()
        list_area.setWidgetResizable(True)
        list_area.setFrameShape(QFrame.Shape.NoFrame)
        list_area.setWidget(list_page)
        self.pages.addWidget(list_area)
        main_layout = QVBoxLayout(list_page)
        left_header = QWidget()
        title_row = QHBoxLayout(left_header)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(12)
        title = QLabel("Meus Links")
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        for label, handler, icon in [
            ("Atualizar  F5", self.start_scan, "refresh"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            button_style(button, icon)
            title_row.addWidget(button)
        title_row.addStretch()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar (Ex: hosts)...")
        self.search_edit.setAccessibleName("Buscar links")
        self.search_edit.setMinimumWidth(100)
        self.search_edit.addAction(symbol_icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.search_edit.textChanged.connect(self.on_search_changed)
        # Header controls are arranged together after all controls exist.
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
        for label, link_type in [
            ("Junction", JunctionType.JUNCTION),
            ("Symlink (diretório)", JunctionType.SYMLINK),
            ("Hard link", JunctionType.HARDLINK),
            ("Symlink (arquivo)", JunctionType.SYMLINK),
        ]:
            self.type_filter.addItem(label, link_type)
        self.type_filter.currentIndexChanged.connect(self.on_filter_changed)
        self.clear_filter_btn = QPushButton("Limpar Filtros")
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.creator_filter)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.clear_filter_btn)
        filter_layout.addStretch()
        filter_container = QWidget()
        filter_container.setLayout(filter_layout)
        filter_container.hide()
        main_layout.addWidget(filter_container)
        filters_button = QPushButton("Filtros")
        filters_button.clicked.connect(self.edit_filters)
        button_style(filters_button, "filter")
        self.reset_filters_btn = button_style(QPushButton("Limpar"), "refresh")
        self.reset_filters_btn.setAccessibleName("Limpar busca e filtros")
        self.reset_filters_btn.setToolTip(
            "Limpa a busca e os filtros e atualiza a lista; mantém a ordenação."
        )
        self.reset_filters_btn.clicked.connect(self.on_home)
        from winlink.ui.link_cards import LinkCardDelegate, LinkCardView, LinkTableHeader

        self.table_view = QTableView()
        self.table_view.setHorizontalHeader(LinkTableHeader(Qt.Orientation.Horizontal))
        self.table_view.setModel(self.filter_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        header = self.table_view.horizontalHeader()
        header.setMinimumSectionSize(100)
        for column, width in enumerate((160, 160, 110, 190, 100, 115)):
            self.table_view.setColumnWidth(column, width)
        self.link_views = QStackedWidget()
        self.card_view = LinkCardView()
        self.card_view.setModel(self.filter_model)

        self.card_view.setItemDelegate(LinkCardDelegate(self.card_view))
        self.card_view.setUniformItemSizes(True)
        self.card_view.setFrameShape(QFrame.Shape.NoFrame)
        self.card_view.setMinimumHeight(240)
        self.card_view.clicked.connect(self.card_clicked)
        self.card_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.card_view.activated.connect(self.open_selected_properties)
        self.card_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.card_view.customContextMenuRequested.connect(self.show_card_context_menu)
        self.link_views.addWidget(self.card_view)
        self.link_views.addWidget(self.table_view)
        view_mode = QComboBox()
        view_mode.addItem("Visão normal", "normal")
        view_mode.addItem("Compacta", "compact")
        view_mode.setCurrentIndex(view_mode.findData(self.settings.link_view_mode))
        self.view_mode = view_mode
        view_mode.currentIndexChanged.connect(
            lambda index: self.link_views.setCurrentIndex(
                index if self.filter_model.rowCount() else 2
            )
        )
        empty = QWidget()
        empty_box = QVBoxLayout(empty)
        empty_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_box.setSpacing(16)
        empty_icon = QLabel()
        empty_icon.setPixmap(symbol_icon("search", "#9ca3af").pixmap(48, 48))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title = QLabel("Nenhum link configurado")
        self.empty_title.setObjectName("sectionTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_hint = QLabel("Verifique os filtros ou inicie a criação.")
        empty_hint.setObjectName("muted")
        empty_hint.setWordWrap(True)
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_box.addWidget(empty_icon)
        empty_box.addWidget(self.empty_title)
        empty_box.addWidget(empty_hint)
        self.link_views.addWidget(empty)
        main_layout.insertWidget(0, left_header)
        self.search_controls = ActionRow(
            [view_mode, self.search_edit, filters_button, self.reset_filters_btn]
        )
        self.search_controls.box.setStretch(1, 1)
        main_layout.insertWidget(1, self.search_controls)
        self.scan_notice = QLabel()
        self.scan_notice.setWordWrap(True)
        self.scan_notice.hide()
        main_layout.addWidget(self.scan_notice)
        self.list_summary = QLabel()
        main_layout.addWidget(self.list_summary)
        self.filter_model.modelReset.connect(self.update_list_summary)
        self.filter_model.rowsInserted.connect(self.update_list_summary)
        self.filter_model.rowsRemoved.connect(self.update_list_summary)
        main_layout.addWidget(self.link_views, 1)
        self.filter_model.sort(0, Qt.SortOrder.AscendingOrder)
        self.table_view.doubleClicked.connect(self.open_selected_properties)
        self.table_view.verticalHeader().hide()
        self.table_view.verticalHeader().setDefaultSectionSize(36)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setWordWrap(False)
        from winlink.ui.pages import CreatePage, HistoryPage, SettingsPage, embed_page

        self.create_page = CreatePage(self)
        embed_page(self.create_page, self.pages)
        self.create_page.accepted.connect(self.create_from_page)
        self.create_page.rejected.connect(lambda: self.navigate(0))
        self.history_page = HistoryPage(self.history_manager, self)
        embed_page(self.history_page, self.pages)
        self.history_page.undo_requested.connect(self.undo_junction)
        self.history_page.rejected.connect(lambda: self.navigate(0))
        self.history_page.close_btn.clicked.disconnect()
        self.history_page.close_btn.clicked.connect(lambda: self.navigate(0))
        self.settings_page = SettingsPage(self.settings, self)
        embed_page(self.settings_page, self.pages)
        self.settings_page.accepted.connect(self.settings_saved)
        self.settings_page.rejected.connect(lambda: self.navigate(0))
        self.navigation.currentRowChanged.connect(self.navigate)
        self.navigation.setCurrentRow(0)
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")
        # Menu bar
        self.update_list_summary()
        self.create_menu_bar()
        self.menuBar().hide()
        for action in self.findChildren(QAction):
            action.setShortcut(QKeySequence())
        self._shortcuts = []
        for sequence, handler in [
            ("Ctrl+N", self.on_new_junction),
            ("Ctrl+H", self.on_history),
            ("Ctrl+,", self.on_settings),
            ("Ctrl+F", self.focus_search),
            ("F5", self.start_scan),
            ("Ctrl+Q", self.close),
        ]:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def focus_search(self):
        self.navigate(0)
        self.search_edit.setFocus()

    def navigate(self, index):
        if self._operation_active:
            self.navigation.blockSignals(True)
            self.navigation.setCurrentRow(self.pages.currentIndex())
            self.navigation.blockSignals(False)
            return
        self.pages.setCurrentIndex(index)
        if self.navigation.currentRow() != index:
            self.navigation.setCurrentRow(index)
        if index == 2:
            self.history_page.load_history()

    def create_from_page(self):
        source = self.create_page.get_source_path()
        target = self.create_page.get_target_path()
        if source and target:
            self.create_link(target, source, self.create_page.get_link_type())

    def reset_creation_form(self):
        self.create_page.source_edit.clear()
        self.create_page.target_edit.clear()
        preference = self.settings.default_link_type
        self.create_page.select_type(
            {"junction": 0, "symlink_dir": 1, "symlink_file": 1, "hardlink": 2}[preference],
            preference == "symlink_file",
        )

    def settings_saved(self):
        self.view_mode.setCurrentIndex(self.view_mode.findData(self.settings.link_view_mode))
        self.apply_theme()
        self.quick_theme.setCurrentIndex(self.quick_theme.findData(self.settings.theme_mode))
        from winlink.utils.logger import setup_logger

        self.logger = setup_logger(
            level=getattr(logging, self.settings.log_level),
            log_file=self.settings.log_file,
            log_to_console=self.settings.log_to_console,
        )
        self.status_bar.showMessage("Configurações salvas")
        self.start_scan()

    def change_theme(self):
        from winlink.core.config import save_settings

        previous_mode = self.settings.theme_mode
        candidate = self.settings.model_copy(deep=True)
        candidate.theme_mode = self.quick_theme.currentData()
        try:
            save_settings(candidate)
        except OSError as exc:
            self.quick_theme.blockSignals(True)
            self.quick_theme.setCurrentIndex(self.quick_theme.findData(previous_mode))
            self.quick_theme.blockSignals(False)
            QMessageBox.warning(self, "Tema não salvo", str(exc))
            return
        self.settings.theme_mode = candidate.theme_mode
        if self.settings_page.theme_combo.currentData() == previous_mode:
            self.settings_page.theme_combo.setCurrentIndex(
                self.settings_page.theme_combo.findData(candidate.theme_mode)
            )
        self.apply_theme()

    def card_clicked(self, index):
        from PyQt6.QtGui import QCursor

        x = self.card_view.viewport().mapFromGlobal(QCursor.pos()).x()
        if x >= self.card_view.viewport().width() - 40:
            self.open_selected_properties(index)

    def refresh_presentation(self):
        from winlink.ui.icons import refresh_widget_icons, symbol_icon

        self.setStyleSheet(self.theme_manager.get_stylesheet())
        refresh_widget_icons(self)
        color = "#d1d5db" if self.theme_manager.current_theme == "dark" else "#4b5563"
        modes = ("dark", "light", "auto")
        mode = self.settings.theme_mode
        names = {"dark": "Escuro", "light": "Claro", "auto": "Seguir sistema"}
        next_mode = modes[(modes.index(mode) + 1) % len(modes)]
        self.about_button.setIcon(symbol_icon("help", color))
        self.theme_button.setIcon(
            symbol_icon({"dark": "moon", "light": "sun", "auto": "system"}[mode], color)
        )
        description = f"Tema: {names[mode]}. Alternar para {names[next_mode]}."
        self.theme_button.setAccessibleName(description)
        self.theme_button.setToolTip(description)

    def cycle_theme(self):
        modes = ("dark", "light", "auto")
        mode = modes[(modes.index(self.settings.theme_mode) + 1) % len(modes)]
        self.quick_theme.setCurrentIndex(self.quick_theme.findData(mode))

    def open_selected_properties(self, index):
        junction = self.junction_model.get_junction(self.filter_model.mapToSource(index))
        if junction:
            self.show_properties(junction)

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
        search_action.triggered.connect(lambda: (self.navigate(0), self.search_edit.setFocus()))
        view_menu.addAction(search_action)
        # Help menu
        help_menu = menubar.addMenu("&Ajuda")
        about_action = QAction("&Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_theme(self):
        """Apply theme to application"""
        self.theme_manager.apply_theme(self.settings.theme_mode)
        self.refresh_presentation()

    def start_scan(self):
        """Start scanning for junctions"""
        if self._operation_active is True:
            return
        if self.scan_worker is not None and self.scan_worker.isRunning():
            self._scan_pending = True
            return
        self._scan_pending = False
        if hasattr(self, "history_page"):
            self.history_page.load_history()
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

        if result.errors:
            self.scan_notice.setText(
                "Descoberta incompleta. A última lista disponível foi preservada. Confira os caminhos e use Atualizar para tentar novamente.\n"
                + "\n".join(result.errors)
            )
            self.scan_notice.show()
            if self.junction_model.rowCount() == 0:
                self.junction_model.set_junctions(result.junctions)
            self.status_bar.showMessage("Descoberta incompleta; consulte o aviso da lista.")
            return
        self.scan_notice.hide()
        CacheManager().save(result)
        self.junction_model.set_junctions(result.junctions)
        self.status_bar.showMessage(
            f"Escaneamento concluído: {len(result.junctions)} junções encontradas"
        )
        self.logger.info(f"Scan completed: {len(result.junctions)} junctions found")

    def on_scan_error(self, error: str):
        """Handle scan error"""
        self.scan_notice.setText(
            f"A atualização falhou. A lista anterior foi preservada. Tente Atualizar novamente.\n{error}"
        )
        self.scan_notice.show()
        self.status_bar.showMessage(f"Erro ao escanear: {error}")
        self.logger.error(f"Scan error: {error}")
        QMessageBox.critical(self, "Erro", f"Erro ao escanear junções: {error}")

    def on_search_changed(self, text: str):
        """Handle search text change"""
        self.filter_model.set_search_text(text)

    def on_filter_changed(self):
        """Handle filter change"""
        self.filter_model.set_filter_type(self.type_filter.currentData())
        self.filter_model.set_filter_directory(
            {2: True, 4: False}.get(self.type_filter.currentIndex())
        )
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
        self.navigate(0)
        self.clear_filters()
        self.start_scan()

    def on_new_junction(self):
        """Handle new junction action"""
        if self._operation_active:
            return
        preference = self.settings.default_link_type
        if not self.create_page.source_edit.text() and not self.create_page.target_edit.text():
            self.create_page.type_combo.setCurrentIndex(
                {"junction": 0, "symlink_dir": 1, "symlink_file": 1, "hardlink": 2}[preference]
            )
            self.create_page.file_symlink.setChecked(preference == "symlink_file")
        self.navigate(1)

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
            progress.set_operation_finished(success, error or "")
            if not success:
                progress.close()
        if (
            self.history_manager.add_operation(
                operation_type, source, target, success=success, error_message=error
            )
            is False
        ):
            QMessageBox.warning(
                self,
                "Histórico",
                "A operação terminou, mas o registro do histórico falhou. Confira o estado do link antes de repetir.",
            )
        if success:
            self.start_scan()
            self.reset_creation_form()

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
                    raise OSError(
                        "O Ponto de Acesso foi substituído por um link. Atualize a lista."
                    )
                if target.exists():
                    original_signature = tree_signature(target)
                    context.report(10, "Copiando arquivos...")
                    if not copy_directory_with_metadata(
                        target, source, check_cancelled=context.check_cancelled
                    ):
                        raise OSError("Falha na cópia; a pasta no Ponto de Acesso foi preservada.")
                    context.check_cancelled()
                    if tree_signature(target) != original_signature:
                        raise OSError(
                            "Os arquivos foram alterados durante a cópia. A pasta original no Ponto de Acesso foi preservada."
                        )
                    context.report(50, "Preservando a pasta no Ponto de Acesso...")
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
                                f"Falha na criação; pasta original do Ponto de Acesso preservada em {backup}"
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
                    "O registro do histórico falhou. Confira o estado do link e consulte os logs antes de repetir a operação.",
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
            self.reset_creation_form()
        except Exception as e:
            self.logger.error(f"Error creating link: {e}")
            progress.set_operation_finished(False, str(e))
            if progress.was_cancelled() is True:
                QMessageBox.information(self, "Cancelado", str(e))
            else:
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
                    "O registro do histórico falhou. Confira o estado do link e consulte os logs antes de repetir a operação.",
                )

    def on_settings(self):
        """Handle settings action"""
        self.navigate(3)

    def on_history(self):
        """Open history within the application shell."""
        self.navigate(2)

    def edit_filters(self):
        from winlink.ui.components import button_style, heading
        from winlink.ui.dialogs.animated_dialog import AnimatedDialog

        dialog = AnimatedDialog(self)
        dialog.preferred_width = 448
        dialog.setWindowTitle("Filtros da lista")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        heading(layout, "Filtrar Links", icon="filter")
        copies = []
        for label, original in [
            ("Status", self.status_filter),
            ("Criador", self.creator_filter),
            ("Tipo", self.type_filter),
        ]:
            layout.addWidget(QLabel(label))
            field = QComboBox()
            field.setAccessibleName(label)
            for index in range(original.count()):
                field.addItem(original.itemText(index))
            field.setCurrentIndex(original.currentIndex())
            layout.addWidget(field)
            copies.append((original, field))
        layout.addWidget(QLabel("Ordenar por"))
        sort_column = QComboBox()
        sort_column.setAccessibleName("Ordenar por")
        sort_column.addItems(
            ["Dados Físicos", "Ponto de Acesso", "Criador", "Tipo", "Tamanho", "Status"]
        )
        sort_column.setCurrentIndex(max(0, self.filter_model.sortColumn()))
        layout.addWidget(sort_column)
        layout.addWidget(QLabel("Ordem"))
        sort_direction = QComboBox()
        sort_direction.setAccessibleName("Ordem")
        sort_direction.addItems(["Crescente", "Decrescente"])
        sort_direction.setCurrentIndex(
            0 if self.filter_model.sortOrder() == Qt.SortOrder.AscendingOrder else 1
        )
        layout.addWidget(sort_direction)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Aplicar filtros")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(dialog.accept)
        button_style(buttons.button(QDialogButtonBox.StandardButton.Apply), "filter", primary=True)
        button_style(buttons.button(QDialogButtonBox.StandardButton.Cancel), "close")
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for original, field in copies:
                original.setCurrentIndex(field.currentIndex())
            self.filter_model.sort(
                sort_column.currentIndex(),
                (
                    Qt.SortOrder.AscendingOrder
                    if sort_direction.currentIndex() == 0
                    else Qt.SortOrder.DescendingOrder
                ),
            )

    def update_list_summary(self):
        count = self.filter_model.rowCount()
        total = self.junction_model.rowCount()
        self.list_summary.setText(f"{count} de {total} links")
        self.empty_title.setText("Busca sem resultados" if total else "Nenhum link configurado")
        self.link_views.setCurrentIndex(self.view_mode.currentIndex() if count else 2)

    def show_card_context_menu(self, position):
        index = self.card_view.indexAt(position)
        if not index.isValid():
            return
        junction = self.junction_model.get_junction(self.filter_model.mapToSource(index))
        if junction:
            menu = QMenu(self)
            from winlink.ui.icons import symbol_icon

            menu.addAction(
                symbol_icon("info"), "Propriedades", lambda: self.show_properties(junction)
            )
            menu.addAction(symbol_icon("undo"), "Desfazer", lambda: self.undo_junction(junction))
            menu.exec(self.card_view.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "navigation"):
            self.navigation_host.setFixedWidth(192 if self.width() < 1100 else 256)

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
        from winlink.ui.icons import symbol_icon

        properties_action = menu.addAction(symbol_icon("info"), "Propriedades")
        properties_action.triggered.connect(lambda: self.show_properties(junction))
        menu.addSeparator()
        undo_action = menu.addAction(symbol_icon("undo"), "Desfazer")
        undo_action.triggered.connect(lambda: self.undo_junction(junction))
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def show_properties(self, junction: Junction):
        """Show junction properties dialog"""
        dialog = PropertiesDialog(junction, self, history_manager=self.history_manager)

        def undo_from_properties(selected):
            import os

            self.undo_junction(selected)
            remaining = (
                (selected.target.is_junction() or selected.target.is_symlink())
                if selected.is_directory
                else os.path.lexists(selected.target)
            )
            if not remaining:
                dialog.accept()

        dialog.undo_requested.connect(undo_from_properties)
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
                    from winlink.core.operations import (
                        verify_directory_link_reference,
                        verify_junction_integrity,
                    )

                    intact = (
                        verify_directory_link_reference(junction)
                        if strategy == UndoStrategy.REMOVE_ONLY
                        else verify_junction_integrity(junction)
                    )
                    if not intact:
                        raise OSError(
                            "O link foi alterado ou está inacessível. Atualize a lista antes de desfazer."
                        )
                    if strategy == UndoStrategy.REMOVE_ONLY:
                        if not remove_junction(junction.target):
                            raise OSError("Não foi possível remover a junção.")
                        junction.target.mkdir(parents=True, exist_ok=True)
                        return
                    if junction.source.resolve() == junction.source.resolve().parent:
                        raise OSError("Não é permitido migrar a raiz de um volume.")
                    if not junction.source.is_dir():
                        raise OSError(
                            "Os Dados Físicos não estão disponíveis para restaurar os arquivos."
                        )
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
                                "Os Dados Físicos foram alterados durante a cópia. O link e os Dados Físicos foram preservados."
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
                                    "Arquivos restaurados; Dados Físicos preservados porque houve alterações externas."
                                )
                            if not delete_directory(junction.source):
                                raise OSError(
                                    "Arquivos restaurados; Dados Físicos preservados porque a limpeza falhou."
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
                        "O registro do histórico falhou. Confira o estado do link e consulte os logs antes de repetir a operação.",
                    )
                # Refresh scan
                self.start_scan()
                if self.settings.show_notifications is not False:
                    QMessageBox.information(self, "Sucesso", "Junção desfeita com sucesso!")
            except Exception as e:
                self.logger.error(f"Error undoing junction: {e}")
                progress.set_operation_finished(False, str(e))
                if progress.was_cancelled() is True:
                    QMessageBox.information(self, "Cancelado", str(e))
                elif "Arquivos restaurados" in str(e):
                    QMessageBox.warning(
                        self,
                        "Restauração realizada; Dados Físicos preservados",
                        f"{e}\nNão repita a reversão. Confira os caminhos preservados.",
                    )
                    self.start_scan()
                else:
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
                        "O registro do histórico falhou. Confira o estado do link e consulte os logs antes de repetir a operação.",
                    )

    def remove_file_link(self, junction: Junction):
        """Remove only the selected name after rechecking its identity."""
        reply = QMessageBox.question(
            self,
            "Remover link de arquivo",
            f"Ponto de Acesso: {junction.target}\nDados Físicos: {junction.source}\n\nRemover apenas o Ponto de Acesso? O arquivo de Dados Físicos será preservado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from winlink.core.operations import verify_junction_integrity

            if junction.source == junction.target or not verify_junction_integrity(junction):
                raise OSError(
                    "O link foi alterado ou os Dados Físicos não estão disponíveis. Atualize a lista."
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
            QMessageBox.warning(
                self,
                "Histórico",
                "A operação terminou, mas o registro do histórico falhou. Confira o estado do link antes de repetir.",
            )
        self.start_scan()

    def show_about(self):
        from winlink.ui.components import button_style, heading
        from winlink.ui.dialogs.animated_dialog import AnimatedDialog

        dialog = AnimatedDialog(self)
        dialog.preferred_width = 560
        dialog.setWindowTitle("Sobre WinLink")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        heading(layout, "Sobre WinLink", icon="link")
        text = QLabel(
            "WinLink Manager · Versão 0.1.4\n\nGerenciador de junctions, links simbólicos e hard links para Windows.\n\nCtrl+N: criar\nCtrl+H: histórico\nCtrl+,: configurações\nCtrl+F: buscar\nF5: atualizar\nCtrl+Q: sair\n\nLicença MIT · Copyright (c) 2026 Steff Martin."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        project_link = QLabel(
            '<a href="https://github.com/steffmartin/win-link">GitHub do projeto WinLink</a>'
        )
        project_link.setOpenExternalLinks(True)
        project_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        project_link.setAccessibleName("GitHub do projeto WinLink")
        project_link.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(project_link)
        close = button_style(QPushButton("Fechar"), "close")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)
        dialog.exec()

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
