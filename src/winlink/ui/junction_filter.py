"""Proxy model for filtering and sorting junctions"""

from typing import cast

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel

from winlink.core.models import Creator, JunctionStatus, JunctionType
from winlink.ui.junction_model import JunctionTableModel


class JunctionFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting junctions"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_status: JunctionStatus | None = None
        self._filter_creator: Creator | None = None
        self._filter_type: JunctionType | None = None
        self._search_text: str = ""
        self._filter_directory: bool | None = None

    def set_filter_status(self, status: JunctionStatus | None) -> None:
        """
        Set status filter.

        Args:
            status: JunctionStatus to filter by, or None for no filter
        """
        self._filter_status = status
        self.invalidateFilter()

    def set_filter_creator(self, creator: Creator | None) -> None:
        """
        Set creator filter.

        Args:
            creator: Creator to filter by, or None for no filter
        """
        self._filter_creator = creator
        self.invalidateFilter()

    def set_filter_type(self, junction_type: JunctionType | None) -> None:
        """
        Set junction type filter.

        Args:
            junction_type: JunctionType to filter by, or None for no filter
        """
        self._filter_type = junction_type
        self.invalidateFilter()

    def set_filter_directory(self, is_directory: bool | None):
        self._filter_directory = is_directory
        self.invalidateFilter()

    def set_search_text(self, text: str) -> None:
        """
        Set search text for filtering.

        Args:
            text: Search text to filter by
        """
        self._search_text = text.lower()
        self.invalidateFilter()

    def clear_filters(self) -> None:
        """Clear all filters"""
        self._filter_status = None
        self._filter_creator = None
        self._filter_type = None
        self._filter_directory = None
        self._search_text = ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determine if a row should be included in the filtered model.

        Args:
            source_row: Row index in source model
            source_parent: Parent index in source model

        Returns:
            True if row should be included, False otherwise
        """
        source_model = cast(JunctionTableModel, self.sourceModel())
        if not source_model:
            return False

        index = source_model.index(source_row, 0)
        junction = source_model.get_junction(index)

        if not junction:
            return False

        # Filter by status
        if self._filter_status and junction.status != self._filter_status:
            return False

        # Filter by creator
        if self._filter_creator and junction.creator != self._filter_creator:
            return False

        # Filter by type
        if self._filter_type and junction.junction_type != self._filter_type:
            return False

        if self._filter_directory is not None and junction.is_directory != self._filter_directory:
            return False

        # Filter by search text
        if self._search_text:
            source_str = str(junction.source).lower()
            target_str = str(junction.target).lower()
            if self._search_text not in source_str and self._search_text not in target_str:
                return False

        return True

    def lessThan(self, source_left: QModelIndex, source_right: QModelIndex) -> bool:
        """
        Compare two items for sorting.

        Args:
            source_left: Left index
            source_right: Right index

        Returns:
            True if left < right
        """
        source_model = cast(JunctionTableModel, self.sourceModel())
        if not source_model:
            return False

        left_junction = source_model.get_junction(source_left)
        right_junction = source_model.get_junction(source_right)

        if not left_junction or not right_junction:
            return False

        column = source_left.column()

        # Custom sorting by column
        if column == 0:  # Origem - sort by path
            return str(left_junction.source) < str(right_junction.source)
        elif column == 1:  # Destino - sort by path
            return str(left_junction.target) < str(right_junction.target)
        elif column == 2:  # Criador - sort by creator
            return left_junction.creator.value < right_junction.creator.value
        elif column == 3:  # Tipo - sort by type
            return left_junction.junction_type.value < right_junction.junction_type.value
        elif column == 4:  # Tamanho - sort by size
            left_size = left_junction.size_bytes or 0
            right_size = right_junction.size_bytes or 0
            return left_size < right_size
        elif column == 5:  # Status - sort by status
            return left_junction.status.value < right_junction.status.value

        # Default to string comparison
        left_data = source_model.data(source_left)
        right_data = source_model.data(source_right)
        return str(left_data) < str(right_data)
