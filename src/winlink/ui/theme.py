"""Theme management for Windows 11 style UI"""

import sys
import winreg
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from winlink.utils.logger import get_logger


class ThemeColors:
    """Color palettes for the link-management workspace."""

    LIGHT = {
        "background": QColor("#F1F4F4"),
        "surface": QColor("#FFFFFF"),
        "surface_variant": QColor("#E8EFEF"),
        "primary": QColor("#126E78"),
        "primary_hover": QColor("#0F6069"),
        "primary_pressed": QColor("#0B5058"),
        "primary_container": QColor("#D6EBE9"),
        "on_primary": QColor("#FFFFFF"),
        "text": QColor("#19282D"),
        "text_secondary": QColor("#52646A"),
        "border": QColor("#C8D4D7"),
        "success": QColor("#14735D"),
        "success_container": QColor("#D9F0E7"),
        "warning": QColor("#86560A"),
        "warning_container": QColor("#F8EBD0"),
        "error": QColor("#B42332"),
        "error_container": QColor("#F8DEE0"),
    }

    DARK = {
        "background": QColor("#111D23"),
        "surface": QColor("#1C2A31"),
        "surface_variant": QColor("#2A3A41"),
        "primary": QColor("#75C9C1"),
        "primary_hover": QColor("#89D9D2"),
        "primary_pressed": QColor("#58B4AC"),
        "primary_container": QColor("#23494B"),
        "on_primary": QColor("#10292B"),
        "text": QColor("#EDF4F4"),
        "text_secondary": QColor("#ADBDC0"),
        "border": QColor("#42555B"),
        "success": QColor("#82D2AE"),
        "success_container": QColor("#183B33"),
        "warning": QColor("#F2C56E"),
        "warning_container": QColor("#4A3B20"),
        "error": QColor("#FF9299"),
        "error_container": QColor("#4B252A"),
    }


def junction_status_color(status) -> QColor:
    """Theme-aware color for a junction status (success/error/warning tokens)."""
    from winlink.core.models import JunctionStatus

    app = QApplication.instance()
    dark = app is not None and app.palette().window().color().lightness() < 128
    palette = ThemeColors.DARK if dark else ThemeColors.LIGHT
    if status == JunctionStatus.ACTIVE:
        return palette["success"]
    if status == JunctionStatus.BROKEN:
        return palette["error"]
    if status == JunctionStatus.INACCESSIBLE:
        return palette["warning"]
    return palette["text"]


