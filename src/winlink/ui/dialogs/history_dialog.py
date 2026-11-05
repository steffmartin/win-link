"""Dialog for displaying operation history"""

from datetime import datetime, timedelta

from PyQt6.QtCore import QAbstractTableModel, QDate, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
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
            return self._get_type_display(operation.operation_type)
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
        tooltip = f"Tipo: {operation.operation_type.value}\n"
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

    def _get_type_display(self, operation_type: OperationType) -> str:
        """Get display text for operation type"""
        type_names = {
            OperationType.CREATE_JUNCTION: "Criar Junção",
            OperationType.CREATE_SYMLINK: "Criar Symlink",
            OperationType.CREATE_HARDLINK: "Criar HardLink",
            OperationType.REMOVE_JUNCTION: "Remover Junção",
            OperationType.UNDO_OPERATION: "Desfazer",
            OperationType.MOVE_FILES: "Mover Arquivos",
            OperationType.COPY_FILES: "Copiar Arquivos",
        }
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

        self._filter_type: OperationType | None = None
        self._filter_date_range: str | None = None

        self.init_ui()
        self.load_history()

    def init_ui(self):
        from winlink.ui.components import FieldGrid, Panel, button_style, heading

        self.setWindowTitle("Histórico de Operações")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        title = heading(layout, "Histórico de Operações")
        self.export_btn = button_style(QPushButton("Exportar"), "download")
        self.export_btn.clicked.connect(self.export_history)
        self.clear_history_btn = button_style(QPushButton("Limpar"), "trash")
        self.clear_history_btn.clicked.connect(self.clear_history)
        title.addWidget(self.export_btn)
        title.addWidget(self.clear_history_btn)
        note = QLabel(
            'Registro de criações e reversões. Use "Desfazer" para reverter a criação selecionada.'
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        layout.addWidget(note)
        self.type_combo = QComboBox()
        self.type_combo.addItem("Todas")
        for op in OperationType:
            self.type_combo.addItem(HistoryTableModel()._get_type_display(op), op)
        self.type_combo.currentTextChanged.connect(self.on_filter_changed)
        self.date_combo = QComboBox()
        self.date_combo.addItems(["Todos", "Hoje", "Última semana", "Último mês", "Personalizado"])
        self.date_combo.currentTextChanged.connect(self.on_filter_changed)
        self.result_combo = QComboBox()
        self.result_combo.addItems(
            ["Todos os resultados", "Sucesso", "Falha", "Cancelado", "Criação desfeita"]
        )
        self.result_combo.setAccessibleName("Resultado")
        self.result_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.from_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.to_date = QDateEdit(QDate.currentDate())
        for name, control in [("De", self.from_date), ("Até", self.to_date)]:
            control.setCalendarPopup(True)
            control.setDisplayFormat("dd/MM/yyyy")
            control.setAccessibleName(name)
            control.dateChanged.connect(self.on_filter_changed)
        panel = Panel()
        panel.content.setContentsMargins(16, 16, 16, 16)
        panel.content.addWidget(QLabel("Filtrar histórico"))
        self.clear_filter_btn = button_style(QPushButton("Limpar filtros"), "filter")
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        panel.content.addWidget(
            FieldGrid(
                [
                    ("Operação", self.type_combo),
                    ("Período", self.date_combo),
                    ("Resultado", self.result_combo),
                    ("De", self.from_date),
                    ("Até", self.to_date),
                    ("", self.clear_filter_btn),
                ]
            )
        )
        layout.addWidget(panel)
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
        self.table_view.horizontalHeader().setStretchLastSection(True)
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

    def on_filter_changed(self):
        """Handle filter change"""
        type_text = self.type_combo.currentData()
        date_text = self.date_combo.currentText()

        # Parse type filter
        if type_text is None:
            self._filter_type = None
        else:
            try:
                self._filter_type = OperationType(type_text)
            except ValueError:
                self._filter_type = None

        # Parse date filter
        self._filter_date_range = date_text if date_text != "Todos" else None

        # Reload with filters
        self.load_history()

    def apply_filters(self, operations: list[OperationRecord]):
        """Apply filters to operations"""
        self.table_model.all_operations = operations
        filtered = operations
        result = self.result_combo.currentText()
        if result == "Sucesso":
            filtered = [op for op in filtered if op.success]
        elif result == "Falha":
            filtered = [
                op for op in filtered if not op.success and op.metadata.get("result") != "cancelled"
            ]
        elif result == "Cancelado":
            filtered = [op for op in filtered if op.metadata.get("result") == "cancelled"]
        elif result == "Criação desfeita":
            filtered = [op for op in filtered if creation_was_undone(op, operations)]
        custom = self._filter_date_range == "Personalizado"
        self.from_date.setEnabled(custom)
        self.to_date.setEnabled(custom)
        if custom:
            start, end = self.from_date.date().toPyDate(), self.to_date.date().toPyDate()
            filtered = [op for op in filtered if start <= op.timestamp.date() <= end]

        # Filter by type
        if self._filter_type:
            filtered = [op for op in filtered if op.operation_type == self._filter_type]

        # Filter by date
        if self._filter_date_range:
            now = datetime.now()
            if self._filter_date_range == "Hoje":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered = [op for op in filtered if op.timestamp >= start_date]
            elif self._filter_date_range == "Última semana":
                start_date = now - timedelta(days=7)
                filtered = [op for op in filtered if op.timestamp >= start_date]
            elif self._filter_date_range == "Último mês":
                start_date = now - timedelta(days=30)
                filtered = [op for op in filtered if op.timestamp >= start_date]

        # Update model
        self.table_model.set_operations(filtered)
        self.total_label.setText(f"Total: {len(filtered)} de {len(operations)} operações")

    def clear_filters(self):
        """Clear all filters"""
        self.type_combo.setCurrentText("Todas")
        self.date_combo.setCurrentText("Todos")
        self.result_combo.setCurrentIndex(0)

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
