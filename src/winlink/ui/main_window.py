"""Main window for WinLink application"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from winlink.utils.logger import get_logger
from winlink.core.config import get_settings


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.settings = get_settings()

        self.init_ui()
        self.logger.info("WinLink main window initialized")

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("WinLink - Gerenciador de Junções NTFS")
        self.setGeometry(100, 100, self.settings.window_width, self.settings.window_height)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout(central_widget)

        # Welcome label
        welcome_label = QLabel("WinLink - Gerenciador de Junções NTFS")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        # Status label
        status_label = QLabel("Sistema configurado com sucesso!")
        status_label.setStyleSheet("font-size: 14px; margin: 10px;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        # Test button
        test_button = QPushButton("Testar Configuração")
        test_button.clicked.connect(self.test_configuration)
        layout.addWidget(test_button)

        # Menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&Arquivo")

        exit_action = QAction("&Sair", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Ajuda")

        about_action = QAction("&Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def test_configuration(self):
        """Test configuration"""
        self.logger.info("Testing configuration...")

        try:
            # Test settings
            self.logger.info(f"Theme mode: {self.settings.theme_mode}")
            self.logger.info(f"Scan directories: {self.settings.scan_directories}")
            self.logger.info(f"Log level: {self.settings.log_level}")

            QMessageBox.information(
                self,
                "Configuração",
                "Configuração testada com sucesso!\n\n"
                f"Theme: {self.settings.theme_mode}\n"
                f"Directórios de escaneamento: {len(self.settings.scan_directories)}\n"
                f"Nível de log: {self.settings.log_level}",
            )
            self.logger.info("Configuration test passed")
        except Exception as e:
            self.logger.error(f"Configuration test failed: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao testar configuração: {e}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Sobre WinLink",
            "WinLink - Gerenciador de Junções NTFS\n\n"
            "Versão 0.1.0\n\n"
            "Aplicativo Windows para gerenciamento de junções NTFS "
            "e links simbólicos com interface moderna compatível com Windows 11.",
        )
