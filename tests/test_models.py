"""Tests for data models"""

from datetime import datetime
from pathlib import Path

from winlink.core.models import (
    Creator,
    Junction,
    JunctionStatus,
    JunctionType,
    OperationRecord,
    OperationType,
    ScanResult,
    UndoStrategy,
    ValidationResult,
)


def test_junction_type_enum():
    """Test JunctionType enum values"""
    assert JunctionType.JUNCTION.value == "JUNCTION"
    assert JunctionType.SYMLINK.value == "SYMLINK"
    assert JunctionType.HARDLINK.value == "HARDLINK"


def test_junction_status_enum():
    """Test JunctionStatus enum values"""
    assert JunctionStatus.ACTIVE.value == "ACTIVE"
    assert JunctionStatus.BROKEN.value == "BROKEN"
    assert JunctionStatus.INACCESSIBLE.value == "INACCESSIBLE"


def test_creator_enum():
    """Test Creator enum values"""
    assert Creator.APP.value == "APP"
    assert Creator.EXISTING.value == "EXISTING"
    assert Creator.MANUAL.value == "MANUAL"


def test_undo_strategy_enum():
    """Test UndoStrategy enum values"""
    assert UndoStrategy.REMOVE_ONLY.value == "REMOVE_ONLY"
    assert UndoStrategy.MOVE_BACK.value == "MOVE_BACK"
    assert UndoStrategy.DUPLICATE.value == "DUPLICATE"
    assert UndoStrategy.KEEP_SOURCE.value == "KEEP_SOURCE"


def test_junction_creation():
    """Test creating a Junction model"""
    junction = Junction(
        source=Path("D:/Cache/.vscode"),
        target=Path("C:/Users/steff/.vscode"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
        creator=Creator.APP,
    )

    assert junction.source == Path("D:/Cache/.vscode")
    assert junction.target == Path("C:/Users/steff/.vscode")
    assert junction.junction_type == JunctionType.JUNCTION
    assert junction.status == JunctionStatus.ACTIVE
    assert junction.creator == Creator.APP
    assert junction.is_directory is True


def test_junction_defaults():
    """Test Junction default values"""
    junction = Junction(
        source=Path("D:/Cache/test"),
        target=Path("C:/Users/test"),
        junction_type=JunctionType.SYMLINK,
    )

    assert junction.status == JunctionStatus.ACTIVE
    assert junction.creator == Creator.EXISTING
    assert junction.created_at is None
    assert junction.size_bytes is None
    assert junction.is_directory is True


def test_junction_with_optional_fields():
    """Test Junction with all fields populated"""
    now = datetime.now()
    junction = Junction(
        source=Path("D:/Cache/.vscode"),
        target=Path("C:/Users/steff/.vscode"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
        creator=Creator.APP,
        created_at=now,
        size_bytes=1024000,
        is_directory=True,
    )

    assert junction.created_at == now
    assert junction.size_bytes == 1024000


def test_operation_type_enum():
    """Test OperationType enum values"""
    assert OperationType.CREATE_JUNCTION.value == "CREATE_JUNCTION"
    assert OperationType.CREATE_SYMLINK.value == "CREATE_SYMLINK"
    assert OperationType.CREATE_HARDLINK.value == "CREATE_HARDLINK"
    assert OperationType.REMOVE_JUNCTION.value == "REMOVE_JUNCTION"
    assert OperationType.UNDO_OPERATION.value == "UNDO_OPERATION"
    assert OperationType.MOVE_FILES.value == "MOVE_FILES"
    assert OperationType.COPY_FILES.value == "COPY_FILES"


def test_operation_record_creation():
    """Test creating an OperationRecord"""
    record = OperationRecord(
        operation_type=OperationType.CREATE_JUNCTION,
        source=Path("D:/Cache/.vscode"),
        target=Path("C:/Users/steff/.vscode"),
        success=True,
    )

    assert record.operation_type == OperationType.CREATE_JUNCTION
    assert record.source == Path("D:/Cache/.vscode")
    assert record.target == Path("C:/Users/steff/.vscode")
    assert record.success is True
    assert record.error_message is None
    assert isinstance(record.timestamp, datetime)


def test_operation_record_defaults():
    """Test OperationRecord default values"""
    record = OperationRecord(operation_type=OperationType.REMOVE_JUNCTION)

    assert record.operation_type == OperationType.REMOVE_JUNCTION
    assert record.source is None
    assert record.target is None
    assert record.success is True
    assert record.error_message is None
    assert record.metadata == {}
    assert isinstance(record.timestamp, datetime)


def test_operation_record_with_error():
    """Test OperationRecord with error"""
    record = OperationRecord(
        operation_type=OperationType.CREATE_JUNCTION,
        success=False,
        error_message="Permission denied",
    )

    assert record.success is False
    assert record.error_message == "Permission denied"


def test_scan_result_creation():
    """Test creating a ScanResult"""
    junction1 = Junction(
        source=Path("D:/Cache/.vscode"),
        target=Path("C:/Users/steff/.vscode"),
        junction_type=JunctionType.JUNCTION,
    )

    junction2 = Junction(
        source=Path("D:/Cache/.git"),
        target=Path("C:/Users/steff/.git"),
        junction_type=JunctionType.SYMLINK,
    )

    result = ScanResult(
        junctions=[junction1, junction2],
        scanned_directories=[Path("C:/Users/steff"), Path("D:/Cache")],
        scan_duration_seconds=1.5,
    )

    assert len(result.junctions) == 2
    assert len(result.scanned_directories) == 2
    assert result.scan_duration_seconds == 1.5
    assert len(result.errors) == 0


def test_scan_result_defaults():
    """Test ScanResult default values"""
    result = ScanResult()

    assert result.junctions == []
    assert result.scanned_directories == []
    assert result.scan_duration_seconds == 0.0
    assert result.errors == []


def test_validation_result_success():
    """Test ValidationResult with success"""
    result = ValidationResult(is_valid=True)

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []


def test_validation_result_with_errors():
    """Test ValidationResult with errors"""
    result = ValidationResult(
        is_valid=False,
        errors=["Target path does not exist", "Insufficient disk space"],
        warnings=["This operation will overwrite existing files"],
    )

    assert result.is_valid is False
    assert len(result.errors) == 2
    assert len(result.warnings) == 1
