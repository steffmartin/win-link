"""Non-blocking release notification and update dialog."""

import threading
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton, QVBoxLayout

from winlink import __version__
from winlink.core import updater
from winlink.ui.components import button_style
from winlink.ui.dialogs.animated_dialog import AnimatedDialog
from winlink.utils.logger import get_logger


class _Signals(QObject):
    checked = pyqtSignal(object)
    progress = pyqtSignal(int, int)
    ready = pyqtSignal(object)
    failed = pyqtSignal()


def _emit(signal, *args):
    try:
        signal.emit(*args)
    except RuntimeError:
        # The window may have closed while a network operation was in progress.
        pass


class UpdateDialog(AnimatedDialog):
    def __init__(self, info: updater.UpdateInfo, parent, root: Path | None = None):
        super().__init__(parent)
        self.info = info
        self.root = root
        self._working = False
        self._signals = _Signals(self)
        self._signals.progress.connect(self._on_progress)
        self._signals.ready.connect(self._on_ready)
        self._signals.failed.connect(self._on_failed)
        self.setWindowTitle("Nova versão disponível")
        self.setModal(True)
        self.preferred_width = 540
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        title = QLabel("Nova versão disponível")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(f"A versão {info.version} está disponível para download.")
        description.setWordWrap(True)
        layout.addWidget(description)
        notes = QLabel(f'<a href="{info.release_url}">O que mudou?</a>')
        notes.setOpenExternalLinks(True)
        notes.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        notes.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        notes.setAccessibleName("Abrir a página da nova versão")
        layout.addWidget(notes)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        self.install = button_style(QPushButton("Instalar"), primary=True)
        self.install.clicked.connect(self._start_download)
        self.ignore = button_style(QPushButton("Ignorar esta versão"))
        self.ignore.clicked.connect(self._ignore)
        self.later = button_style(QPushButton("Agora não"))
        self.later.clicked.connect(self.reject)
        # A vertical stack remains reachable in a small window and at high DPI.
        layout.addWidget(self.install)
        layout.addWidget(self.ignore)
        layout.addWidget(self.later)
        if root is None or not info.installer_url or not info.checksum_url:
            self.install.setEnabled(False)
            self.status.setText(
                "Instalação automática indisponível nesta cópia. Consulte a página da versão."
            )

    def _ignore(self):
        try:
            updater.ignore_version(self.info.version)
        except OSError:
            self.status.setText("Não foi possível salvar a versão ignorada. Tente novamente.")
            return
        self.reject()

    def _set_working(self, working: bool):
        self._working = working
        self.install.setEnabled(not working)
        self.ignore.setEnabled(not working)
        self.later.setEnabled(not working)

    def _start_download(self):
        if self._working or self.root is None:
            return
        self._set_working(True)
        self.progress.setRange(0, 0)
        self.progress.show()
        self.status.setText("Preparando download…")

        def run():
            try:
                path = updater.download_update(
                    self.info,
                    lambda received, total: _emit(self._signals.progress, received, total),
                )
                _emit(self._signals.ready, path)
            except Exception:
                _emit(self._signals.failed)

        threading.Thread(target=run, daemon=True, name="winlink-update-download").start()

    def _on_progress(self, received: int, total: int):
        if total:
            percent = min(100, received * 100 // total)
            self.progress.setRange(0, 100)
            self.progress.setValue(percent)
            self.status.setText(f"Baixando atualização… {percent}%")
        else:
            self.status.setText(f"Baixando atualização… {received / 1048576:.1f} MB")

    def _on_ready(self, installer: Path):
        try:
            parent = self.parent()
            if self.root is None or getattr(parent, "_operation_active", False):
                raise RuntimeError("Operação em andamento")
            updater.launch_helper(installer, self.root)
        except Exception:
            updater.discard_download(installer)
            self._on_failed()
            return
        self._working = False
        self.accept()
        parent.close()

    def _on_failed(self):
        self._set_working(False)
        self.progress.hide()
        self.status.setText(
            "Não foi possível baixar, verificar ou iniciar a atualização. Tente novamente."
        )

    def reject(self):
        if not self._working:
            super().reject()

    def closeEvent(self, event):
        if self._working:
            event.ignore()
        else:
            super().closeEvent(event)


class UpdateController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._signals = _Signals(self)
        self._signals.checked.connect(self._checked)
        self._pending = None
        self.dialog = None

    def start(self):
        def run():
            try:
                info = updater.check_update(__version__)
            except Exception as exc:
                get_logger(__name__).debug("Verificação de atualização indisponível: %s", exc)
                info = None
            _emit(self._signals.checked, info)

        threading.Thread(target=run, daemon=True, name="winlink-update-check").start()

    def _checked(self, info):
        if info is None or not self.window.isVisible():
            return
        self._pending = info
        self._show_when_ready()

    def _show_when_ready(self):
        if not self.window.isVisible() or self._pending is None:
            return
        if self.window._operation_active or QApplication.activeModalWidget() is not None:
            QTimer.singleShot(500, self._show_when_ready)
            return
        self.dialog = UpdateDialog(self._pending, self.window, updater.installed_root())
        self._pending = None
        self.dialog.open()
