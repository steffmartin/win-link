"""Background execution with cooperative cancellation and Qt signals."""

from collections.abc import Callable
from threading import Event

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class OperationCancelledError(Exception):
    """Raised at a safe cancellation boundary."""


class OperationWorker(QThread):
    """Run filesystem work without accessing widgets from the worker thread."""

    progress = pyqtSignal(int, str)
    completed = pyqtSignal(bool, str)

    def __init__(self, operation: Callable, parent=None):
        super().__init__(parent)
        self.operation = operation
        self._cancel = Event()

    def cancel(self):
        self._cancel.set()

    def check_cancelled(self):
        if self._cancel.is_set():
            raise OperationCancelledError("Operação cancelada")

    def report(self, value: int, message: str):
        self.progress.emit(value, message)

    def run(self):
        try:
            self.check_cancelled()
            self.operation(self)
        except Exception as exc:
            self.completed.emit(False, str(exc))
        else:
            self.completed.emit(True, "")


def run_operation(operation, progress):
    """Wait for background work through a Qt loop that keeps the UI responsive."""
    from PyQt6.QtCore import QEventLoop

    loop = QEventLoop()
    outcome: list[bool | str] = []
    worker = OperationWorker(operation)
    worker.progress.connect(progress.update_progress)
    progress.cancellation_requested.connect(worker.cancel)

    def completed(success, message):
        outcome.extend((success, message))
        loop.quit()

    worker.completed.connect(completed)
    worker.start()
    loop.exec()
    worker.wait()
    progress.cancellation_requested.disconnect(worker.cancel)
    if not outcome[0]:
        raise OSError(outcome[1])


class QuietProgress(QObject):
    """Signal sink for background checks that do not mutate user files."""

    cancellation_requested = pyqtSignal()

    def update_progress(self, value, message):
        pass


def evaluate_in_background(callback):
    result = []
    run_operation(lambda context: result.append(callback()), QuietProgress())
    return result[0]
