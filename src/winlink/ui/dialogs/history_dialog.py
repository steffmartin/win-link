"""Dialog for displaying operation history"""

from datetime import datetime, timedelta

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)

from winlink.core.history import HistoryManager, creation_was_undone
from winlink.core.models import OperationRecord, OperationType
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.ui.dialogs.filter_selection_dialog import FilterSelectionDialog
from winlink.utils.logger import get_logger


class HistoryTableModel(QAbstractTableModel):
    """Model for displaying operation history"""

    _operations: list[OperationRecord]

    COLUMNS = [
        "Data / Hora",
        "Ação Realizada",
        "Ponto de Acesso",
        "Status",
        "Recuperação",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._operations: list[OperationRecord] = []
        self.all_operations: list[OperationRecord] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows"""
        if parent.isValid():
            return 0
        return len(self._operations)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns"""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return data for a cell"""
        if not index.isValid():
            return None

        if index.row() >= len(self._operations):
            return None

        operation = self._operations[int(index.row())]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(operation, column)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip_data(operation)
        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_foreground_color(operation)

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):
        """Return header data"""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def _get_display_data(self, operation: OperationRecord, column: int) -> str:
        """Get display data for a column"""
        if column == 0:  # Data
            return operation.timestamp.strftime("%d/%m/%Y %H:%M")
        elif column == 1:  # Tipo
            return self._get_type_display(operation)
        elif column == 2:  # Detalhes
            return str(operation.target or operation.source or "—")
        elif column == 3:
            if creation_was_undone(operation, self.all_operations):
                return "Criação desfeita"
            if operation.metadata.get("result") == "cancelled":
                return "Cancelado"
            return "Sucesso" if operation.success else "Falha"
        return ""

    def _get_tooltip_data(self, operation: OperationRecord) -> str:
        """Get tooltip data"""
        tooltip = f"Tipo: {self._get_type_display(operation)}\n"
        tooltip += f"Data: {operation.timestamp.isoformat()}\n"
        if operation.source:
            tooltip += f"Dados Físicos: {operation.source}\n"
        if operation.target:
            tooltip += f"Ponto de Acesso: {operation.target}\n"
        if operation.error_message:
            tooltip += f"Erro: {operation.error_message}"
        return tooltip

    def _get_foreground_color(self, operation: OperationRecord) -> QColor | None:
        """Get foreground color based on operation type"""
        if not operation.success:
            return QColor("#C42B1A")
        return None

    def _get_type_display(self, operation: OperationRecord | OperationType) -> str:
        """Get display text for operation type"""
        from winlink.core.models import JunctionType
        from winlink.ui.type_labels import link_type_label

        operation_type = (
            operation.operation_type if isinstance(operation, OperationRecord) else operation
        )
        type_names = {
            OperationType.REMOVE_JUNCTION: "Remover Junção",
            OperationType.UNDO_OPERATION: "Desfazer",
            OperationType.MOVE_FILES: "Mover Arquivos",
            OperationType.COPY_FILES: "Copiar Arquivos",
        }
        if operation_type in (
            OperationType.CREATE_JUNCTION,
            OperationType.CREATE_SYMLINK,
            OperationType.CREATE_HARDLINK,
        ):
            is_directory = (
                operation.metadata.get("is_directory")
                if isinstance(operation, OperationRecord)
                else operation_type != OperationType.CREATE_HARDLINK
            )
            if not isinstance(is_directory, bool):
                source = operation.source if isinstance(operation, OperationRecord) else None
                is_directory = source.is_dir() if source and source.exists() else True
            link_type = {
                OperationType.CREATE_JUNCTION: JunctionType.JUNCTION,
                OperationType.CREATE_SYMLINK: JunctionType.SYMLINK,
                OperationType.CREATE_HARDLINK: JunctionType.HARDLINK,
            }[operation_type]
            return f"Criar {link_type_label(link_type, is_directory)}"
        return type_names.get(operation_type, operation_type.value)

    def _get_details_display(self, operation: OperationRecord) -> str:
        """Get display text for details"""
        if operation.source and operation.target:
            source_name = operation.source.name
            target_name = operation.target.name
            return f"{source_name} -> {target_name}"
        elif operation.source:
            return str(operation.source)
        elif operation.target:
            return str(operation.target)
        return ""

    def set_operations(self, operations: list[OperationRecord]) -> None:
        """Set the list of operations"""
        self.beginResetModel()
        self._operations = operations
        self.endResetModel()

    def get_operation(self, index: QModelIndex) -> OperationRecord | None:
        """Get operation at a given index"""
        if not index.isValid() or index.row() >= len(self._operations):
            return None
        return self._operations[int(index.row())]


class HistoryDialog(AnimatedDialog):
    """Dialog for displaying operation history"""

    undo_requested = pyqtSignal(object)

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.history_manager = history_manager

        self._filter_types: set[OperationType] | None = None
        self._filter_date_range: str | None = None
        self._filter_results: set[str] | None = None
        self._sort_column = 0
        self._sort_ascending = False

        self.init_ui()
        self.load_history()

    def init_ui(self):
        from winlink.ui.components import button_style, heading

        self.setWindowTitle("Histórico de Operações")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        heading(layout, "Histórico de Operações")
        self.export_btn = button_style(QPushButton("Exportar"), "download")
        self.export_btn.clicked.connect(self.export_history)
        self.clear_history_btn = button_style(QPushButton("Apagar histórico"), "trash")
        self.clear_history_btn.clicked.connect(self.clear_history)
        history_actions = QHBoxLayout()
        self.filters_btn = button_style(QPushButton("Filtros"), "filter")
        self.filters_btn.clicked.connect(self.edit_filters)
        history_actions.addWidget(self.filters_btn)
        history_actions.addStretch()
        history_actions.addWidget(self.export_btn)
        history_actions.addWidget(self.clear_history_btn)
        layout.addLayout(history_actions)
        note = QLabel(
            'Registro de criações e reversões. Use "Desfazer" para reverter a criação selecionada.'
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        layout.addWidget(note)
        self.total_label = QLabel()
        self.total_label.setObjectName("muted")
        layout.addWidget(self.total_label)
        self.table_model = HistoryTableModel(self)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setWordWrap(False)
        self.table_view.setMinimumHeight(240)
        self.table_view.setShowGrid(False)
        history_header = self.table_view.horizontalHeader()
        history_header.setMinimumSectionSize(48)
        history_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.verticalHeader().hide()
        self.table_view.verticalHeader().setDefaultSectionSize(64)
        for index, width in enumerate((150, 150, 240, 160, 230)):
            self.table_view.setColumnWidth(index, width)
        from winlink.ui.history_actions import HistoryActionDelegate, HistoryStatusDelegate

        delegate = HistoryActionDelegate(self.table_view)
        delegate.requested.connect(self.row_action)
        self.table_view.setItemDelegateForColumn(4, delegate)
        self.table_view.setItemDelegateForColumn(3, HistoryStatusDelegate(self.table_view))
        layout.addWidget(self.table_view, 1)
        self.details_btn = button_style(QPushButton("Detalhes"), "info")
        self.details_btn.clicked.connect(self.show_details)
        self.undo_btn = button_style(QPushButton("Desfazer selecionada"), "undo")
        self.undo_btn.clicked.connect(self.undo_selected)
        # Keyboard-accessible alternatives to the per-row pointer actions.
        actions = QHBoxLayout()
        actions.addWidget(self.details_btn)
        actions.addWidget(self.undo_btn)
        actions.addStretch()
        layout.addLayout(actions)
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.hide()
        layout.addWidget(self.close_btn)

    def row_action(self, index, action):
        self.table_view.setCurrentIndex(index)
        self.undo_selected() if action == "undo" else self.show_details()

    def show_details(self):
        record = self.table_model.get_operation(self.table_view.currentIndex())
        if record:
            import json

            dialog = AnimatedDialog(self)
            dialog.setWindowTitle("Detalhes da operação")
            from winlink.ui.components import button_style, heading

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(16)
            heading(layout, "Detalhes da operação", icon="info")
            details = QTextEdit()
            details.setReadOnly(True)
            details.setPlainText(
                self.table_model._get_tooltip_data(record)
                + "\n"
                + json.dumps(record.metadata, ensure_ascii=False, indent=2)
            )
            layout.addWidget(details)
            close = button_style(QPushButton("Fechar"), "close")
            close.clicked.connect(dialog.accept)
            layout.addWidget(close)
            dialog.exec()

    def undo_selected(self):
        from winlink.core.models import Creator, Junction, JunctionType
        from winlink.core.operations import verify_junction_integrity

        record = self.table_model.get_operation(self.table_view.currentIndex())
        types = {
            OperationType.CREATE_JUNCTION: JunctionType.JUNCTION,
            OperationType.CREATE_SYMLINK: JunctionType.SYMLINK,
            OperationType.CREATE_HARDLINK: JunctionType.HARDLINK,
        }
        if (
            not record
            or creation_was_undone(record, self.history_manager.get_history())
            or not record.success
            or record.operation_type not in types
            or not record.source
            or not record.target
        ):
            QMessageBox.warning(
                self, "Histórico", "Selecione uma criação bem-sucedida para desfazer."
            )
            return
        for field, path in [("link_identity", record.target), ("source_identity", record.source)]:
            expected = record.metadata.get(field)
            if expected:
                try:
                    actual = path.lstat() if field == "link_identity" else path.stat()
                    matches = expected == [actual.st_dev, actual.st_ino]
                except OSError:
                    matches = False
                if not matches:
                    QMessageBox.warning(
                        self,
                        "Histórico",
                        "A identidade do link ou dos dados mudou. Atualize a lista; esta criação não pode ser desfeita pelo histórico.",
                    )
                    return
        junction = Junction(
            source=record.source,
            target=record.target,
            junction_type=types[record.operation_type],
            creator=Creator.APP,
            is_directory=record.source.is_dir(),
        )
        if not verify_junction_integrity(junction):
            QMessageBox.warning(
                self, "Histórico", "O link foi removido ou alterado. Atualize a lista."
            )
            return
        self.accept()
        self.undo_requested.emit(junction)

    def load_history(self):
        """Load history from manager"""
        operations = self.history_manager.get_history()
        self.apply_filters(operations)

    def edit_filters(self):
        dialog = FilterSelectionDialog("Filtros do histórico", self)
        dialog.clear_button.setText("Limpar")
        type_options = [
            (HistoryTableModel()._get_type_display(operation), operation)
            for operation in OperationType
        ]
        dialog.add_multi_group(
            "type",
            "Operação",
            type_options,
            self._filter_types,
        )
        date_range = QComboBox()
        date_range.setAccessibleName("Período")
        date_range.addItem("Todo período", None)
        date_range.addItem("Hoje", "today")
        date_range.addItem("Última semana", "week")
        date_range.addItem("Último mês", "month")
        date_range.addItem("Último ano", "year")
        index = date_range.findData(self._filter_date_range)
        date_range.setCurrentIndex(max(0, index))
        dialog.add_control_group("date", "Período", date_range)
        dialog.clear_button.clicked.connect(lambda: date_range.setCurrentIndex(0))
        dialog.add_multi_group(
            "result",
            "Resultado",
            [(result, result) for result in ["Sucesso", "Falha", "Cancelado", "Criação desfeita"]],
            self._filter_results,
        )
        sort_column = QComboBox()
        sort_column.setAccessibleName("Ordenar por")
        sort_column.addItems(HistoryTableModel.COLUMNS)
        sort_column.setCurrentIndex(self._sort_column)
        dialog.add_control_group("sort_column", "Ordenar por", sort_column)
        sort_order = QComboBox()
        sort_order.setAccessibleName("Ordem")
        sort_order.addItems(["Crescente", "Decrescente"])
        sort_order.setCurrentIndex(0 if self._sort_ascending else 1)
        dialog.add_control_group("sort_order", "Ordem", sort_order)
        dialog.clear_button.clicked.connect(lambda: sort_column.setCurrentIndex(0))
        dialog.clear_button.clicked.connect(lambda: sort_order.setCurrentIndex(1))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._filter_types = dialog.selected("type")
        self._filter_date_range = date_range.currentData()
        self._filter_results = dialog.selected("result")
        self._sort_column = sort_column.currentIndex()
        self._sort_ascending = sort_order.currentIndex() == 0
        self.load_history()

    def apply_filters(self, operations: list[OperationRecord]):
        """Apply filters to operations"""
        self.table_model.all_operations = operations
        filtered = operations
        if self._filter_results is not None:
            selected_results = self._filter_results
            filtered = [
                op
                for op in filtered
                if (
                    ("Sucesso" in selected_results and op.success)
                    or (
                        "Falha" in selected_results
                        and not op.success
                        and op.metadata.get("result") != "cancelled"
                    )
                    or (
                        "Cancelado" in selected_results and op.metadata.get("result") == "cancelled"
                    )
                    or (
                        "Criação desfeita" in selected_results
                        and creation_was_undone(op, operations)
                    )
                )
            ]
        # Filter by type
        if self._filter_types is not None:
            filtered = [op for op in filtered if op.operation_type in self._filter_types]

        # Filter by date
        if self._filter_date_range is not None:
            now = datetime.now()
            date_limits = {
                "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
                "week": now - timedelta(days=7),
                "month": now - timedelta(days=30),
                "year": now - timedelta(days=365),
            }
            filtered = [
                op for op in filtered if op.timestamp >= date_limits[self._filter_date_range]
            ]

        filtered = self._sort_operations(filtered)

        # Update model
        self.table_model.set_operations(filtered)
        self.total_label.setText(f"Total: {len(filtered)} de {len(operations)} operações")

    def _sort_operations(self, operations: list[OperationRecord]) -> list[OperationRecord]:
        def sort_key(operation: OperationRecord):
            if self._sort_column == 0:
                return operation.timestamp
            if self._sort_column == 1:
                return self.table_model._get_type_display(operation).casefold()
            if self._sort_column == 2:
                return str(operation.target or operation.source or "").casefold()
            if self._sort_column == 3:
                return self.table_model._get_display_data(operation, 3).casefold()
            undone = creation_was_undone(operation, self.table_model.all_operations)
            recoverable = (
                operation.success
                and operation.operation_type
                in (
                    OperationType.CREATE_JUNCTION,
                    OperationType.CREATE_SYMLINK,
                    OperationType.CREATE_HARDLINK,
                )
                and not undone
            )
            return (0 if recoverable else 1 if undone else 2, operation.timestamp)

        return sorted(operations, key=sort_key, reverse=not self._sort_ascending)

    def clear_filters(self):
        """Clear all filters"""
        self._filter_types = None
        self._filter_date_range = None
        self._filter_results = None
        self.load_history()

    def clear_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Tem certeza que deseja limpar todo o histórico de operações?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if not self.history_manager.clear_history():
                QMessageBox.critical(self, "Erro", "Não foi possível limpar o histórico.")
                return
            self.load_history()
            QMessageBox.information(self, "Sucesso", "Histórico limpo com sucesso.")

    def export_history(self):
        """Export history to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Histórico", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                operations = self.history_manager.get_history()
                import json

                data = [op.model_dump() for op in operations]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "Sucesso", "Histórico exportado com sucesso.")
            except Exception as e:
                self.logger.error(f"Error exporting history: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao exportar histórico: {e}")
