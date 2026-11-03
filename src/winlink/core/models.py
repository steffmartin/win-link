"""Data models for WinLink junction management"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_serializer


class JunctionType(str, Enum):
    """Type of junction/link"""

    JUNCTION = "JUNCTION"
    SYMLINK = "SYMLINK"
    HARDLINK = "HARDLINK"


class JunctionStatus(str, Enum):
    """Status of a junction"""

    ACTIVE = "ACTIVE"
    BROKEN = "BROKEN"
    INACCESSIBLE = "INACCESSIBLE"


class Creator(str, Enum):
    """Who created the junction"""

    APP = "APP"
    EXISTING = "EXISTING"
    MANUAL = "MANUAL"


class UndoStrategy(str, Enum):
    """Strategy for undoing a junction"""

    REMOVE_ONLY = "REMOVE_ONLY"
    MOVE_BACK = "MOVE_BACK"
    DUPLICATE = "DUPLICATE"
    KEEP_SOURCE = "KEEP_SOURCE"


class Junction(BaseModel):
    """Represents a junction/symlink/hardlink"""

    source: Path = Field(description="Path where files actually exist")
    target: Path = Field(description="Path of the junction/symlink")
    junction_type: JunctionType = Field(description="Type of junction")
    status: JunctionStatus = Field(default=JunctionStatus.ACTIVE, description="Current status")
    creator: Creator = Field(default=Creator.EXISTING, description="Who created it")
    created_at: Optional[datetime] = Field(default=None, description="When it was created")
    size_bytes: Optional[int] = Field(default=None, description="Total size in bytes")
    is_directory: bool = Field(default=True, description="Whether it's a directory")

    @field_serializer("source", "target")
    def serialize_path(self, value: Path) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class OperationType(str, Enum):
    """Type of operation performed"""

    CREATE_JUNCTION = "CREATE_JUNCTION"
    CREATE_SYMLINK = "CREATE_SYMLINK"
    CREATE_HARDLINK = "CREATE_HARDLINK"
    REMOVE_JUNCTION = "REMOVE_JUNCTION"
    UNDO_OPERATION = "UNDO_OPERATION"
    MOVE_FILES = "MOVE_FILES"
    COPY_FILES = "COPY_FILES"


class OperationRecord(BaseModel):
    """Record of an operation in the history"""

    operation_type: OperationType = Field(description="Type of operation")
    source: Optional[Path] = Field(default=None, description="Source path involved")
    target: Optional[Path] = Field(default=None, description="Target path involved")
    timestamp: datetime = Field(default_factory=datetime.now, description="When operation occurred")
    success: bool = Field(default=True, description="Whether operation succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Additional operation metadata")

    @field_serializer("source", "target")
    def serialize_path(self, value: Optional[Path]) -> Optional[str]:
        return str(value) if value else None

    @field_serializer("timestamp")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class ScanResult(BaseModel):
    """Result of scanning for junctions"""

    junctions: list[Junction] = Field(default_factory=list, description="Found junctions")
    scanned_directories: list[Path] = Field(default_factory=list, description="Directories scanned")
    scan_duration_seconds: float = Field(default=0.0, description="Time taken to scan")
    errors: list[str] = Field(default_factory=list, description="Errors encountered during scan")


class ValidationResult(BaseModel):
    """Result of validation checks"""

    is_valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
