"""Configuration management for WinLink"""

from enum import Enum
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScanDirectory(str, Enum):
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
    theme_mode: str = "auto"  # auto, light, dark

    # Scan directories
    scan_directories: List[str] = Field(
        default_factory=lambda: [
            str(Path.home()),
            "D:\\Cache",
        ]
    )

    # History
    max_history_entries: int = 1000
    history_file: Path = Field(
        default_factory=lambda: Path.home() / "AppData" / "Roaming" / "WinLink" / "history.json"
    )

    # Logging
    log_level: str = "INFO"
    log_file: Path = Field(
        default_factory=lambda: Path.home() / "AppData" / "Roaming" / "WinLink" / "winlink.log"
    )
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


def get_settings() -> AppSettings:
    """
    Get application settings instance.

    Returns:
        AppSettings instance
    """
    return AppSettings()
