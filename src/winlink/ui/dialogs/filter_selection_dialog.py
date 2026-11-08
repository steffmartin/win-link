"""Reusable responsive filter dialog with draft selections."""

from collections.abc import Sequence

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionComboBox,
    QStylePainter,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from winlink.ui.components import button_style, heading
from winlink.ui.dialogs.animated_dialog import AnimatedDialog


class MultiSelectComboBox(QComboBox):
    """Compact combo with an independent checkable popup."""

    def __init__(self, options: Sequence[tuple[str, object]], accessible_name: str):
        super().__init__()
        self._options: dict[object, QCheckBox] = {}
        self._menu = QMenu(self)
        self._menu.setAccessibleName(f"Opções de {accessible_name}")
        self._options_panel = QWidget()
        self._options_layout = QVBoxLayout(self._options_panel)
        self._options_layout.setContentsMargins(8, 8, 8, 8)
        self._options_layout.setSpacing(4)
        for label, value in options:
            checkbox = QCheckBox(label, self._options_panel)
            checkbox.setAccessibleName(label)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._update_summary)
            self._options[value] = checkbox
            self._options_layout.addWidget(checkbox)
        self._options_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(280)
        scroll.setWidget(self._options_panel)
        action = QWidgetAction(self._menu)
        action.setDefaultWidget(scroll)
        self._menu.addAction(action)
        self._summary = ""
        self.setAccessibleName(accessible_name)
        self._update_summary()

    def set_selected(self, selected: set | None) -> None:
        selected_values = set(self._options) if selected is None else selected
        for value, checkbox in self._options.items():
            checkbox.setChecked(value in selected_values)
        self._update_summary()

    def selected_values(self) -> set | None:
        values = {value for value, checkbox in self._options.items() if checkbox.isChecked()}
        if not self._options or len(values) == len(self._options):
            return None
        return values

    def option_values(self) -> list[object]:
        return list(self._options)

    def _update_summary(self, *_args) -> None:
        checked = sum(checkbox.isChecked() for checkbox in self._options.values())
        if checked == 1:
            self._summary = "1 selecionado"
        else:
            self._summary = f"{checked} selecionados"
        self.update()

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = self._summary
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)

    def showPopup(self) -> None:
        width = max(self.width(), min(self._options_panel.sizeHint().width() + 24, 420))
        self._menu.setFixedWidth(width)
        self._menu.setFixedHeight(min(self._options_panel.sizeHint().height() + 20, 280))
        self._menu.popup(self.mapToGlobal(self.rect().bottomLeft()))

    def hidePopup(self) -> None:
        self._menu.hide()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._menu.isVisible():
                self._menu.hide()
            else:
                self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Down):
            if not self._menu.isVisible():
                self.showPopup()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._menu.hide()
            event.accept()
            return
        super().keyPressEvent(event)


class MultiSelectionGroup(QGroupBox):
    def __init__(self, title: str, options: Sequence[tuple[str, object]], selected: set | None):
        super().__init__(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.combo = MultiSelectComboBox(options, title)
        self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo.setMinimumWidth(140)
        self.combo.setMaximumWidth(360)
        self.combo.setFixedHeight(self.combo.sizeHint().height())
        layout.addWidget(self.combo)
        self.set_selected(selected)

    def set_selected(self, selected: set | None) -> None:
        self.combo.set_selected(selected)

    def selected_values(self) -> set | None:
        return self.combo.selected_values()

    def clear_selection(self) -> None:
        self.set_selected(None)

    def option_values(self) -> list[object]:
        return self.combo.option_values()


class FilterSelectionDialog(AnimatedDialog):
    """Three-column filter editor; selections are committed only on Apply."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.preferred_width = 920
        self._groups: dict[str, QGroupBox] = {}
        self._grid_columns = 3
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(10)
        heading(self._content_layout, title, icon="filter")
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(8)
        self._content_layout.addLayout(self._grid)
        self._actions = QHBoxLayout()
        self.clear_button = button_style(QPushButton("Limpar"), "refresh")
        self.clear_button.clicked.connect(self.clear_selections)
        self._actions.addWidget(self.clear_button)
        self._actions.addStretch()
        self._content_layout.addLayout(self._actions)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        self.apply_button = buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.apply_button.setText("Aplicar")
        self.cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setText("Cancelar")
        button_style(self.apply_button, "filter", primary=True)
        button_style(self.cancel_button, "close")
        self.apply_button.clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._actions.addWidget(buttons)
        self._content_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def add_multi_group(
        self, key: str, title: str, options: Sequence[tuple[str, object]], selected: set | None
    ) -> MultiSelectionGroup:
        group = MultiSelectionGroup(title, options, selected)
        self._add_group(key, group)
        return group

    def add_control_group(self, key: str, title: str, control: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(control)
        self._add_group(key, group)
        return group

    def _add_group(self, key: str, group: QGroupBox) -> None:
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._groups[key] = group
        self._reflow()

    def _reflow(self) -> None:
        while self._grid.count():
            self._grid.takeAt(0)
        for index, group in enumerate(self._groups.values()):
            row, column = divmod(index, self._grid_columns)
            self._grid.addWidget(group, row, column, Qt.AlignmentFlag.AlignTop)
        for column in range(3):
            self._grid.setColumnStretch(column, 1 if column < self._grid_columns else 0)

    def selected(self, key: str):
        group = self._groups[key]
        if isinstance(group, MultiSelectionGroup):
            return group.selected_values()
        raise TypeError(f"Filter group {key!r} is not a selection group")

    def clear_selections(self) -> None:
        for group in self._groups.values():
            if isinstance(group, MultiSelectionGroup):
                group.clear_selection()

    def resizeEvent(self, event):
        width = self.width()
        columns = 3 if width >= 820 else 2 if width >= 560 else 1
        if columns != self._grid_columns:
            self._grid_columns = columns
            self._reflow()
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        area = self.findChild(QScrollArea)
        if area is not None:
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if not getattr(self, "_compact_size_applied", False):
            self._compact_size_applied = True
            QTimer.singleShot(0, self._fit_compact_height)

    def _fit_compact_height(self) -> None:
        area = self.findChild(QScrollArea)
        content = area.widget() if area is not None else None
        if content is not None and content.layout() is not None:
            available = self.screen().availableGeometry()
            height = content.layout().sizeHint().height() + 40
            self.resize(self.width(), min(height, int(available.height() * 0.9)))
