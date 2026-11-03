"""History management for operations"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from winlink.core.config import get_settings
from winlink.core.models import OperationRecord, OperationType
from winlink.utils.logger import get_logger

logger = get_logger(__name__)


class HistoryManager:
    """Manager for operation history"""

    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize history manager.

        Args:
            history_file: Path to history file (uses default if None)
        """
        if history_file is None:
            settings = get_settings()
            history_file = settings.history_file

        self.history_file = Path(history_file)
        self._ensure_history_file_exists()

    def _ensure_history_file_exists(self):
        """Ensure history file and parent directory exist"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self.history_file.write_text("[]", encoding="utf-8")
        except Exception as e:
            logger.error(f"Error creating history file {self.history_file}: {e}")

    def _load_history(self) -> list[dict]:
        """
        Load history from file.

        Returns:
            List of operation dictionaries
        """
        try:
            if not self.history_file.exists():
                return []

            content = self.history_file.read_text(encoding="utf-8")
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding history file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []

    def _save_history(self, history: list[dict]) -> bool:
        """
        Save history to file.

        Args:
            history: List of operation dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Error saving history: {e}")
            return False

    def add_operation(
        self,
        operation_type: OperationType,
        source: Optional[Path] = None,
        target: Optional[Path] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Add an operation to history.

        Args:
            operation_type: Type of operation
            source: Source path
            target: Target path
            success: Whether operation succeeded
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            settings = get_settings()
            history = self._load_history()

            # Create operation record
            record = OperationRecord(
                operation_type=operation_type,
                source=source,
                target=target,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            # Add to history
            history.append(record.model_dump())

            # Trim if exceeds max entries
            if len(history) > settings.max_history_entries:
                history = history[-settings.max_history_entries :]

            return self._save_history(history)

        except Exception as e:
            logger.error(f"Error adding operation to history: {e}")
            return False

    def get_history(self, limit: Optional[int] = None) -> list[OperationRecord]:
        """
        Get operation history.

        Args:
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of operation records
        """
        try:
            history_dicts = self._load_history()

            # Convert to OperationRecord objects
            records = [OperationRecord(**record) for record in history_dicts]

            # Reverse to get most recent first
            records.reverse()

            # Apply limit
            if limit is not None:
                records = records[:limit]

            return records

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    def get_history_by_type(self, operation_type: OperationType) -> list[OperationRecord]:
        """
        Get operations of a specific type.

        Args:
            operation_type: Type of operation to filter

        Returns:
            List of operation records
        """
        history = self.get_history()
        return [record for record in history if record.operation_type == operation_type]

    def get_history_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[OperationRecord]:
        """
        Get operations within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of operation records
        """
        history = self.get_history()
        return [
            record
            for record in history
            if start_date <= record.timestamp <= end_date
        ]

    def get_last_operation(
        self, operation_type: Optional[OperationType] = None
    ) -> Optional[OperationRecord]:
        """
        Get the last operation.

        Args:
            operation_type: Filter by operation type (optional)

        Returns:
            Last operation record or None
        """
        history = self.get_history()

        if operation_type is not None:
            history = [record for record in history if record.operation_type == operation_type]

        return history[0] if history else None

    def clear_history(self) -> bool:
        """
        Clear all history.

        Returns:
            True if successful, False otherwise
        """
        try:
            return self._save_history([])
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False

    def get_operation_count(self) -> int:
        """
        Get total number of operations in history.

        Returns:
            Number of operations
        """
        history = self._load_history()
        return len(history)

    def undo_last_operation(self) -> Optional[OperationRecord]:
        """
        Get the last operation for undo.

        Returns:
            Last operation record or None
        """
        return self.get_last_operation()
