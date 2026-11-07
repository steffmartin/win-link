"""Behavioral checks for changes to existing presentation flows."""

from unittest.mock import Mock

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QMessageBox, QToolButton, QToolTip

from winlink.core.config import AppSettings, get_settings, save_settings
from winlink.core.models import JunctionType
from winlink.ui.dialogs.progress_dialog import ProgressDialog
from winlink.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=False))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    result = MainWindow()
    qtbot.addWidget(result)
    result.show()
    yield result
    for progress in result.findChildren(ProgressDialog):
        progress.set_operation_finished(True)
        progress.close()


def test_theme_button_cycles_existing_modes_and_persists(window, qtbot):
    assert window.theme_button.menu() is None
    window.quick_theme.setCurrentIndex(window.quick_theme.findData("dark"))
    for mode, next_label in [("light", "Seguir sistema"), ("auto", "Escuro"), ("dark", "Claro")]:
        window.theme_button.setFocus()
        qtbot.keyClick(window.theme_button, Qt.Key.Key_Space)
        assert get_settings().theme_mode == mode
        assert window.settings.theme_mode == mode
        assert next_label in window.theme_button.toolTip()
        assert not window.theme_button.icon().isNull()


@pytest.mark.parametrize("apply", [False, True])
def test_sorting_is_a_filter_draft_and_uses_current_table_sort(window, apply):
    window.filter_model.sort(1, Qt.SortOrder.DescendingOrder)
    observations = []

    def edit():
        dialog = QApplication.activeModalWidget()
        combos = dialog.findChildren(QComboBox)
        observations.append((combos[5].currentIndex(), combos[6].currentIndex()))
        combos[0].setCurrentIndex(2)
        combos[5].setCurrentIndex(5)
        combos[6].setCurrentIndex(0)
        dialog.accept() if apply else dialog.reject()

    QTimer.singleShot(20, edit)
    window.edit_filters()
    assert observations == [(1, 1)]
    assert window.status_filter.currentIndex() == (2 if apply else 0)
    assert window.filter_model.sortColumn() == (5 if apply else 1)
    assert window.filter_model.sortOrder() == (
        Qt.SortOrder.AscendingOrder if apply else Qt.SortOrder.DescendingOrder
    )


def test_clear_action_preserves_sort_and_refreshes(window, monkeypatch):
    window.search_edit.setText("example")
    window.status_filter.setCurrentIndex(2)
    window.filter_model.sort(1, Qt.SortOrder.DescendingOrder)
    refresh = Mock()
    monkeypatch.setattr(window, "start_scan", refresh)
    window.reset_filters_btn.click()
    assert not window.search_edit.text()
    assert window.status_filter.currentIndex() == 0
    assert window.filter_model.sortColumn() == 1
    assert window.filter_model.sortOrder() == Qt.SortOrder.DescendingOrder
    refresh.assert_called_once()


def test_settings_help_is_available_by_keyboard_without_toggling_option(window, qtbot, monkeypatch):
    page = window.settings_page
    window.navigate(3)
    buttons = [b for b in page.findChildren(QToolButton) if b.accessibleName().startswith("Ajuda:")]
    assert len(buttons) == 6
    display = Mock()
    monkeypatch.setattr(QToolTip, "showText", display)
    before = (
        page.confirm_checkbox.isChecked(),
        page.backup_checkbox.isChecked(),
        page.notify_checkbox.isChecked(),
        page.warn_nested_checkbox.isChecked(),
    )
    for button in buttons:
        window.pages.currentWidget().ensureWidgetVisible(button)
        button.setFocus()
        qtbot.keyClick(button, Qt.Key.Key_Space)
        assert display.call_args.args[1] == button.toolTip()
        assert button.accessibleDescription() == button.toolTip()
    assert before == (
        page.confirm_checkbox.isChecked(),
        page.backup_checkbox.isChecked(),
        page.notify_checkbox.isChecked(),
        page.warn_nested_checkbox.isChecked(),
    )
    assert not page.confirm_checkbox.isEnabled()


def test_settings_expand_with_the_available_window(window, qtbot):
    window.navigate(3)
    window.resize(760, 400)
    qtbot.wait(30)
    included = window.settings_page.scan_list
    excluded = window.settings_page.excluded_list
    assert (
        included.mapTo(window.settings_page, included.rect().topLeft()).y()
        < excluded.mapTo(window.settings_page, excluded.rect().topLeft()).y()
    )
    assert window.pages.currentWidget().horizontalScrollBar().maximum() == 0
    window.resize(1280, 800)
    qtbot.wait(30)
    left = included.mapTo(window.settings_page, included.rect().topLeft())
    right = excluded.mapTo(window.settings_page, excluded.rect().topLeft())
    assert left.y() == right.y()
    assert left.x() + included.width() < right.x()


def test_about_retains_keyboard_accessible_project_link(window):
    observed = []

    def inspect():
        dialog = QApplication.activeModalWidget()
        links = [
            label
            for label in dialog.findChildren(QLabel)
            if "https://github.com/steffmartin/win-link" in label.text()
        ]
        observed.extend(links)
        assert links[0].openExternalLinks()
        assert links[0].textInteractionFlags() & Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        dialog.reject()

    QTimer.singleShot(20, inspect)
    window.about_button.click()
    assert len(observed) == 1
    assert not window.about_button.text()
    assert window.about_button.accessibleName() == "Sobre WinLink"


@pytest.mark.parametrize("kind", [JunctionType.JUNCTION, JunctionType.HARDLINK])
def test_success_clears_form_and_keeps_only_progress_feedback(window, monkeypatch, tmp_path, kind):
    source, target = tmp_path / "data", tmp_path / "access"
    if kind == JunctionType.JUNCTION:
        source.mkdir()
        (source / "keep.txt").write_text("preserve")
    else:
        source.write_text("preserve")
    window.settings.default_link_type = "symlink_file"
    page = window.create_page
    page.select_type(0 if kind == JunctionType.JUNCTION else 2, kind == JunctionType.HARDLINK)
    page.source_edit.setText(str(source))
    page.target_edit.setText(str(target))
    info = Mock()
    monkeypatch.setattr(QMessageBox, "information", info)
    window.create_link(target, source, kind)
    try:
        assert target.exists()
        assert source.samefile(target)
        assert source.exists()
        assert not page.source_edit.text() and not page.target_edit.text()
        assert page.file_symlink.isChecked()
        info.assert_not_called()
        progress = window.findChildren(ProgressDialog)[-1]
        assert progress.isVisible()
        assert progress.cancel_btn.text() == "Fechar"
        assert window.history_manager.get_history()[0].success
    finally:
        target.rmdir() if target.is_junction() else target.unlink()


def test_failed_creation_preserves_form(window, monkeypatch, tmp_path):
    from winlink.core import operations

    source, target = tmp_path / "data", tmp_path / "access"
    source.mkdir()
    page = window.create_page
    page.source_edit.setText(str(source))
    page.target_edit.setText(str(target))
    monkeypatch.setattr(operations, "create_junction", lambda *a: False)
    monkeypatch.setattr(QMessageBox, "critical", Mock())
    window.create_link(target, source, JunctionType.JUNCTION)
    assert page.source_edit.text() == str(source)
    assert page.target_edit.text() == str(target)
    assert not target.exists()
    assert not window.history_manager.get_history()[0].success