class ThemeManager(QObject):
    """Manages application theme following Windows 11 system theme"""

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self._current_theme = "light"
        self._mode = "auto"
        self._system_timer = QTimer(self)
        self._system_timer.setInterval(2000)
        self._system_timer.timeout.connect(self.refresh_system_theme)
        self._system_timer.start()

    def refresh_system_theme(self):
        if self._mode == "auto" and self.get_system_theme() != self._current_theme:
            self.apply_theme("auto")

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
        palette.setColor(QPalette.ColorRole.Mid, colors["border"])
        palette.setColor(QPalette.ColorRole.WindowText, colors["text"])
        palette.setColor(QPalette.ColorRole.PlaceholderText, colors["text_secondary"])
        palette.setColor(QPalette.ColorRole.Link, colors["primary"])
        palette.setColor(QPalette.ColorRole.BrightText, colors["error"])

        # Base colors (for widgets)
        palette.setColor(QPalette.ColorRole.Base, colors["surface"])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors["surface_variant"])
        palette.setColor(QPalette.ColorRole.Text, colors["text"])

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, colors["surface"])
        palette.setColor(QPalette.ColorRole.ButtonText, colors["text"])
        palette.setColor(QPalette.ColorRole.Light, colors["surface_variant"])
        palette.setColor(QPalette.ColorRole.Dark, colors["border"])

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, colors["primary"])
        palette.setColor(QPalette.ColorRole.HighlightedText, colors["on_primary"])
        for role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText,
            QPalette.ColorRole.PlaceholderText,
        ):
            palette.setColor(QPalette.ColorGroup.Disabled, role, colors["text_secondary"])

        # Apply palette
        QApplication.instance().setPalette(palette)

        # Emit signal
        self.theme_changed.emit(self._current_theme)

    def get_stylesheet(self) -> str:
        colors = self.get_theme_colors()

        def color(name: str) -> str:
            return str(colors[name].name())

        bg = color("background")
        surface = color("surface")
        variant = color("surface_variant")
        primary = color("primary")
        primary_hover = color("primary_hover")
        primary_pressed = color("primary_pressed")
        primary_container = color("primary_container")
        on_primary = color("on_primary")
        text = color("text")
        secondary = color("text_secondary")
        border = color("border")

        assets = (
            Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3] / "resources")) / "ui"
        )
        arrow = (assets / "chevron-down.svg").as_posix()
        arrow_up = (assets / "chevron-up.svg").as_posix()
        radio_off = (assets / "radio-off.svg").as_posix()
        radio_on = (assets / "radio-on.svg").as_posix()
        checkbox_off = (assets / "checkbox-off.svg").as_posix()
        checkbox_on = (assets / "checkbox-on.svg").as_posix()
        checkbox_disabled = (assets / "checkbox-disabled.svg").as_posix()
        return f"""
        QWidget {{
            background-color: {bg};
            color: {text};
            font-family: "Segoe UI";
            font-size: 14px;
        }}
        QMainWindow, QDialog {{ background-color: {bg}; }}
        QLabel {{ background: transparent; }}
        QFrame#header {{ background: {bg}; border-bottom: 1px solid {border}; }}
        QLabel#brand {{ font-size: 20px; font-weight: 700; }}
        QLabel#brandDescriptor {{ color: {secondary}; font-size: 13px; }}
        QLabel#brandIcon {{ background: {primary}; border-radius: 7px; }}
        QLabel#pageTitle {{ font-size: 24px; font-weight: 700; }}
        QLabel#sectionTitle {{ font-size: 20px; font-weight: 700; }}
        QLabel#fieldLabel {{ font-size: 14px; font-weight: 600; }}
        QLabel#muted {{ color: {secondary}; font-size: 13px; }}
        QLabel#pathText {{ font-family: Consolas; font-size: 12px; }}
        QLabel#undoPaths {{ padding: 10px 12px; background: {variant};
            border-radius: 5px; font-weight: 600; }}
        QLabel#strategyDescription {{ color: {secondary}; font-size: 12px;
            margin-left: 28px; }}
        QLabel#warningText {{ color: {color("warning")}; background: {color("warning_container")};
            border: 1px solid {border}; border-radius: 5px; padding: 10px 12px; }}
        QLabel#spaceLabel {{ color: {secondary}; margin: 8px 0; }}
        QLabel#progressStatus {{ font-size: 15px; font-weight: 600; margin: 8px 0; }}
        QLabel#progressDetails {{ color: {secondary}; margin: 4px 0; }}
        QLabel#sidebarFooter {{ color: {secondary}; background: transparent;
            border-top: 1px solid {border}; padding-top: 16px; font-size: 11px; }}
        QFrame#sidebar {{ background: {surface}; border-right: 1px solid {border}; }}
        QListWidget#navigation {{ background: transparent; border: none; padding: 0;
            font-size: 14px; font-weight: 600; }}
        QListWidget#navigation::item {{ padding: 10px 8px; border-radius: 6px; }}
        QListWidget#navigation::item:hover {{ background: {variant}; }}
        QListWidget#navigation::item:selected {{ background: {primary_container}; color: {primary}; }}
        QListWidget#navigation:focus {{ outline: none; }}
        QPushButton {{ min-height: 20px; padding: 8px 14px; border: 1px solid {border};
            border-radius: 6px; background: {surface}; color: {text}; font-weight: 500; }}
        QPushButton:hover, QToolButton:hover {{ background: {variant}; }}
        QPushButton:pressed, QToolButton:pressed {{ background: {primary_container}; }}
        QPushButton:disabled {{ background: {variant}; color: {secondary}; border-color: {border}; }}
        QPushButton:focus, QToolButton:focus, QComboBox:focus, QLineEdit:focus,
        QPlainTextEdit:focus, QTextEdit:focus, QListWidget:focus, QTableView:focus {{
            border: 2px solid {primary};
        }}
        QPushButton[primary="true"] {{ background: {primary}; color: {on_primary};
            border-color: {primary}; padding: 9px 16px; font-weight: 600; }}
        QPushButton[primary="true"]:hover {{ background: {primary_hover}; border-color: {primary_hover}; }}
        QPushButton[primary="true"]:pressed {{ background: {primary_pressed}; border-color: {primary_pressed}; }}
        QPushButton[primary="true"]:disabled {{ background: {variant}; color: {secondary}; border-color: {border}; }}
        QPushButton[danger="true"] {{ color: {color("error")}; border-color: {color("error")}; }}
        QPushButton[danger="true"]:hover {{ background: {color("error_container")}; }}
        QPushButton#typeCard {{ min-height: 110px; max-height: 110px; padding: 0;
            border-radius: 7px; background: {surface}; text-align: left; }}
        QPushButton#typeCard:checked {{ background: {primary_container}; border: 2px solid {primary}; }}
        QPushButton#typeCard:focus {{ border: 2px solid {primary}; }}
        QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QDateTimeEdit {{
            min-height: 20px; padding: 8px 10px; border: 1px solid {border};
            border-radius: 5px; background: {surface}; selection-background-color: {primary};
            selection-color: {on_primary};
        }}
        QPlainTextEdit#pathBlock {{ font-family: Consolas; padding: 12px;
            background: {variant}; border-radius: 5px; }}
        QLineEdit#pathInput {{ font-family: Consolas; font-size: 13px; }}
        QComboBox {{ padding-right: 28px; }}
        QComboBox:hover, QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover {{ border-color: {primary}; }}
        QComboBox::drop-down {{ width: 24px; border: none; }}
        QComboBox::down-arrow {{ image: url("{arrow}"); width: 16px; height: 16px; }}
        QDateTimeEdit::up-button, QDateTimeEdit::down-button {{ background: transparent;
            border: none; width: 22px; }}
        QDateTimeEdit::up-arrow {{ image: url("{arrow_up}"); width: 16px; height: 16px; }}
        QDateTimeEdit::down-arrow {{ image: url("{arrow}"); width: 16px; height: 16px; }}
        QComboBox QAbstractItemView {{ padding: 4px; background: {surface};
            selection-background-color: {primary_container}; selection-color: {text}; }}
        QToolButton#headerIcon {{ min-width: 28px; min-height: 28px; border: 1px solid transparent;
            border-radius: 16px; padding: 4px; }}
        QToolButton#headerIcon:focus {{ border: 2px solid {primary}; }}
        QToolButton {{ background: transparent; border: 1px solid transparent;
            border-radius: 4px; padding: 3px; }}
        QToolButton#headerIcon::menu-button {{ border: none; width: 12px; background: transparent; }}
        QToolButton#headerIcon::menu-arrow {{ image: url("{arrow}"); width: 12px; height: 12px; }}
        QWidget#fieldContainer {{ background: transparent; }}
        QFrame#panel, QFrame#structurePanel {{ background: {surface};
            border: 1px solid {border}; border-radius: 8px; }}
        QFrame#structureNode {{ background: {bg}; border: 1px solid {border}; border-radius: 7px; }}
        QLabel#infoBanner {{ padding: 14px; background: {primary_container};
            border: 1px solid {border}; border-radius: 6px; }}
        QTableView {{ background: {surface}; alternate-background-color: {variant};
            border: 1px solid {border}; border-radius: 6px; gridline-color: {border}; }}
        QTableView::item {{ padding: 6px; }}
        QTableView::item:selected {{ background: {primary_container}; color: {text}; }}
        QHeaderView::section {{ border: none; border-bottom: 1px solid {border};
            padding: 10px; background: {variant}; font-weight: 600; }}
        QGroupBox {{ background: {surface}; border: 1px solid {border}; border-radius: 6px;
            margin-top: 14px; padding: 20px 12px 12px; font-weight: 600; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        QRadioButton::indicator {{ width: 20px; height: 20px; image: url("{radio_off}"); }}
        QRadioButton::indicator:checked {{ image: url("{radio_on}"); }}
        QCheckBox::indicator {{ width: 20px; height: 20px; image: url("{checkbox_off}"); }}
        QCheckBox::indicator:checked {{ image: url("{checkbox_on}"); }}
        QCheckBox::indicator:checked:disabled {{ image: url("{checkbox_disabled}"); }}
        QRadioButton {{ background: transparent; spacing: 10px; padding: 8px 4px; }}
        QCheckBox {{ background: transparent; spacing: 10px; padding: 4px 0; }}
        QCheckBox:disabled {{ color: {secondary}; }}
        QProgressBar {{ background: {surface}; border: 1px solid {border}; border-radius: 4px;
            min-height: 18px; text-align: center; }}
        QProgressBar::chunk {{ background: {primary}; border-radius: 3px; }}
        QStatusBar {{ background: {surface}; color: {text}; border-top: 1px solid {border}; }}
        QMenuBar, QMenu {{ background: {surface}; color: {text}; }}
        QMenu {{ border: 1px solid {border}; padding: 4px; }}
        QMenu::item {{ padding: 7px 24px; }}
        QMenu::item:selected, QMenuBar::item:selected {{ background: {primary_container}; }}
        QToolBar {{ background: {surface}; border: 1px solid {border}; spacing: 4px; }}
        QTabWidget::pane {{ border: 1px solid {border}; background: {bg}; }}
        QTabBar::tab {{ background: {surface}; color: {text}; border: 1px solid {border};
            border-bottom: none; padding: 8px 16px; margin-right: 2px; }}
        QTabBar::tab:selected {{ background: {bg}; }}
        QTabBar::tab:hover {{ background: {variant}; }}
        QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px;
            min-height: 24px; }}
        QScrollBar::handle:vertical:hover {{ background: {secondary}; }}
        QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
        QScrollBar::handle:horizontal {{ background: {border}; border-radius: 5px;
            min-width: 24px; }}
        QScrollBar::handle:horizontal:hover {{ background: {secondary}; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
        QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
        """

    @property
    def current_theme(self) -> str:
        """Get current theme name"""
        return str(self._current_theme)

    @property
    def mode(self) -> str:
        """Get theme mode (auto/light/dark)"""
        return str(self._mode)
