"""Layout regressions that catch clipped controls rather than pixel snapshots."""

from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QLabel, QScrollArea

from winlink.core.config import AppSettings, save_settings
from winlink.core.models import OperationType
from winlink.ui.components import Columns
from winlink.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=False))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    result = MainWindow()
    qtbot.addWidget(result)
    result.show()
    return result


@pytest.mark.parametrize("size", [(1280, 800), (760, 400)])
def test_four_pages_respect_requested_window_size(window, qtbot, size):
    available = window.screen().availableGeometry()
    # Windows caps top-level windows to the physical monitor at 200% DPI.
    # Keep the small viewport exact and fit the desktop case to available pixels.
    size = (min(size[0], available.width()), min(size[1], available.height() - 60))
    window.resize(*size)
    for page in range(4):
        window.navigate(page)
        qtbot.wait(20)
        assert window.width() == size[0] and window.height() == size[1]
        assert isinstance(window.pages.currentWidget(), QScrollArea)
        area = window.pages.currentWidget()
        assert area.horizontalScrollBar().maximum() == 0
        if page == 2 and size[0] >= 1100:
            assert window.history_page.table_view.horizontalScrollBar().maximum() == 0


def test_creation_cards_have_readable_children_and_two_columns(window, qtbot):
    window.resize(1280, 800)
    window.navigate(1)
    qtbot.wait(30)
    cards = window.create_page.type_cards
    assert cards[0].y() == cards[1].y()
    assert cards[2].y() > cards[0].y()
    for card in cards:
        assert card.height() >= 100
        for label in card.findChildren(QLabel):
            assert label.height() >= 16
            assert label.geometry().bottom() <= card.height()
    assert (
        window.create_page.creation_columns.box.direction()
        == window.create_page.creation_columns.box.Direction.LeftToRight
    )
    window.resize(760, 400)
    qtbot.wait(30)
    assert (
        window.create_page.creation_columns.box.direction()
        == window.create_page.creation_columns.box.Direction.TopToBottom
    )


def test_icons_present_on_navigation_and_primary_actions(window):
    for index in range(4):
        assert not window.navigation.item(index).icon().isNull()
    for button in [
        window.create_page.create_btn,
        window.create_page.source_browse_btn,
        window.history_page.export_btn,
        window.history_page.clear_history_btn,
        window.settings_page.save_btn,
        window.settings_page.defaults_btn,
    ]:
        assert not button.icon().isNull()


def test_list_header_reflows_without_overlapping_controls(window, qtbot):
    window.resize(760, 400)
    window.navigate(0)
    qtbot.wait(30)
    area = window.pages.currentWidget()
    area.verticalScrollBar().setValue(0)
    header = area.widget().findChild(Columns)
    assert header.height() >= 110
    assert window.search_edit.height() >= 36
    assert window.search_edit.mapTo(area.widget(), QPoint(0, 0)).y() >= header.y()


def test_history_row_actions_choose_the_clicked_record(window, qtbot, tmp_path, monkeypatch):
    for i in range(2):
        window.history_manager.add_operation(
            OperationType.CREATE_JUNCTION, tmp_path / f"data{i}", tmp_path / f"link{i}"
        )
    window.resize(1280, 800)
    window.navigate(2)
    qtbot.wait(30)
    page = window.history_page
    callback = Mock()
    monkeypatch.setattr(page, "undo_selected", callback)
    index = page.table_model.index(1, 4)
    page.table_view.scrollTo(index)
    qtbot.wait(20)
    rect = page.table_view.visualRect(index)
    qtbot.mouseClick(
        page.table_view.viewport(),
        Qt.MouseButton.LeftButton,
        pos=QPoint(rect.left() + 160, rect.top() + 30),
    )
    callback.assert_called_once()
    assert page.table_view.currentIndex().row() == 1


def test_settings_footer_is_reachable_in_small_window(window, qtbot):
    window.resize(760, 400)
    window.navigate(3)
    qtbot.wait(30)
    area = window.pages.currentWidget()
    area.ensureWidgetVisible(window.settings_page.save_btn)
    qtbot.wait(20)
    button = window.settings_page.save_btn
    position = button.mapTo(area.viewport(), QPoint(0, 0))
    assert position.y() >= 0
    assert position.y() + button.height() <= area.viewport().height()


def test_type_selection_cannot_be_unchecked_by_repeated_click(window, qtbot):
    window.navigate(1)
    for button in window.create_page.type_cards:
        button.click()
        assert button.isChecked()
        button.click()
        assert button.isChecked()
        assert sum(card.isChecked() for card in window.create_page.type_cards) == 1


def test_empty_state_remains_visible_when_switching_view_mode(window):
    assert window.link_views.currentIndex() == 2
    window.view_mode.setCurrentIndex(1)
    assert window.link_views.currentIndex() == 2
    assert window.empty_title.text() == "Nenhum link configurado"
