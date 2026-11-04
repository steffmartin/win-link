"""Theme management for Windows 11 style UI"""

import winreg

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from winlink.utils.logger import get_logger


class ThemeColors:
    """Color palettes for light and dark themes"""

    # Light theme (Windows 11)
    LIGHT = {
        "background": QColor("#FFFFFF"),
        "surface": QColor("#F3F3F3"),
        "surface_variant": QColor("#EDEDED"),
        "primary": QColor("#0067C0"),
        "primary_container": QColor("#D0E4FF"),
        "on_primary": QColor("#FFFFFF"),
        "text": QColor("#1A1A1A"),
        "text_secondary": QColor("#5C5C5C"),
        "border": QColor("#E5E5E5"),
        "success": QColor("#107C10"),
        "warning": QColor("#9B8F06"),
        "error": QColor("#C42B1A"),
    }

    # Dark theme (Windows 11)
    DARK = {
        "background": QColor("#202020"),
        "surface": QColor("#2B2B2B"),
        "surface_variant": QColor("#333333"),
        "primary": QColor("#4CC2FF"),
        "primary_container": QColor("#004275"),
        "on_primary": QColor("#000000"),
        "text": QColor("#FFFFFF"),
        "text_secondary": QColor("#D0D0D0"),
        "border": QColor("#404040"),
        "success": QColor("#6CCB6F"),
        "warning": QColor("#E2D868"),
        "error": QColor("#FF8A80"),
    }


