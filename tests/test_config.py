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
    assert settings.warn_nested_junctions is True


def test_settings_persist_and_reload(monkeypatch, tmp_path):
    from winlink.core.config import save_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings = AppSettings(theme_mode="dark", scan_directories=[str(tmp_path)])
    save_settings(settings)
    loaded = get_settings()
    assert loaded.theme_mode == "dark"
    assert loaded.scan_directories == [str(tmp_path)]


def test_invalid_settings_file_is_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = tmp_path / "WinLink" / "config.json"
    path.parent.mkdir()
    path.write_text("broken")
    assert isinstance(get_settings(), AppSettings)
    assert path.read_text() == "broken"


def test_invalid_configuration_values_are_rejected():
    import pytest
    from pydantic import ValidationError
    for values in [{"theme_mode": "unknown"}, {"log_level": "invalid"}, {"max_history_entries": 0}]:
        with pytest.raises(ValidationError):
            AppSettings(**values)
