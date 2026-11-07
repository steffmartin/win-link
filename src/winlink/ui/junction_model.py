"""Table model for displaying junctions in QTableView"""

from pathlib import Path

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor

from winlink.core.models import Creator, Junction, JunctionStatus, JunctionType


class JunctionTableModel(QAbstractTableModel):
    """Model for displaying junctions in a table view"""

    _junctions: list[Junction]

    COLUMNS = [
        "Dados Físicos",
        "Ponto de Acesso",
        "Criador",
        "Tipo",
        "Tamanho",
        "Tags",
        "Status",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._junctions: list[Junction] = []

    def upsert_junction(self, junction: Junction) -> None:
        """Insert or replace the entry for a junction target."""
        for row, existing in enumerate(self._junctions):
            if existing.target == junction.target:
                self._junctions[row] = junction
                self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                return
        row = len(self._junctions)
        self.beginInsertRows(QModelIndex(), row, row)
        self._junctions.append(junction)
        self.endInsertRows()

    def remove_junction_target(self, target: Path) -> None:
        """Remove the entry for a junction target if present."""
        for row, existing in enumerate(self._junctions):
            if existing.target == target:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._junctions[row]
                self.endRemoveRows()
                return

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows"""
        if parent.isValid():
            return 0
        return len(self._junctions)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns"""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return data for a cell"""
        if not index.isValid():
            return None

        if index.row() >= len(self._junctions):
            return None

        junction = self._junctions[int(index.row())]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(junction, column)
        elif role == Qt.ItemDataRole.DecorationRole and column == 6:
            from winlink.ui.icons import status_icon
            from winlink.ui.theme import junction_status_color

            return status_icon(junction.status, junction_status_color(junction.status).name())
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip_data(junction, column)
        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_foreground_color(junction, column)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return self._get_alignment(column)

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):
        """Return header data"""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def _get_display_data(self, junction: Junction, column: int) -> str:
        """Get display data for a column"""
        if column == 0:  # Origem
            return str(junction.source)
        elif column == 1:  # Destino
            return str(junction.target)
        elif column == 2:  # Criador
            return self._get_creator_display(junction.creator)
        elif column == 3:  # Tipo
            from winlink.ui.type_labels import link_type_label

            return link_type_label(junction.junction_type, junction.is_directory)
        elif column == 4:  # Tamanho
            return self._format_size(junction.size_bytes)
        elif column == 5:  # Tags
            return ", ".join(junction.tags)
        elif column == 6:  # Status
            return self._get_status_display(junction.status)
        return ""

    def _get_tooltip_data(self, junction: Junction, column: int) -> str:
        """Get tooltip data for a column"""
        if column == 0:  # Origem
            return str(junction.source.absolute())
        elif column == 1:  # Destino
            return str(junction.target.absolute())
        elif column == 2:  # Criador
            return f"Criador: {junction.creator.value}"
        elif column == 3:  # Tipo
            return f"Tipo: {junction.junction_type.value}"
        elif column == 4:  # Tamanho
            if junction.size_bytes:
                return f"{junction.size_bytes:,} bytes"
            return "Tamanho desconhecido"
        elif column == 5:  # Tags
            return ", ".join(junction.tags)
        elif column == 6:  # Status
            return f"Status: {junction.status.value}"
        return ""

    def _get_foreground_color(self, junction: Junction, column: int) -> QColor | None:
        """Get foreground color for a cell"""
        if column == 6:  # Status column
            from winlink.ui.theme import junction_status_color

            return junction_status_color(junction.status)
        return None

    def _get_alignment(self, column: int) -> Qt.AlignmentFlag:
        """Get text alignment for a column"""
        if column == 4:  # Tamanho
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

    def _get_creator_display(self, creator: Creator) -> str:
        """Get display text for creator"""
        if creator == Creator.APP:
            return "App"
        elif creator == Creator.EXISTING:
            return "Existente"
        elif creator == Creator.MANUAL:
            return "Manual"
        return creator.value

    def _get_type_display(self, junction_type: JunctionType, is_directory: bool = True) -> str:
        """Get display text for junction type"""
        from winlink.ui.type_labels import link_type_label

        return link_type_label(junction_type, is_directory)

    def _get_status_display(self, status: JunctionStatus) -> str:
        """Get display text for status"""
        if status == JunctionStatus.ACTIVE:
            return "Ativo"
        elif status == JunctionStatus.BROKEN:
            return "Quebrado"
        elif status == JunctionStatus.INACCESSIBLE:
            return "Inacessível"
        return status.value

    def _format_size(self, size_bytes: float | None) -> str:
        """Format size in human-readable format"""
        if size_bytes is None:
            return "N/A"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def set_junctions(self, junctions: list[Junction]) -> None:
        """
        Set the list of junctions.

        Args:
            junctions: List of Junction objects
        """
        self.beginResetModel()
        self._junctions = junctions
        self.endResetModel()

    def remove_excluded(self, exclusions: tuple[Path, ...]) -> None:
        from winlink.core.scanner import is_discovery_excluded

        visible = [j for j in self._junctions if not is_discovery_excluded(j.target, exclusions)]
        if len(visible) != len(self._junctions):
            self.set_junctions(visible)

    def get_junction(self, index: QModelIndex) -> Junction | None:
        """
        Get junction at a given index.

        Args:
            index: Model index

        Returns:
            Junction object or None
        """
        if not index.isValid() or index.row() >= len(self._junctions):
            return None
        return self._junctions[int(index.row())]

    def clear(self) -> None:
        """Clear all junctions"""
        self.beginResetModel()
        self._junctions = []
        self.endResetModel()

    def add_junction(self, junction: Junction) -> None:
        """
        Add a junction to the model.

        Args:
            junction: Junction to add
        """
        self.beginInsertRows(QModelIndex(), len(self._junctions), len(self._junctions))
        self._junctions.append(junction)
        self.endInsertRows()

    def remove_junction(self, index: QModelIndex) -> None:
        """
        Remove a junction from the model.

        Args:
            index: Model index of junction to remove
        """
        if not index.isValid() or index.row() >= len(self._junctions):
            return

        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._junctions.pop(index.row())
        self.endRemoveRows()

    def update_junction(self, index: QModelIndex, junction: Junction) -> None:
        """
        Update a junction in the model.

        Args:
            index: Model index of junction to update
            junction: New junction data
        """
        if not index.isValid() or index.row() >= len(self._junctions):
            return

        self._junctions[int(index.row())] = junction
        self.dataChanged.emit(
            self.index(index.row(), 0), self.index(index.row(), len(self.COLUMNS) - 1)
        )
