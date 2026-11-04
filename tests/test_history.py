"""Tests for history management"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from winlink.core.history import HistoryManager
from winlink.core.models import OperationRecord, OperationType


def test_history_manager_initialization():
    """Test initializing history manager"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        assert manager.history_file == history_file
        assert history_file.exists()
        assert json.loads(history_file.read_text()) == []


def test_add_operation():
    """Test adding an operation to history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        result = manager.add_operation(
            operation_type=OperationType.CREATE_JUNCTION,
            source=Path("D:/source"),
            target=Path("C:/target"),
        )

        assert result is True

        history = manager.get_history()
        assert len(history) == 1
        assert history[0].operation_type == OperationType.CREATE_JUNCTION


def test_add_operation_with_error():
    """Test adding a failed operation to history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        result = manager.add_operation(
            operation_type=OperationType.CREATE_JUNCTION,
            success=False,
            error_message="Permission denied",
        )

        assert result is True

        history = manager.get_history()
        assert len(history) == 1
        assert history[0].success is False
        assert history[0].error_message == "Permission denied"


def test_add_operation_with_metadata():
    """Test adding operation with metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        metadata = {"size": 1024, "junction_type": "JUNCTION"}
        result = manager.add_operation(
            operation_type=OperationType.CREATE_JUNCTION,
            metadata=metadata,
        )

        assert result is True

        history = manager.get_history()
        assert len(history) == 1
        assert history[0].metadata == metadata


def test_get_history():
    """Test getting history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)
        manager.add_operation(OperationType.REMOVE_JUNCTION)

        history = manager.get_history()
        assert len(history) == 2
        # Most recent first
        assert history[0].operation_type == OperationType.REMOVE_JUNCTION
        assert history[1].operation_type == OperationType.CREATE_JUNCTION


def test_get_history_with_limit():
    """Test getting history with limit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        for _ in range(5):
            manager.add_operation(OperationType.CREATE_JUNCTION)

        history = manager.get_history(limit=3)
        assert len(history) == 3


def test_get_history_by_type():
    """Test getting history filtered by type"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)
        manager.add_operation(OperationType.REMOVE_JUNCTION)
        manager.add_operation(OperationType.CREATE_JUNCTION)

        junction_ops = manager.get_history_by_type(OperationType.CREATE_JUNCTION)
        assert len(junction_ops) == 2


def test_get_history_by_date_range():
    """Test getting history filtered by date range"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        now = datetime.now()
        manager.add_operation(OperationType.CREATE_JUNCTION)

        # Use a range that includes the operation
        history = manager.get_history_by_date_range(
            start_date=now - timedelta(minutes=1),
            end_date=now + timedelta(minutes=1),
        )
        assert len(history) == 1


def test_get_last_operation():
    """Test getting last operation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)
        manager.add_operation(OperationType.REMOVE_JUNCTION)

        last = manager.get_last_operation()
        assert last is not None
        assert last.operation_type == OperationType.REMOVE_JUNCTION


def test_get_last_operation_by_type():
    """Test getting last operation filtered by type"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)
        manager.add_operation(OperationType.REMOVE_JUNCTION)
        manager.add_operation(OperationType.CREATE_JUNCTION)

        last = manager.get_last_operation(OperationType.CREATE_JUNCTION)
        assert last is not None
        assert last.operation_type == OperationType.CREATE_JUNCTION


def test_get_last_operation_empty():
    """Test getting last operation when history is empty"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        last = manager.get_last_operation()
        assert last is None


def test_clear_history():
    """Test clearing history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)
        manager.add_operation(OperationType.REMOVE_JUNCTION)

        result = manager.clear_history()
        assert result is True

        history = manager.get_history()
        assert len(history) == 0


def test_get_operation_count():
    """Test getting operation count"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        assert manager.get_operation_count() == 0

        manager.add_operation(OperationType.CREATE_JUNCTION)
        assert manager.get_operation_count() == 1

        manager.add_operation(OperationType.REMOVE_JUNCTION)
        assert manager.get_operation_count() == 2


def test_undo_last_operation():
    """Test getting last operation for undo"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        manager = HistoryManager(history_file)

        manager.add_operation(OperationType.CREATE_JUNCTION)

        undo_op = manager.undo_last_operation()
        assert undo_op is not None
        assert undo_op.operation_type == OperationType.CREATE_JUNCTION


def test_history_max_entries():
    """Test that history respects max entries limit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"

        # Create manager with custom settings by patching
        from unittest.mock import patch

        with patch("winlink.core.history.get_settings") as mock_settings:
            from winlink.core.config import AppSettings

            mock_settings_instance = AppSettings(max_history_entries=5)
            mock_settings.return_value = mock_settings_instance

            manager = HistoryManager(history_file)

            # Add more operations than max
            for i in range(10):
                manager.add_operation(OperationType.CREATE_JUNCTION, metadata={"index": i})

            history = manager.get_history()
            assert len(history) == 5

            # Should have kept the most recent 5
            assert history[0].metadata["index"] == 9
            assert history[4].metadata["index"] == 5


def test_failed_history_replace_preserves_previous_records(tmp_path, monkeypatch):
    from pathlib import Path
    manager = HistoryManager(tmp_path / "history.json")
    assert manager.add_operation(OperationType.CREATE_JUNCTION)
    original = manager.history_file.read_bytes()
    def fail_replace(self, target):
        raise PermissionError("locked")
    monkeypatch.setattr(Path, "replace", fail_replace)
    assert not manager.add_operation(OperationType.REMOVE_JUNCTION)
    assert manager.history_file.read_bytes() == original


def test_add_operation_does_not_overwrite_corrupt_history(tmp_path):
    path = tmp_path / "history.json"
    original = '{"partial":'
    path.write_text(original)
    manager = HistoryManager(path)
    assert manager.get_history() == []
    assert not manager.add_operation(OperationType.CREATE_JUNCTION)
    assert path.read_text() == original
