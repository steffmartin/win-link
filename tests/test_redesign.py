"""Redesign integration regressions; all application/filesystem data is isolated."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialogButtonBox, QMessageBox, QScrollArea

from winlink.core.config import AppSettings, get_settings, save_settings, settings_path
from winlink.core.history import HistoryManager, creation_was_undone
from winlink.core.models import (
    Creator,
    Junction,
    JunctionStatus,
    JunctionType,
    OperationRecord,
    OperationType,
)
from winlink.ui.main_window import MainWindow
from winlink.ui.dialogs.settings_dialog import SettingsDialog
from winlink.ui.dialogs.history_dialog import HistoryDialog


def _clear_list_filter_dialog(window):
    from PyQt6.QtWidgets import QApplication

    def clear():
        dialog = QApplication.activeModalWidget()
        dialog.clear_button.click()
        dialog.accept()

    QTimer.singleShot(20, clear)
    window.edit_filters()


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    save_settings(AppSettings(scan_directories=[str(tmp_path)], remember_window_size=False))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    result = MainWindow()
    qtbot.addWidget(result)
    result.show()
    return result


def test_legacy_config_roundtrip_preserves_storage(tmp_path):
    settings_path().parent.mkdir(parents=True, exist_ok=True)
    settings_path().write_text(
        '{"theme_mode":"dark","history_file":"D:/custom/history.json","show_notifications":false}'
    )
    settings = get_settings()
    assert settings.default_link_type == "junction"
    save_settings(settings)
    loaded = get_settings()
    assert loaded.history_file == Path("D:/custom/history.json")
    assert loaded.theme_mode == "dark" and not loaded.show_notifications


@pytest.mark.parametrize(
    "preference,index,file",
    [
        ("junction", 0, False),
        ("symlink_dir", 1, False),
        ("symlink_file", 1, True),
        ("hardlink", 2, False),
    ],
)
def test_default_type_reaches_creation_page(window, preference, index, file):
    window.settings.default_link_type = preference
    window.on_new_junction()
    assert window.pages.currentIndex() == 1
    assert window.create_page.type_combo.currentIndex() == index
    assert window.create_page.file_symlink.isChecked() == file
    assert window.create_page.is_directory_link() is (
        preference not in ("symlink_file", "hardlink")
    )


def test_default_type_saved_in_settings_is_selected_from_navigation(window):
    settings_page = window.settings_page
    settings_page.default_type_combo.setCurrentIndex(
        settings_page.default_type_combo.findData("symlink_dir")
    )
    settings_page.save_settings()

    window.navigate(1)

    assert window.create_page.is_directory_link()
    assert window.create_page.get_link_type() == JunctionType.SYMLINK
    assert window.create_page.type_cards[1].isChecked()


def test_default_type_labels_are_localized_without_changing_values(window):
    combo = window.settings_page.default_type_combo
    assert [combo.itemText(index) for index in range(combo.count())] == [
        "Pasta - Junção",
        "Pasta - Symlink",
        "Arquivo - Hardlink",
        "Arquivo - Symlink",
    ]
    assert [combo.itemData(index) for index in range(combo.count())] == [
        "junction",
        "symlink_dir",
        "hardlink",
        "symlink_file",
    ]
    assert window.create_page.type_cards[0].text() == "Junção"


@pytest.mark.parametrize(
    ("operation_type", "is_directory", "expected"),
    [
        (OperationType.CREATE_JUNCTION, True, "Criar Junção"),
        (OperationType.CREATE_SYMLINK, True, "Criar Symlink (pasta)"),
        (OperationType.CREATE_SYMLINK, False, "Criar Symlink (arquivo)"),
        (OperationType.CREATE_HARDLINK, False, "Criar Hardlink"),
    ],
)
def test_history_uses_consistent_link_type_labels(operation_type, is_directory, expected, tmp_path):
    from winlink.ui.dialogs.history_dialog import HistoryTableModel

    record = OperationRecord(
        operation_type=operation_type,
        source=tmp_path / ("folder" if is_directory else "file"),
        metadata={"is_directory": is_directory},
    )
    model = HistoryTableModel()

    assert model._get_type_display(record) == expected


def test_legacy_history_defaults_unknown_symlink_category_to_directory(tmp_path):
    from winlink.ui.dialogs.history_dialog import HistoryTableModel

    record = OperationRecord(
        operation_type=OperationType.CREATE_SYMLINK,
        source=tmp_path / "source-no-longer-available",
    )

    assert HistoryTableModel()._get_type_display(record) == "Criar Symlink (pasta)"


def test_compact_type_labels_distinguish_symlink_targets(window, tmp_path):
    from winlink.core.models import Junction

    entries = [
        Junction(
            source=tmp_path / ("folder" if is_directory else "file"),
            target=tmp_path / f"link-{index}",
            junction_type=JunctionType.SYMLINK,
            is_directory=is_directory,
        )
        for index, is_directory in enumerate((True, False))
    ]
    window.junction_model.set_junctions(entries)

    assert (
        window.junction_model.data(window.junction_model.index(0, 3), Qt.ItemDataRole.DisplayRole)
        == "Symlink (pasta)"
    )
    assert (
        window.junction_model.data(window.junction_model.index(1, 3), Qt.ItemDataRole.DisplayRole)
        == "Symlink (arquivo)"
    )
    assert window.create_page.type_combo.itemText(0) == "Junção"


def test_settings_restore_discard_and_save_are_transactional(qtbot, tmp_path):
    settings = AppSettings(
        theme_mode="dark",
        default_link_type="hardlink",
        scan_directories=[str(tmp_path)],
        history_file=tmp_path / "custom.json",
    )
    save_settings(settings)
    original = settings_path().read_bytes()
    dialog = SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.restore_defaults()
    assert dialog.theme_combo.currentData() == "auto"
    assert settings_path().read_bytes() == original
    assert settings.theme_mode == "dark"
    dialog.discard_changes()
    assert dialog.theme_combo.currentData() == "dark"
    dialog.restore_defaults()
    dialog.save_settings()
    assert get_settings().theme_mode == "auto"
    assert get_settings().history_file == tmp_path / "custom.json"
    assert get_settings().confirm_before_destructive


def test_settings_save_failure_keeps_existing_data(qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs import settings_dialog

    settings = AppSettings(theme_mode="dark")
    save_settings(settings)
    original = settings_path().read_bytes()
    dialog = SettingsDialog(settings)
    qtbot.addWidget(dialog)
    dialog.theme_combo.setCurrentIndex(dialog.theme_combo.findData("light"))
    monkeypatch.setattr(settings_dialog, "save_settings", Mock(side_effect=OSError("denied")))
    monkeypatch.setattr(QMessageBox, "critical", Mock())
    dialog.save_settings()
    assert settings.theme_mode == "dark"
    assert settings_path().read_bytes() == original


def test_pages_navigation_reentry_and_keyboard(window, qtbot):
    window.activateWindow()
    window.setFocus()
    qtbot.wait(50)
    qtbot.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 2
    qtbot.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 1
    window._operation_active = True
    window.navigation.setCurrentRow(3)
    assert window.pages.currentIndex() == 1
    assert window.navigation.currentRow() == 1
    window._operation_active = False
    qtbot.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert window.pages.currentIndex() == 0
    assert window.search_edit.hasFocus()


def test_symlink_file_and_directory_filter(window, tmp_path):
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / str(i),
                target=tmp_path / f"link{i}",
                junction_type=JunctionType.SYMLINK,
                is_directory=directory,
            )
            for i, directory in enumerate([True, False])
        ]
    )
    window._selected_types = {"symlink_file"}
    window._apply_active_filters()
    assert window.filter_model.rowCount() == 1
    window._selected_types = {"symlink_dir"}
    window._apply_active_filters()
    assert window.filter_model.rowCount() == 1
    _clear_list_filter_dialog(window)
    assert window.filter_model.rowCount() == 2


def test_multiselect_filter_combinations_empty_selection_and_clear(window, tmp_path):
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / "active",
                target=tmp_path / "active-link",
                junction_type=JunctionType.JUNCTION,
                status=JunctionStatus.ACTIVE,
                creator=Creator.APP,
                tags=["alpha"],
            ),
            Junction(
                source=tmp_path / "broken",
                target=tmp_path / "broken-link",
                junction_type=JunctionType.SYMLINK,
                status=JunctionStatus.BROKEN,
                creator=Creator.MANUAL,
                tags=["beta"],
            ),
            Junction(
                source=tmp_path / "inaccessible",
                target=tmp_path / "inaccessible-link",
                junction_type=JunctionType.HARDLINK,
                is_directory=False,
                status=JunctionStatus.INACCESSIBLE,
                creator=Creator.EXISTING,
                tags=["gamma"],
            ),
        ]
    )
    window._selected_statuses = {"ACTIVE", "BROKEN"}
    window._selected_creators = {"APP", "MANUAL"}
    window._selected_types = {"junction_dir", "symlink_dir"}
    window._selected_tags = {"alpha", "beta"}
    window._apply_active_filters()
    assert window.filter_model.rowCount() == 2

    window._selected_creators = set()
    window._apply_active_filters()
    assert window.filter_model.rowCount() == 0
    _clear_list_filter_dialog(window)
    assert window.filter_model.rowCount() == 3


def test_filter_dialog_all_values_and_empty_selection(window, qtbot, tmp_path):
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / "data",
                target=tmp_path / "link",
                junction_type=JunctionType.JUNCTION,
            )
        ]
    )

    def uncheck_all():
        from PyQt6.QtWidgets import QApplication

        dialog = QApplication.activeModalWidget()
        group = dialog._groups["status"]
        group.set_selected(set())
        dialog.accept()

    QTimer.singleShot(20, uncheck_all)
    window.edit_filters()
    assert window._selected_statuses == set()
    assert window.filter_model.rowCount() == 0
    assert get_settings().list_filter_status_values == []

    def check_all():
        from PyQt6.QtWidgets import QApplication

        dialog = QApplication.activeModalWidget()
        group = dialog._groups["status"]
        group.set_selected(None)
        dialog.accept()

    QTimer.singleShot(20, check_all)
    window.edit_filters()
    assert window._selected_statuses is None
    assert window.filter_model.rowCount() == 1
    assert get_settings().list_filter_status_values is None


def test_filter_multiselect_controls_stay_compact_and_popup_remains_open(qtbot):
    from winlink.ui.dialogs.filter_selection_dialog import FilterSelectionDialog

    dialog = FilterSelectionDialog("Filtros", None)
    options = [(f"Valor {index}", index) for index in range(35)]
    tags = dialog.add_multi_group("tags", "Tag", options, None)
    statuses = dialog.add_multi_group(
        "status", "Status", [("Ativa", "active"), ("Quebrada", "broken")], None
    )
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert tags.combo.sizeHint().height() == statuses.combo.sizeHint().height()
    assert tags.selected_values() is None
    assert tags.combo._summary == "35 selecionados"
    qtbot.mouseClick(tags.combo, Qt.MouseButton.LeftButton, pos=tags.combo.rect().center())
    qtbot.waitUntil(tags.combo._menu.isVisible)
    qtbot.mouseClick(tags.combo._options[3], Qt.MouseButton.LeftButton)
    assert tags.selected_values() == set(range(35)) - {3}
    assert tags.combo._summary == "34 selecionados"
    assert tags.combo._menu.isVisible()
    tags.combo._options[3].setFocus()
    qtbot.keyClick(tags.combo._options[3], Qt.Key.Key_Space)
    assert tags.selected_values() is None


def test_empty_tag_filter_selects_untagged_links_and_persists(window, qtbot, tmp_path):
    from winlink.ui.main_window import EMPTY_TAG_FILTER

    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / "tagged",
                target=tmp_path / "tagged-link",
                junction_type=JunctionType.JUNCTION,
                tags=["photos"],
            ),
            Junction(
                source=tmp_path / "untagged",
                target=tmp_path / "untagged-link",
                junction_type=JunctionType.JUNCTION,
            ),
        ]
    )

    def select_empty_tag():
        from PyQt6.QtWidgets import QApplication

        dialog = QApplication.activeModalWidget()
        assert "(Vazio)" in [
            checkbox.text() for checkbox in dialog._groups["tags"].combo._options.values()
        ]
        dialog._groups["tags"].set_selected({EMPTY_TAG_FILTER})
        dialog.accept()

    QTimer.singleShot(20, select_empty_tag)
    window.edit_filters()

    assert window._selected_tags == set()
    assert window._selected_empty_tag
    assert window.filter_model.rowCount() == 1
    assert (
        window.junction_model.get_junction(
            window.filter_model.mapToSource(window.filter_model.index(0, 0))
        ).source
        == tmp_path / "untagged"
    )
    assert get_settings().list_filter_tags == []
    assert get_settings().list_filter_include_empty_tag


def test_saved_tag_filter_ignores_removed_mode_and_clears_unavailable_tags(
    qtbot, monkeypatch, tmp_path
):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(MainWindow, "start_scan", lambda self: None)
    save_settings(
        AppSettings.model_validate(
            {
                "scan_directories": [str(tmp_path)],
                "remember_window_size": False,
                "list_filter_tags": ["keep"],
                "list_filter_tag_mode": 1,
                "list_filter_tag_modes": ["exclude"],
            }
        )
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window.junction_model.set_junctions(
        [
            Junction(
                source=tmp_path / "data",
                target=tmp_path / "link",
                junction_type=JunctionType.JUNCTION,
                tags=["keep"],
            )
        ]
    )
    window.update_tag_filter_options()
    assert window._selected_tags == {"keep"}
    assert window.filter_model.rowCount() == 1
    window._persist_list_filters()
    restored = MainWindow()
    qtbot.addWidget(restored)
    assert restored._selected_tags == {"keep"}
    assert restored.filter_model.rowCount() == 0

    window.junction_model.set_junctions([])
    window.update_tag_filter_options()
    assert window._selected_tags is None
    assert get_settings().list_filter_tags is None
    assert "list_filter_tag_mode" not in get_settings().model_dump()
    assert "list_filter_tag_modes" not in get_settings().model_dump()


@pytest.mark.parametrize("accept", [False, True])
def test_filters_use_draft(window, accept):
    def edit():
        from PyQt6.QtWidgets import QApplication

        dialog = QApplication.activeModalWidget()
        status = dialog._groups["status"]
        status.set_selected({"BROKEN"})
        dialog.accept() if accept else dialog.reject()

    QTimer.singleShot(20, edit)
    window.edit_filters()
    assert window._selected_statuses == ({"BROKEN"} if accept else None)


def test_history_combines_result_and_removes_custom_date_controls(qtbot, tmp_path):
    from PyQt6.QtWidgets import QApplication, QComboBox

    manager = HistoryManager(tmp_path / "history.json")
    records = [
        OperationRecord(
            operation_type=OperationType.CREATE_JUNCTION,
            timestamp=datetime(2026, 1, 2, 23, 59),
            success=True,
        ),
        OperationRecord(
            operation_type=OperationType.CREATE_JUNCTION,
            timestamp=datetime(2026, 1, 3),
            success=False,
        ),
    ]
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    assert not hasattr(dialog, "from_date")
    assert not hasattr(dialog, "to_date")
    choices = []

    def inspect_filters():
        selection_dialog = QApplication.activeModalWidget()
        period = next(
            combo
            for combo in selection_dialog.findChildren(QComboBox)
            if combo.accessibleName() == "Período"
        )
        choices.extend(
            (period.itemText(index), period.itemData(index)) for index in range(period.count())
        )
        assert period.currentData() is None
        choices.append(selection_dialog.clear_button.text())
        selection_dialog.reject()

    QTimer.singleShot(20, inspect_filters)
    dialog.edit_filters()
    assert choices == [
        ("Todo período", None),
        ("Hoje", "today"),
        ("Última semana", "week"),
        ("Último mês", "month"),
        ("Último ano", "year"),
        "Limpar",
    ]
    assert dialog.filters_btn.text() == "Filtros"
    dialog._filter_results = {"Sucesso"}
    dialog.apply_filters(records)
    assert dialog.table_model.rowCount() == 1
    assert "1 de 2" in dialog.total_label.text()
    assert dialog.clear_history_btn.text() == "Apagar histórico"


@pytest.mark.parametrize("apply", [False, True])
def test_history_filter_dialog_is_a_multi_select_draft(qtbot, monkeypatch, apply):
    from PyQt6.QtWidgets import QApplication

    records = [
        OperationRecord(operation_type=OperationType.CREATE_JUNCTION, success=True),
        OperationRecord(operation_type=OperationType.UNDO_OPERATION, success=False),
    ]
    manager = Mock()
    manager.get_history.return_value = records
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)

    def edit():
        selection_dialog = QApplication.activeModalWidget()
        group = selection_dialog._groups["type"]
        group.set_selected({OperationType.CREATE_JUNCTION})
        if apply:
            results = selection_dialog._groups["result"]
            results.set_selected({"Sucesso"})
        selection_dialog.accept() if apply else selection_dialog.reject()

    QTimer.singleShot(20, edit)
    dialog.edit_filters()
    if apply:
        assert dialog._filter_types == {OperationType.CREATE_JUNCTION}
        assert dialog._filter_results == {"Sucesso"}
        assert dialog.table_model.rowCount() == 1
    else:
        assert dialog._filter_types is None
        assert dialog._filter_results is None
        assert dialog.table_model.rowCount() == 2


def test_history_filter_clear_resets_draft_to_all_values(qtbot, monkeypatch):
    from PyQt6.QtWidgets import QApplication

    records = [
        OperationRecord(operation_type=OperationType.CREATE_JUNCTION, success=True),
        OperationRecord(operation_type=OperationType.UNDO_OPERATION, success=False),
    ]
    manager = Mock()
    manager.get_history.return_value = records
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    dialog._filter_results = {"Falha"}
    dialog._sort_column = 2
    dialog._sort_ascending = True
    dialog.load_history()
    assert dialog.table_model.rowCount() == 1

    def clear():
        selection_dialog = QApplication.activeModalWidget()
        selection_dialog.clear_button.click()
        selection_dialog.accept()

    QTimer.singleShot(20, clear)
    dialog.edit_filters()
    assert dialog._filter_results is None
    assert dialog._filter_types is None
    assert dialog._filter_date_range is None
    assert dialog._sort_column == 0
    assert not dialog._sort_ascending
    assert dialog.table_model.rowCount() == 2


def test_history_period_filter_is_single_select_and_applies(qtbot):
    from PyQt6.QtWidgets import QApplication, QComboBox

    manager = Mock()
    manager.get_history.return_value = []
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)

    def select_year():
        selection_dialog = QApplication.activeModalWidget()
        period = next(
            combo
            for combo in selection_dialog.findChildren(QComboBox)
            if combo.accessibleName() == "Período"
        )
        period.setCurrentIndex(period.findData("year"))
        selection_dialog.accept()

    QTimer.singleShot(20, select_year)
    dialog.edit_filters()
    assert dialog._filter_date_range == "year"


def test_history_sorting_defaults_to_newest_and_sorts_every_column(qtbot, tmp_path):
    from PyQt6.QtWidgets import QApplication, QComboBox

    records = [
        OperationRecord(
            operation_type=OperationType.CREATE_JUNCTION,
            timestamp=datetime(2026, 1, 1),
            source=tmp_path / "source-z",
            target=tmp_path / "target-z",
            success=True,
        ),
        OperationRecord(
            operation_type=OperationType.UNDO_OPERATION,
            timestamp=datetime(2026, 1, 3),
            source=tmp_path / "source-a",
            target=tmp_path / "target-a",
            success=True,
        ),
        OperationRecord(
            operation_type=OperationType.CREATE_SYMLINK,
            timestamp=datetime(2026, 1, 2),
            source=tmp_path / "source-m",
            target=tmp_path / "target-m",
            success=False,
        ),
    ]
    manager = Mock()
    manager.get_history.return_value = records
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)

    def operations_in_table():
        return [
            dialog.table_model.get_operation(dialog.table_model.index(row, 0))
            for row in range(dialog.table_model.rowCount())
        ]

    assert dialog._sort_column == 0
    assert not dialog._sort_ascending
    assert [operation.timestamp for operation in operations_in_table()] == [
        datetime(2026, 1, 3),
        datetime(2026, 1, 2),
        datetime(2026, 1, 1),
    ]

    for column, key in [
        (0, lambda operation: operation.timestamp),
        (1, lambda operation: dialog.table_model._get_type_display(operation).casefold()),
        (2, lambda operation: str(operation.target or operation.source or "").casefold()),
        (3, lambda operation: dialog.table_model._get_display_data(operation, 3).casefold()),
    ]:
        dialog._sort_column = column
        dialog._sort_ascending = True
        dialog.load_history()
        assert [key(operation) for operation in operations_in_table()] == sorted(
            key(operation) for operation in records
        )

    dialog._sort_column = 4
    dialog._sort_ascending = True
    dialog.load_history()
    assert [operation.operation_type for operation in operations_in_table()] == [
        OperationType.CREATE_JUNCTION,
        OperationType.CREATE_SYMLINK,
        OperationType.UNDO_OPERATION,
    ]

    def edit_sort():
        selection_dialog = QApplication.activeModalWidget()
        sort_column = next(
            combo
            for combo in selection_dialog.findChildren(QComboBox)
            if combo.accessibleName() == "Ordenar por"
        )
        sort_order = next(
            combo
            for combo in selection_dialog.findChildren(QComboBox)
            if combo.accessibleName() == "Ordem"
        )
        assert [sort_column.itemText(index) for index in range(sort_column.count())] == [
            "Data / Hora",
            "Ação Realizada",
            "Ponto de Acesso",
            "Status",
            "Recuperação",
        ]
        assert sort_column.currentIndex() == 4
        assert sort_order.currentText() == "Crescente"
        sort_column.setCurrentIndex(0)
        sort_order.setCurrentIndex(1)
        selection_dialog.accept()

    QTimer.singleShot(20, edit_sort)
    dialog.edit_filters()
    assert dialog._sort_column == 0
    assert not dialog._sort_ascending
    assert [operation.timestamp for operation in operations_in_table()] == [
        datetime(2026, 1, 3),
        datetime(2026, 1, 2),
        datetime(2026, 1, 1),
    ]


def test_legacy_undone_creation_cannot_be_repeated(qtbot, monkeypatch, tmp_path):
    manager = HistoryManager(tmp_path / "history.json")
    creation = OperationRecord(
        operation_type=OperationType.CREATE_JUNCTION,
        source=tmp_path / "data",
        target=tmp_path / "link",
        timestamp=datetime(2026, 1, 1),
    )
    undo = OperationRecord(
        operation_type=OperationType.UNDO_OPERATION,
        source=creation.source,
        target=creation.target,
        timestamp=datetime(2026, 1, 2),
    )
    records = [undo, creation]
    assert creation_was_undone(creation, records)
    manager._save_history([record.model_dump() for record in [creation, undo]])
    dialog = HistoryDialog(manager)
    qtbot.addWidget(dialog)
    dialog.table_view.setCurrentIndex(dialog.table_model.index(1, 0))
    monkeypatch.setattr(QMessageBox, "warning", Mock())
    with qtbot.assertNotEmitted(dialog.undo_requested):
        dialog.undo_selected()
    assert dialog.table_model.data(dialog.table_model.index(1, 3)) == "Criação desfeita"


def test_small_window_pages_can_scroll_to_last_control(window, qtbot):
    window.resize(760, 400)
    for index, button in [(1, window.create_page.create_btn), (3, window.settings_page.save_btn)]:
        window.navigate(index)
        qtbot.wait(10)
        area = window.pages.currentWidget()
        assert isinstance(area, QScrollArea)
        area.ensureWidgetVisible(button)
        qtbot.wait(10)
        assert (
            area.viewport()
            .rect()
            .intersects(
                button.rect().translated(button.mapTo(area.viewport(), button.rect().topLeft()))
            )
        )


def test_quick_theme_persists_auto_and_manual(window, monkeypatch):
    window.quick_theme.setCurrentIndex(window.quick_theme.findData("dark"))
    assert get_settings().theme_mode == "dark"
    window.quick_theme.setCurrentIndex(window.quick_theme.findData("auto"))
    monkeypatch.setattr(window.theme_manager, "get_system_theme", lambda: "light")
    window.theme_manager.refresh_system_theme()
    assert window.theme_manager.current_theme == "light"
    assert get_settings().theme_mode == "auto"


def test_history_detects_replaced_junction_even_same_destination(qtbot, monkeypatch, tmp_path):
    from winlink.core.operations import create_junction

    data, link, old = tmp_path / "data", tmp_path / "link", tmp_path / "old"
    data.mkdir()
    assert create_junction(data, link)
    manager = HistoryManager(tmp_path / "history.json")
    assert manager.add_operation(OperationType.CREATE_JUNCTION, data, link)
    record = manager.get_history()[0]
    assert record.metadata["link_identity"]
    link.rename(old)
    try:
        assert create_junction(data, link)
        dialog = HistoryDialog(manager)
        qtbot.addWidget(dialog)
        dialog.table_view.setCurrentIndex(dialog.table_model.index(0, 0))
        warning = Mock()
        monkeypatch.setattr(QMessageBox, "warning", warning)
        with qtbot.assertNotEmitted(dialog.undo_requested):
            dialog.undo_selected()
        warning.assert_called_once()
        assert link.is_junction()
    finally:
        if link.is_junction():
            link.rmdir()
        old.rmdir()


def test_failed_scan_preserves_last_list(window, tmp_path):
    from winlink.core.models import ScanResult

    junction = Junction(
        source=tmp_path / "data", target=tmp_path / "link", junction_type=JunctionType.JUNCTION
    )
    window.junction_model.set_junctions([junction])
    window.on_scan_finished(
        ScanResult(
            errors=["Acesso negado"], excluded_directories=list(window.discovery_exclusions())
        )
    )
    assert window.junction_model.rowCount() == 1
    assert "preservada" in window.scan_notice.text()
    window.on_scan_finished(ScanResult(excluded_directories=list(window.discovery_exclusions())))
    assert window.junction_model.rowCount() == 0
    assert window.scan_notice.isHidden()


def test_progress_escape_requests_cooperative_cancel(qtbot):
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    dialog = ProgressDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    with qtbot.waitSignal(dialog.cancellation_requested):
        qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.isVisible()
    assert not dialog.cancel_btn.isEnabled()
    dialog.set_operation_finished(False, "Operação cancelada")
    assert dialog.status_label.text().startswith("Cancelado")
    qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert not dialog.isVisible()


def test_new_creation_page_runs_real_preview_and_junction(window, qtbot, monkeypatch, tmp_path):
    from winlink.ui.dialogs.preview_dialog import PreviewDialog
    from winlink.ui.dialogs.progress_dialog import ProgressDialog
    from PyQt6.QtWidgets import QApplication

    source, target = tmp_path / "data", tmp_path / "new-link"
    source.mkdir()
    (source / "important.txt").write_text("preserve")
    for name in ["warning", "information", "critical"]:
        monkeypatch.setattr(QMessageBox, name, Mock(return_value=QMessageBox.StandardButton.Yes))
    window.navigate(1)
    page = window.create_page
    page.source_edit.setText(str(source))
    page.target_edit.setText(str(target))
    timer = QTimer()

    def confirm():
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, PreviewDialog) and dialog.confirm_btn.isEnabled():
            timer.stop()
            dialog.confirm_btn.click()

    timer.timeout.connect(confirm)
    timer.start(10)
    try:
        page.create_btn.click()
        assert target.is_junction()
        assert (target / "important.txt").read_text() == "preserve"
        assert window.history_manager.get_history()[0].success
        assert window.history_manager.get_history()[0].metadata["link_identity"]
    finally:
        timer.stop()
        for widget in window.findChildren(ProgressDialog):
            widget.set_operation_finished(True)
            widget.close()
        if target.is_junction():
            target.rmdir()


def test_broken_directory_remove_only_checks_reference(tmp_path):
    from winlink.core.operations import create_junction, verify_directory_link_reference

    source, target, moved = tmp_path / "source", tmp_path / "link", tmp_path / "moved"
    source.mkdir()
    (source / "keep.txt").write_text("keep")
    assert create_junction(source, target)
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    try:
        source.rename(moved)
        assert verify_directory_link_reference(junction)
        changed = Junction(
            source=tmp_path / "different", target=target, junction_type=JunctionType.JUNCTION
        )
        assert not verify_directory_link_reference(changed)
        assert (moved / "keep.txt").read_text() == "keep"
    finally:
        target.rmdir()


def test_properties_reversal_request_preserves_selection_until_confirmed(qtbot, tmp_path):
    from winlink.ui.dialogs.properties_dialog import PropertiesDialog

    data = tmp_path / "data"
    data.mkdir()
    junction = Junction(source=data, target=tmp_path / "link", junction_type=JunctionType.JUNCTION)
    dialog = PropertiesDialog(junction)
    qtbot.addWidget(dialog)
    assert not dialog.tags_edit.placeholderText()
    dialog.show()
    with qtbot.waitSignal(dialog.undo_requested):
        dialog.undo_btn.click()
    assert dialog.isVisible()
    assert dialog.junction == junction


def test_stale_scan_cannot_restore_newly_excluded_links(window, tmp_path, monkeypatch):
    from winlink.core.cache import CacheManager
    from winlink.core.models import ScanResult

    excluded = tmp_path / "excluded"
    junction = Junction(
        source=tmp_path / "data",
        target=excluded / "link",
        junction_type=JunctionType.JUNCTION,
    )
    previous = list(window.discovery_exclusions())
    window.junction_model.set_junctions([junction])
    window.settings.scan_excluded_directories = [str(excluded)]
    window.settings_saved()
    assert window.junction_model.rowCount() == 0

    def unexpected_save(*args):
        pytest.fail("stale scan must not replace cache")

    monkeypatch.setattr(CacheManager, "save", unexpected_save)
    window.on_scan_finished(ScanResult(junctions=[junction], excluded_directories=previous))
    assert window.junction_model.rowCount() == 0
