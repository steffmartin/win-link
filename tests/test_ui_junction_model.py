"""Tests for junction table model"""

from datetime import datetime
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt, QModelIndex

from winlink.core.models import Junction, JunctionType, JunctionStatus, Creator
from winlink.ui.junction_model import JunctionTableModel


@pytest.fixture
def junction_model():
    """Fixture for JunctionTableModel"""
    return JunctionTableModel()


@pytest.fixture
def sample_junctions():
    """Fixture for sample junctions"""
    return [
        Junction(
            source=Path("D:\\Cache\\.vscode"),
            target=Path("C:\\Users\\steff\\.vscode"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
            creator=Creator.APP,
            created_at=datetime.now(),
            size_bytes=1024 * 1024 * 100,  # 100 MB
        ),
        Junction(
            source=Path("D:\\Cache\\.cargo"),
            target=Path("C:\\Users\\steff\\.cargo"),
            junction_type=JunctionType.SYMLINK,
            status=JunctionStatus.BROKEN,
            creator=Creator.EXISTING,
            created_at=datetime.now(),
            size_bytes=1024 * 1024 * 50,  # 50 MB
        ),
        Junction(
            source=Path("D:\\Cache\\test"),
            target=Path("C:\\Users\\steff\\test"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.INACCESSIBLE,
            creator=Creator.MANUAL,
            created_at=datetime.now(),
            size_bytes=None,
        ),
    ]


def test_model_initialization(junction_model):
    """Test model initialization"""
    assert junction_model.rowCount() == 0
    assert junction_model.columnCount() == 7


def test_model_set_junctions(junction_model, sample_junctions):
    """Test setting junctions"""
    junction_model.set_junctions(sample_junctions)
    assert junction_model.rowCount() == len(sample_junctions)


def test_model_data_display(junction_model, sample_junctions):
    """Test data display"""
    junction_model.set_junctions(sample_junctions)

    # Test first junction
    index = junction_model.index(0, 0)  # Source column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert "D:\\Cache\\.vscode" in data

    index = junction_model.index(0, 1)  # Target column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert "C:\\Users\\steff\\.vscode" in data

    index = junction_model.index(0, 2)  # Creator column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert data == "App"

    index = junction_model.index(0, 3)  # Type column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert data == "Junção"

    index = junction_model.index(0, 4)  # Size column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert "MB" in data

    index = junction_model.index(0, 6)  # Status column
    data = junction_model.data(index, Qt.ItemDataRole.DisplayRole)
    assert "Ativo" in data


def test_tags_are_displayed_in_the_compact_tags_column(junction_model, sample_junctions):
    sample_junctions[0].tags = ["minha-pasta", "fotos"]
    junction_model.set_junctions(sample_junctions)
    assert junction_model.headerData(5, Qt.Orientation.Horizontal) == "Tags"
    assert junction_model.data(junction_model.index(0, 5)) == "minha-pasta, fotos"


def test_model_header_data(junction_model):
    """Test header data"""
    for col in range(junction_model.columnCount()):
        header = junction_model.headerData(col, Qt.Orientation.Horizontal)
        assert header is not None
        assert isinstance(header, str)


def test_model_get_junction(junction_model, sample_junctions):
    """Test getting junction at index"""
    junction_model.set_junctions(sample_junctions)

    index = junction_model.index(0, 0)
    junction = junction_model.get_junction(index)
    assert junction is not None
    assert junction.source == sample_junctions[0].source


def test_model_clear(junction_model, sample_junctions):
    """Test clearing junctions"""
    junction_model.set_junctions(sample_junctions)
    assert junction_model.rowCount() > 0

    junction_model.clear()
    assert junction_model.rowCount() == 0


def test_model_add_junction(junction_model):
    """Test adding a junction"""
    junction = Junction(
        source=Path("D:\\Cache\\new"),
        target=Path("C:\\Users\\steff\\new"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
        creator=Creator.APP,
    )

    initial_count = junction_model.rowCount()
    junction_model.add_junction(junction)
    assert junction_model.rowCount() == initial_count + 1


def test_model_remove_junction(junction_model, sample_junctions):
    """Test removing a junction"""
    junction_model.set_junctions(sample_junctions)
    initial_count = junction_model.rowCount()

    index = junction_model.index(0, 0)
    junction_model.remove_junction(index)
    assert junction_model.rowCount() == initial_count - 1


def test_model_update_junction(junction_model, sample_junctions):
    """Test updating a junction"""
    junction_model.set_junctions(sample_junctions)

    index = junction_model.index(0, 0)
    updated_junction = sample_junctions[0].model_copy(
        update={"status": JunctionStatus.BROKEN, "size_bytes": 0}
    )

    junction_model.update_junction(index, updated_junction)

    junction = junction_model.get_junction(index)
    assert junction.status == JunctionStatus.BROKEN
    assert junction.size_bytes == 0


def test_model_size_formatting(junction_model):
    """Test size formatting"""
    # Test bytes
    assert "B" in junction_model._format_size(100)

    # Test KB
    assert "KB" in junction_model._format_size(1024)

    # Test MB
    assert "MB" in junction_model._format_size(1024 * 1024)

    # Test GB
    assert "GB" in junction_model._format_size(1024 * 1024 * 1024)

    # Test None
    assert junction_model._format_size(None) == "N/A"


def test_model_invalid_index(junction_model):
    """Test handling invalid indices"""
    # Invalid row
    index = junction_model.index(999, 0)
    data = junction_model.data(index)
    assert data is None

    junction = junction_model.get_junction(index)
    assert junction is None


def test_table_model_has_no_children(junction_model, sample_junctions):
    junction_model.set_junctions(sample_junctions)
    parent = junction_model.index(0, 0)
    assert junction_model.rowCount(parent) == 0
    assert junction_model.columnCount(parent) == 0


def test_update_notifies_entire_row(junction_model, sample_junctions):
    junction_model.set_junctions(sample_junctions)
    changes = []
    junction_model.dataChanged.connect(lambda left, right, roles: changes.append((left.column(), right.column())))
    junction_model.update_junction(junction_model.index(0, 2), sample_junctions[1])
    assert changes == [(0, 6)]


def test_upsert_and_remove_by_target(junction_model, sample_junctions):
    junction_model.set_junctions(list(sample_junctions))
    created = Junction(
        source=Path("D:\\new"),
        target=Path("C:\\new-link"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
    )
    junction_model.upsert_junction(created)
    assert junction_model.rowCount() == 4

    updated = created.model_copy(update={"status": JunctionStatus.BROKEN})
    junction_model.upsert_junction(updated)
    assert junction_model.rowCount() == 4
    assert junction_model._junctions[-1].status == JunctionStatus.BROKEN

    junction_model.remove_junction_target(created.target)
    assert junction_model.rowCount() == 3
    junction_model.remove_junction_target(Path("C:\\does-not-exist"))
    assert junction_model.rowCount() == 3
