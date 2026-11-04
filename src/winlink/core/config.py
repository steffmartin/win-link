"""Configuration management for WinLink"""

import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScanDirectory(StrEnum):
    """Predefined scan directories"""

    USER_PROFILE = "USER_PROFILE"
    CACHE = "CACHE"
    CUSTOM = "CUSTOM"


class AppSettings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WINLINK_",
        extra="ignore",
    )

    # Theme
    theme_mode: Literal["auto", "light", "dark"] = "auto"

    default_link_type: Literal["junction", "symlink_dir", "symlink_file", "hardlink"] = "junction"

    # Scan directories
    scan_directories: list[str] = Field(
        default_factory=lambda: [
            str(Path.home()),
            "D:\\Cache",
        ]
    )

    # History
    max_history_entries: int = Field(default=1000, ge=1)
    history_file: Path = Field(default_factory=lambda: settings_path().with_name("history.json"))

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: Path = Field(default_factory=lambda: settings_path().with_name("winlink.log"))
    log_to_console: bool = True

    # UI
    window_width: int = 1200
    window_height: int = 800
    remember_window_size: bool = True

    # Operations
    auto_backup_before_undo: bool = True
    confirm_before_destructive: bool = True
    show_notifications: bool = True
    warn_nested_junctions: bool = True


def settings_path() -> Path:
    """Return the per-user configuration location."""
    return (
        Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        / "WinLink"
        / "config.json"
    )


def get_appdata_path() -> Path:
    """Return the APPDATA directory for WinLink."""
    return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "WinLink"


def save_settings(settings: AppSettings, path: Path | None = None) -> None:
    """Persist settings atomically; propagate errors to the caller."""
    path = path or settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
    temporary.replace(path)


def get_settings() -> AppSettings:
    """
    Get application settings instance.

    Returns:
        AppSettings instance
    """
    path = settings_path()
    if path.exists():
        try:
            return AppSettings(**json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            # Preserve invalid files for diagnosis and allow the application to start.
            pass
    return AppSettings()
