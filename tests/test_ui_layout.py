"""Layout regressions that catch clipped controls rather than pixel snapshots."""

from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QLabel, QScrollArea

from winlink.core.config import AppSettings, save_settings
from winlink.core.models import OperationType
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
    positions = [card.mapTo(window.create_page, QPoint()) for card in cards]
    assert positions[0].y() == positions[1].y()
    assert positions[2].y() > positions[0].y()
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


def test_list_search_controls_fit_both_window_sizes(window, qtbot):
    window.navigate(0)
    row = window.search_controls
    for width, height in [(1280, 800), (760, 400)]:
        window.resize(width, height)
        qtbot.wait(30)
        for control in row.buttons:
            assert row.rect().contains(control.geometry())
        for left, right in zip(row.buttons, row.buttons[1:]):
            assert not left.geometry().intersects(right.geometry())
        if row.width() >= sum(control.sizeHint().width() for control in row.buttons) + 36:
            assert len({control.geometry().center().y() for control in row.buttons}) <= 2


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


def test_settings_persist_default_link_view(window):
    from winlink.core.config import get_settings

    page = window.settings_page
    assert window.view_mode.currentData() == "normal"
    page.link_view_combo.setCurrentIndex(1)
    assert get_settings().link_view_mode == "normal"
    page.discard_changes()
    assert page.link_view_combo.currentData() == "normal"

    page.link_view_combo.setCurrentIndex(1)
    page.save_settings()
    assert get_settings().link_view_mode == "compact"
    assert window.view_mode.currentData() == "compact"
    assert window.link_views.currentIndex() == 2
    reopened = MainWindow()
    try:
        assert reopened.view_mode.currentData() == "compact"
    finally:
        reopened.close()


def test_type_help_is_inside_card_and_activates_without_selecting(window, qtbot):
    from PyQt6.QtWidgets import QToolButton

    window.navigate(1)
    cards = window.create_page.type_cards
    selected = [card.isChecked() for card in cards]
    for card in cards:
        help_button = card.findChild(QToolButton)
        assert help_button is not None
        assert card.rect().contains(help_button.geometry())
        card.setFocus()
        qtbot.keyClick(card, Qt.Key.Key_Tab)
        assert help_button.hasFocus()
        with qtbot.waitSignal(help_button.clicked):
            qtbot.keyClick(help_button, Qt.Key.Key_Space)
        assert [item.isChecked() for item in cards] == selected


def test_compact_paths_share_width_and_can_be_resized(window, qtbot, tmp_path):
    from winlink.core.models import Junction, JunctionType

    window.junction_model.set_junctions(
        [Junction(source=tmp_path, target=tmp_path / "link", junction_type=JunctionType.JUNCTION)]
    )
    window.view_mode.setCurrentIndex(1)
    window.resize(760, 500)
    qtbot.wait(30)
    table = window.table_view
    before = [table.columnWidth(column) for column in range(6)]
    window.resize(1280, 800)
    qtbot.wait(30)
    after = [table.columnWidth(column) for column in range(6)]
    assert after[0] > before[0]
    assert abs((after[0] - before[0]) - (after[1] - before[1])) <= 1
    assert after[2:] == before[2:]
    table.horizontalHeader().resizeSection(0, after[0] + 20)
    assert table.columnWidth(0) == after[0] + 20

def test_exclusion_draft_can_be_restored_discarded_and_saved(window):
    from winlink.core import config

    page = window.settings_page
    saved = list(window.settings.scan_excluded_directories)
    page.restore_defaults()
    assert page.excluded_list.count() >= 1
    page.discard_changes()
    assert [page.excluded_list.item(i).text() for i in range(page.excluded_list.count())] == saved

    while page.excluded_list.count():
        page.excluded_list.setCurrentRow(0)
        page.remove_excluded_directory()
    page.save_settings()
    assert config.get_settings().scan_excluded_directories == []
    page.restore_defaults()
    assert page.excluded_list.count() >= 1
    assert config.get_settings().scan_excluded_directories == []


def test_maximized_geometry_is_restored_on_next_launch(qtbot, monkeypatch, tmp_path):
    from winlink.core.config import get_settings

    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=True))
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.showMaximized()
    qtbot.wait(20)
    window.close()
    qtbot.wait(20)
    assert get_settings().window_geometry
    restored = MainWindow()
    qtbot.addWidget(restored)
    restored.show()
    qtbot.wait(20)
    assert restored.isMaximized()
    restored.close()


def test_saved_offscreen_geometry_is_moved_back_on_screen(qtbot, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=True))
    window = MainWindow()
    qtbot.addWidget(window)
    window.setGeometry(-3000, -3000, 800, 600)
    window.show()
    window.close()
    qtbot.wait(20)
    restored = MainWindow()
    qtbot.addWidget(restored)
    restored.show()
    qtbot.wait(20)
    assert restored.screen().availableGeometry().contains(restored.geometry())
    restored.close()


def test_list_filters_are_remembered_between_sessions(qtbot, monkeypatch, tmp_path):
    from PyQt6.QtCore import Qt

    from winlink.core.config import get_settings

    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    save_settings(
        AppSettings(
            scan_directories=[str(tmp_path)],
            remember_window_size=False,
            list_filter_status=3,
            list_filter_creator=2,
            list_filter_type=1,
            list_sort_column=4,
            list_sort_ascending=False,
        )
    )
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.status_filter.currentIndex() == 3
    assert window.creator_filter.currentIndex() == 2
    assert window.type_filter.currentIndex() == 1
    assert window.filter_model.sortColumn() == 4
    assert window.filter_model.sortOrder() == Qt.SortOrder.DescendingOrder
    window.status_filter.setCurrentIndex(1)
    assert get_settings().list_filter_status == 1
    window.close()
