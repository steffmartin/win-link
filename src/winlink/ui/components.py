"""Shared presentation components matching the approved prototype."""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from winlink.ui.icons import set_button_icon, symbol_icon


class NavigationDelegate(QStyledItemDelegate):
    """Keep keyboard focus around the full item, without the native text outline."""

    def paint(self, painter, option, index):
        option = QStyleOptionViewItem(option)
        view = self.parent()
        focused = bool(option.state & QStyle.StateFlag.State_HasFocus)
        option.state &= ~QStyle.StateFlag.State_HasFocus
        super().paint(painter, option, index)
        if focused and view.keyboard_focus:
            painter.save()
            painter.setPen(option.palette.highlight().color())
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(option.rect.adjusted(1, 1, -2, -2), 6, 6)
            painter.restore()


class NavigationList(QListWidget):
    keyboard_focus = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(NavigationDelegate(self))

    def focusInEvent(self, event):
        self.keyboard_focus = event.reason() != Qt.FocusReason.MouseFocusReason
        super().focusInEvent(event)

    def mousePressEvent(self, event):
        self.keyboard_focus = False
        super().mousePressEvent(event)
        self.viewport().update()

    def keyPressEvent(self, event):
        self.keyboard_focus = True
        super().keyPressEvent(event)
        self.viewport().update()


def heading(layout, text, subtitle=None, icon=None):
    row = QHBoxLayout()
    row.setSpacing(10)
    if icon:
        artwork = QLabel()
        artwork.setPixmap(symbol_icon(icon, "#3b82f6").pixmap(24, 24))
        row.addWidget(artwork)
    label = QLabel(text)
    label.setObjectName("pageTitle")
    row.addWidget(label)
    row.addStretch()
    layout.addLayout(row)
    if subtitle:
        description = QLabel(subtitle)
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(description)
    return row


def field(layout, text, widget):
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    label.setBuddy(widget)
    layout.addWidget(label)
    layout.addWidget(widget)
    return label


def contextual_help(title, description):
    from PyQt6.QtWidgets import QToolButton, QToolTip

    help_button = QToolButton()
    set_button_icon(help_button, "info")
    help_button.setAutoRaise(True)
    help_button.setToolTip(description)
    help_button.setAccessibleName(f"Ajuda: {title}")
    help_button.setAccessibleDescription(description)
    help_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    help_button.clicked.connect(
        lambda: QToolTip.showText(
            help_button.mapToGlobal(help_button.rect().bottomLeft()), description, help_button
        )
    )
    return help_button


def help_row(widget, title, description):
    row = QWidget()
    box = QHBoxLayout(row)
    box.setContentsMargins(0, 0, 0, 0)
    box.setSpacing(8)
    box.addWidget(widget)
    box.addWidget(contextual_help(title, description))
    box.addStretch()
    return row


def button_style(button, icon=None, primary=False, danger=False):
    button.setProperty("primary", primary)
    button.setProperty("danger", danger)
    button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    if icon:
        set_button_icon(button, icon)
    return button


class Columns(QWidget):
    """Stack content below 850 logical pixels without fixed child widths."""

    def __init__(self, left, right, parent=None):
        super().__init__(parent)
        self.box = QBoxLayout(QBoxLayout.Direction.TopToBottom, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(32)
        self.box.addWidget(left, 1)
        self.box.addWidget(right, 1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def minimumSizeHint(self):
        return QSize(0, self.box.minimumSize().height())

    def resizeEvent(self, event):
        direction = (
            QBoxLayout.Direction.LeftToRight
            if self.width() >= 850
            else QBoxLayout.Direction.TopToBottom
        )
        self.box.setDirection(direction)
        self.box.activate()
        self.setMinimumHeight(self.box.minimumSize().height())
        self.updateGeometry()
        super().resizeEvent(event)


class Panel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(24, 24, 24, 24)
        self.content.setSpacing(16)


class TypeButton(QPushButton):
    def __init__(self, title, description, icon, help_text, indicator=None, indicator_help=None):
        super().__init__(title)
        from PyQt6.QtWidgets import QStyle, QStyleOptionButton, QStylePainter

        self.setCheckable(True)
        self.setObjectName("typeCard")
        self.setAccessibleName(title)
        self.setMinimumHeight(110)
        box = QVBoxLayout(self)
        box.setContentsMargins(16, 14, 16, 14)
        box.setSpacing(8)
        row = QHBoxLayout()
        art = QLabel()
        art.setProperty("glyph", icon)
        art.setPixmap(symbol_icon(icon, "#3b82f6").pixmap(20, 20))
        row.addWidget(art)
        name = QLabel(title)
        name.setObjectName("fieldLabel")
        row.addWidget(name)
        row.addStretch()
        if indicator:
            indicator_label = QLabel()
            indicator_label.setProperty("glyph", indicator)
            indicator_label.setPixmap(symbol_icon(indicator).pixmap(16, 16))
            indicator_label.setToolTip(indicator_help or "")
            indicator_label.setAccessibleName(indicator_help or title)
            indicator_label.setAccessibleDescription(indicator_help or "")
            row.addWidget(indicator_label)
        row.addWidget(contextual_help(title, help_text))
        box.addLayout(row)
        desc = QLabel(description)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        box.addWidget(desc)
        for label in self.findChildren(QLabel):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._style_types = (QStyle, QStyleOptionButton, QStylePainter)

    def paintEvent(self, event):
        from PyQt6.QtGui import QIcon

        style, option_type, painter_type = self._style_types
        option = option_type()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter = painter_type(self)
        painter.drawControl(style.ControlElement.CE_PushButton, option)


class ActionRow(QWidget):
    def __init__(self, buttons, parent=None):
        super().__init__(parent)
        self.buttons = buttons
        self.box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(12)
        self.box.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for button in buttons:
            self.box.addWidget(button)

    def minimumSizeHint(self):
        return QSize(0, self.box.minimumSize().height())

    def resizeEvent(self, event):
        required = sum(button.sizeHint().width() for button in self.buttons) + 12 * (
            len(self.buttons) - 1
        )
        self.box.setDirection(
            QBoxLayout.Direction.TopToBottom
            if self.width() < required
            else QBoxLayout.Direction.LeftToRight
        )
        self.box.activate()
        self.setMinimumHeight(self.box.minimumSize().height())
        self.updateGeometry()
        super().resizeEvent(event)


class FieldGrid(QWidget):
    def __init__(self, fields, parent=None):
        from PyQt6.QtWidgets import QGridLayout

        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(16)
        self.fields = []
        for title, control in fields:
            container = QWidget()
            container.setObjectName("fieldContainer")
            box = QVBoxLayout(container)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(6)
            field(box, title, control)
            self.fields.append(container)
        self._columns = 0
        self.reflow(1)

    def reflow(self, columns):
        if columns == self._columns:
            return
        self._columns = columns
        for index, container in enumerate(self.fields):
            self.grid.addWidget(container, index // columns, index % columns)
        for column in range(3):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def minimumSizeHint(self):
        return QSize(0, self.grid.minimumSize().height())

    def resizeEvent(self, event):
        self.reflow(3 if self.width() >= 660 else 2 if self.width() >= 360 else 1)
        super().resizeEvent(event)
