"""Tests for configuration management"""

from pathlib import Path

from winlink.core.config import AppSettings, get_settings


def test_get_settings():
    """Test getting settings instance"""
    settings = get_settings()
    assert isinstance(settings, AppSettings)
    assert settings.theme_mode == "auto"
    assert len(settings.scan_directories) >= 1


def test_default_scan_directories():
    """Test default scan directories"""
    settings = AppSettings()
    assert len(settings.scan_directories) >= 1
    assert str(Path.home()) in settings.scan_directories


def test_window_settings():
    """Test window settings"""
    settings = AppSettings()
    assert settings.window_width == 1200
    assert settings.window_height == 800
    assert settings.remember_window_size is True


def test_operation_settings():
    """Test operation settings"""
    settings = AppSettings()
    assert settings.auto_backup_before_undo is True
    assert settings.confirm_before_destructive is True
    assert settings.show_notifications is True