class ThemeManager(QObject):
    """Manages application theme following Windows 11 system theme"""

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self._current_theme = "light"
        self._mode = "auto"

    def get_system_theme(self) -> str:
        """
        Detect Windows system theme from registry.

        Returns:
            "light" or "dark"
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)

            # 0 = dark, 1 = light
            return "light" if value == 1 else "dark"
        except Exception as e:
            self.logger.warning(f"Failed to detect system theme: {e}")
            return "light"

    def get_theme_colors(self, theme: str | None = None) -> dict:
        """
        Get color palette for a theme.

        Args:
            theme: "light" or "dark". If None, uses current theme.

        Returns:
            Dictionary of QColor objects
        """
        if theme is None:
            theme = self._current_theme

        return ThemeColors.LIGHT if theme == "light" else ThemeColors.DARK

    def apply_theme(self, mode: str = "auto", theme: str | None = None) -> None:
        """
        Apply theme to application.

        Args:
            mode: "auto", "light", or "dark"
            theme: Specific theme to apply (if mode is not "auto")
        """
        self._mode = mode

        if mode == "auto":
            self._current_theme = self.get_system_theme()
        else:
            self._current_theme = mode

        self.logger.info(f"Applying theme: {self._current_theme} (mode: {mode})")

        # Get colors
        colors = self.get_theme_colors()

        # Create palette
        palette = QPalette()

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, colors["background"])
        palette.setColor(QPalette.ColorRole.WindowText, colors["text"])

        # Base colors (for widgets)
        palette.setColor(QPalette.ColorRole.Base, colors["surface"])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors["surface_variant"])
        palette.setColor(QPalette.ColorRole.Text, colors["text"])

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, colors["surface"])
        palette.setColor(QPalette.ColorRole.ButtonText, colors["text"])

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, colors["primary"])
        palette.setColor(QPalette.ColorRole.HighlightedText, colors["on_primary"])

        # Apply palette
        QApplication.instance().setPalette(palette)

        # Emit signal
        self.theme_changed.emit(self._current_theme)

    def get_stylesheet(self) -> str:
        """
        Get QSS stylesheet for current theme.

        Returns:
            QSS stylesheet string
        """
        colors = self.get_theme_colors()

        # Convert QColor to hex strings
        def to_hex(color: QColor) -> str:
            return str(color.name())

        bg = to_hex(colors["background"])
        surface = to_hex(colors["surface"])
        surface_variant = to_hex(colors["surface_variant"])
        primary = to_hex(colors["primary"])
        primary_container = to_hex(colors["primary_container"])
        on_primary = to_hex(colors["on_primary"])
        text = to_hex(colors["text"])
        text_secondary = to_hex(colors["text_secondary"])
        border = to_hex(colors["border"])

        stylesheet = f"""
        QMainWindow {{
            background-color: {bg};
        }}

        QWidget {{
            background-color: {bg};
            color: {text};
            font-family: "Segoe UI";
            font-size: 14px;
        }}

        QPushButton {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 6px 12px;
            color: {text};
        }}

        QPushButton:hover {{
            background-color: {surface_variant};
        }}

        QPushButton:pressed {{
            background-color: {primary_container};
        }}

        QPushButton:disabled {{
            background-color: {surface_variant};
            color: {text_secondary};
        }}

        QLineEdit {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 6px;
            color: {text};
        }}

        QLineEdit:focus {{
            border: 1px solid {primary};
        }}

        QTableView {{
            background-color: {bg};
            alternate-background-color: {surface};
            border: 1px solid {border};
            gridline-color: {border};
        }}

        QTableView::item {{
            padding: 4px;
        }}

        QTableView::item:selected {{
            background-color: {primary};
            color: {on_primary};
        }}

        QHeaderView::section {{
            background-color: {surface};
            color: {text};
            padding: 6px;
            border: 1px solid {border};
            border-bottom: 2px solid {primary};
            font-weight: bold;
        }}

        QGroupBox {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }}

        QStatusBar {{
            background-color: {surface};
            color: {text};
            border-top: 1px solid {border};
        }}

        QMenuBar {{
            background-color: {surface};
            color: {text};
        }}

        QMenuBar::item {{
            padding: 6px 12px;
        }}

        QMenuBar::item:selected {{
            background-color: {primary_container};
        }}

        QMenu {{
            background-color: {surface};
            border: 1px solid {border};
        }}

        QMenu::item {{
            padding: 6px 24px;
        }}

        QMenu::item:selected {{
            background-color: {primary_container};
        }}

        QToolBar {{
            background-color: {surface};
            border: 1px solid {border};
            spacing: 4px;
        }}

        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px;
        }}

        QToolButton:hover {{
            background-color: {surface_variant};
        }}

        QToolButton:pressed {{
            background-color: {primary_container};
        }}

        QComboBox {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px;
        }}

        QComboBox:hover {{
            border: 1px solid {primary};
        }}

        QComboBox::drop-down {{
            border: none;
        }}

        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}

        QLabel {{
            color: {text};
        }}

        QCheckBox {{
            spacing: 6px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {border};
            border-radius: 3px;
            background-color: {surface};
        }}

        QCheckBox::indicator:checked {{
            background-color: {primary};
            border: 1px solid {primary};
        }}

        QRadioButton {{
            spacing: 6px;
        }}

        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {border};
            border-radius: 9px;
            background-color: {surface};
        }}

        QRadioButton::indicator:checked {{
            background-color: {primary};
            border: 2px solid {primary};
        }}

        QProgressBar {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 3px;
        }}

        QTabWidget::pane {{
            border: 1px solid {border};
            background-color: {bg};
        }}

        QTabBar::tab {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {bg};
            border-bottom: 1px solid {bg};
        }}

        QTabBar::tab:hover {{
            background-color: {surface_variant};
        }}

        QDockWidget {{
            background-color: {surface};
            border: 1px solid {border};
            titlebar-close-icon: url(close.png);
        }}

        QDockWidget::title {{
            background-color: {surface_variant};
            padding: 6px;
            font-weight: bold;
        }}

        QScrollBar:vertical {{
            background-color: {surface};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {text_secondary};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {text};
        }}

        QScrollBar:horizontal {{
            background-color: {surface};
            height: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {text_secondary};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {text};
        }}
        """

        return stylesheet

    @property
    def current_theme(self) -> str:
        """Get current theme name"""
        return str(self._current_theme)

    @property
    def mode(self) -> str:
        """Get theme mode (auto/light/dark)"""
        return str(self._mode)
