"""Tests for theme management"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication

from winlink.core.models import Junction, JunctionStatus, JunctionType
from winlink.ui.dialogs.properties_dialog import PropertiesDialog
from winlink.ui.junction_model import JunctionTableModel
from winlink.ui.theme import (
    ThemeColors,
    ThemeManager,
    junction_status_color,
)


@pytest.fixture
def app(qtbot):
    """Fixture for QApplication"""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def theme_manager():
    """Fixture for ThemeManager"""
    return ThemeManager()


def test_theme_manager_initialization(theme_manager):
    """Test ThemeManager initialization"""
    assert theme_manager.current_theme in ["light", "dark"]
    assert theme_manager.mode == "auto"


def test_get_system_theme(theme_manager):
    """Test system theme detection"""
    theme = theme_manager.get_system_theme()
    assert theme in ["light", "dark"]


def test_get_theme_colors_light(theme_manager):
    """Test getting light theme colors"""
    colors = theme_manager.get_theme_colors("light")
    assert "background" in colors
    assert "surface" in colors
    assert "primary" in colors
    assert "text" in colors


def test_get_theme_colors_dark(theme_manager):
    """Test getting dark theme colors"""
    colors = theme_manager.get_theme_colors("dark")
    assert "background" in colors
    assert "surface" in colors
    assert "primary" in colors
    assert "text" in colors


def test_apply_theme_light(theme_manager, app):
    """Test applying light theme"""
    theme_manager.apply_theme("light")
    assert theme_manager.current_theme == "light"
    assert theme_manager.mode == "light"


def test_apply_theme_dark(theme_manager, app):
    """Test applying dark theme"""
    theme_manager.apply_theme("dark")
    assert theme_manager.current_theme == "dark"
    assert theme_manager.mode == "dark"


def test_apply_theme_auto(theme_manager, app):
    """Test applying auto theme"""
    theme_manager.apply_theme("auto")
    assert theme_manager.mode == "auto"
    assert theme_manager.current_theme in ["light", "dark"]


def test_get_stylesheet(theme_manager):
    """Test getting stylesheet"""
    stylesheet = theme_manager.get_stylesheet()
    assert isinstance(stylesheet, str)
    assert len(stylesheet) > 0
    assert "QMainWindow" in stylesheet
    assert "QWidget" in stylesheet
    assert "QPushButton" in stylesheet


def test_theme_colors_constants():
    """Test theme color constants"""
    assert hasattr(ThemeColors, "LIGHT")
    assert hasattr(ThemeColors, "DARK")

    # Check light theme has required colors
    light_colors = ThemeColors.LIGHT
    required_keys = [
        "background",
        "surface",
        "primary",
        "text",
        "success",
        "warning",
        "error",
    ]
    for key in required_keys:
        assert key in light_colors

    # Check dark theme has required colors
    dark_colors = ThemeColors.DARK
    for key in required_keys:
        assert key in dark_colors


@pytest.mark.parametrize(
    ("theme", "status", "expected"),
    [
        ("light", JunctionStatus.INACCESSIBLE, "#9b8f06"),
        ("light", JunctionStatus.BROKEN, "#c42b1a"),
        ("dark", JunctionStatus.INACCESSIBLE, "#e2d868"),
        ("dark", JunctionStatus.BROKEN, "#ff8a80"),
    ],
)
def test_status_colors_match_table_and_properties(app, theme, status, expected):
    original_palette = app.palette()
    palette = QPalette(original_palette)
    colors = ThemeColors.DARK if theme == "dark" else ThemeColors.LIGHT
    palette.setColor(QPalette.ColorRole.Window, colors["background"])
    app.setPalette(palette)
    try:
        junction = Junction(
            source="C:/physical",
            target="C:/link",
            junction_type=JunctionType.JUNCTION,
            status=status,
        )
        model = JunctionTableModel()
        model.set_junctions([junction])
        color = model.data(model.index(0, 6), Qt.ItemDataRole.ForegroundRole)

        assert color == junction_status_color(status)
        assert color.name() == expected
        assert PropertiesDialog.get_status_color(None, status) == expected
    finally:
        app.setPalette(original_palette)
