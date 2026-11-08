"""Dialog for undoing a junction"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from winlink.core.models import UndoStrategy
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class UndoDialog(AnimatedDialog):
    """Dialog for undoing a junction"""

    def __init__(self, source: Path, target: Path, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.source = source
        self.target = target

        self._strategy = UndoStrategy.MOVE_BACK
        self._keep_source = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Desfazer Junção")
        self.setMinimumWidth(600)
        self.setModal(True)

        from winlink.ui.components import button_style, heading

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        heading(
            layout,
            "Reverter Link",
            "Escolha a estratégia e confira os caminhos antes de confirmar.",
            icon="undo",
        )

        # Junction info
        info_label = QLabel("Link selecionado")
        layout.addWidget(info_label)

        junction_label = QLabel(f"Ponto de Acesso: {self.target}\nDados Físicos: {self.source}")
        junction_label.setWordWrap(True)
        junction_label.setObjectName("undoPaths")
        layout.addWidget(junction_label)

        # Strategy selection
        strategy_label = QLabel("Escolha o que fazer:")
        strategy_label.setObjectName("fieldLabel")
        layout.addWidget(strategy_label)

        self.strategy_group = QButtonGroup(self)

        # Remove only option
        self.remove_only_radio = QRadioButton("Remover apenas a junção")
        self.remove_only_radio.setToolTip(
            "O link será removido, deixando uma pasta vazia no Ponto de Acesso. Os arquivos permanecem nos Dados Físicos."
        )
        self.strategy_group.addButton(self.remove_only_radio, 0)
        layout.addWidget(self.remove_only_radio)

        remove_only_desc = QLabel(
            "O link será removido, deixando uma pasta vazia no Ponto de Acesso. Os arquivos permanecem nos Dados Físicos."
        )
        remove_only_desc.setWordWrap(True)
        remove_only_desc.setObjectName("strategyDescription")
        layout.addWidget(remove_only_desc)

        # Move back option
        self.move_back_radio = QRadioButton("Mover arquivos de volta")
        self.move_back_radio.setChecked(True)
        self.move_back_radio.setToolTip(
            "Os arquivos voltarão dos Dados Físicos para o Ponto de Acesso, substituindo o link por uma pasta normal. A opção de backup preserva os Dados Físicos."
        )
        self.strategy_group.addButton(self.move_back_radio, 1)
        layout.addWidget(self.move_back_radio)

        move_back_desc = QLabel(
            "Os arquivos voltarão dos Dados Físicos para o Ponto de Acesso, substituindo o link por uma pasta normal. A opção de backup preserva os Dados Físicos."
        )
        move_back_desc.setWordWrap(True)
        move_back_desc.setObjectName("strategyDescription")
        layout.addWidget(move_back_desc)

        # Duplicate option
        self.duplicate_radio = QRadioButton("Duplicar arquivos")
        self.duplicate_radio.setToolTip(
            "Os arquivos serão copiados dos Dados Físicos para o Ponto de Acesso, substituindo o link por uma pasta normal. Os Dados Físicos permanecem com os arquivos."
        )
        self.strategy_group.addButton(self.duplicate_radio, 2)
        layout.addWidget(self.duplicate_radio)

        duplicate_desc = QLabel(
            "Os arquivos serão copiados dos Dados Físicos para o Ponto de Acesso, substituindo o link por uma pasta normal. Os Dados Físicos permanecem com os arquivos."
        )
        duplicate_desc.setWordWrap(True)
        duplicate_desc.setObjectName("strategyDescription")
        layout.addWidget(duplicate_desc)

        # Keep source checkbox
        self.keep_source_checkbox = QCheckBox("Manter Dados Físicos como backup")
        self.keep_source_checkbox.setToolTip("Mantém os arquivos nos Dados Físicos como backup.")
        layout.addWidget(self.keep_source_checkbox)

        layout.addSpacing(12)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = button_style(QPushButton("Cancelar"), "close")
        self.cancel_btn.clicked.connect(self.reject)

        self.undo_btn = button_style(QPushButton("Executar Reversão"), "undo", primary=True)
        self.undo_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.undo_btn)

        layout.addLayout(button_layout)

        # Connect signals
        self.strategy_group.buttonClicked.connect(self.on_strategy_changed)

    def on_strategy_changed(self, button):
        """Handle strategy radio button change"""
        if button == self.remove_only_radio:
            self._strategy = UndoStrategy.REMOVE_ONLY
            self.keep_source_checkbox.setEnabled(False)
        elif button == self.move_back_radio:
            self._strategy = UndoStrategy.MOVE_BACK
            self.keep_source_checkbox.setEnabled(True)
        elif button == self.duplicate_radio:
            self._strategy = UndoStrategy.DUPLICATE
            self.keep_source_checkbox.setEnabled(True)

    def get_strategy(self) -> UndoStrategy:
        """Get selected undo strategy"""
        return self._strategy

    def get_keep_source(self) -> bool:
        """Get whether to keep source as backup"""
        return bool(self.keep_source_checkbox.isChecked())

    def accept(self):
        """Override accept to validate before closing"""
        strategy = self.get_strategy()

        # Validate strategy with keep_source
        if strategy == UndoStrategy.REMOVE_ONLY and self.keep_source_checkbox.isChecked():
            # Not applicable for remove_only
            self.keep_source_checkbox.setChecked(False)

        self.logger.info(
            f"Undoing junction {self.target} -> {self.source} with strategy {strategy}"
        )
        super().accept()
