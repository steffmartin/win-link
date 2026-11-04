"""Behavior of background operations and cancellation boundaries."""

from winlink.ui.operation_worker import OperationWorker


def test_worker_runs_and_reports_progress(qtbot):
    values = []
    worker = OperationWorker(lambda context: context.report(50, "copying"))
    worker.progress.connect(lambda value, message: values.append((value, message)))
    with qtbot.waitSignal(worker.completed) as signal:
        worker.start()
    worker.wait()
    assert signal.args == [True, ""]
    assert values == [(50, "copying")]


def test_worker_cancelled_before_start_does_not_execute(qtbot):
    calls = []
    worker = OperationWorker(lambda context: calls.append(True))
    worker.cancel()
    with qtbot.waitSignal(worker.completed) as signal:
        worker.start()
    worker.wait()
    assert signal.args == [False, "Operação cancelada"]
    assert calls == []


def test_worker_reports_exception(qtbot):
    def fail(context):
        raise OSError("copy failed")

    worker = OperationWorker(fail)
    with qtbot.waitSignal(worker.completed) as signal:
        worker.start()
    worker.wait()
    assert signal.args == [False, "copy failed"]


def test_background_wait_keeps_qt_responsive(qtbot):
    from threading import Event
    from PyQt6.QtCore import QTimer
    from winlink.ui.operation_worker import run_operation
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    progress = ProgressDialog()
    qtbot.addWidget(progress)
    released = Event()
    ticks = []

    def release():
        ticks.append(True)
        released.set()

    QTimer.singleShot(20, release)

    def operation(context):
        if not released.wait(2):
            raise RuntimeError("Qt event loop did not respond")

    run_operation(operation, progress)
    assert ticks == [True]


def test_background_wait_delivers_cancellation(qtbot):
    import pytest
    from threading import Event
    from PyQt6.QtCore import QTimer
    from winlink.ui.operation_worker import run_operation
    from winlink.ui.dialogs.progress_dialog import ProgressDialog

    progress = ProgressDialog()
    qtbot.addWidget(progress)
    released = Event()

    def cancel():
        progress.cancel_operation()
        released.set()

    QTimer.singleShot(20, cancel)

    def operation(context):
        assert released.wait(2)
        context.check_cancelled()

    with pytest.raises(OSError, match="cancelada"):
        run_operation(operation, progress)
