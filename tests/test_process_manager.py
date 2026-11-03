"""Tests for process manager"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from winlink.core.process_manager import (
    get_friendly_process_name,
    get_known_blocking_processes,
    get_process_info,
    get_processes_using_directory,
    get_processes_using_file,
    is_process_running,
    suggest_processes_to_close,
    suggest_processes_to_close_for_directory,
    terminate_process,
    terminate_processes,
)


def test_get_known_blocking_processes():
    """Test getting known blocking processes"""
    processes = get_known_blocking_processes()
    assert isinstance(processes, dict)
    assert "code.exe" in processes
    assert processes["code.exe"] == "Visual Studio Code"


def test_get_friendly_process_name_known():
    """Test getting friendly name for known process"""
    name = get_friendly_process_name("code.exe")
    assert name == "Visual Studio Code"


def test_get_friendly_process_name_unknown():
    """Test getting friendly name for unknown process"""
    name = get_friendly_process_name("unknown.exe")
    assert name == "unknown.exe"


def test_get_processes_using_file_empty():
    """Test getting processes using file when none"""
    with patch("winlink.core.process_manager.psutil.process_iter") as mock_iter:
        mock_iter.return_value = []

        processes = get_processes_using_file(Path("C:/test/file.txt"))
        assert processes == []


def test_get_processes_using_file_with_processes():
    """Test getting processes using file with processes"""
    with patch("winlink.core.process_manager.psutil.process_iter") as mock_iter:
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 1234, "name": "test.exe", "exe": "C:/test.exe"}
        mock_proc.open_files.return_value = [MagicMock(path="C:/test/file.txt")]

        mock_iter.return_value = [mock_proc]

        processes = get_processes_using_file(Path("C:/test/file.txt"))
        assert len(processes) == 1
        assert processes[0]["pid"] == 1234
        assert processes[0]["name"] == "test.exe"


def test_get_processes_using_directory_empty():
    """Test getting processes using directory when none"""
    with patch("winlink.core.process_manager.psutil.process_iter") as mock_iter:
        mock_iter.return_value = []

        processes = get_processes_using_directory(Path("C:/test/dir"))
        assert processes == []


def test_get_processes_using_directory_with_processes():
    """Test getting processes using directory with processes"""
    with patch("winlink.core.process_manager.psutil.process_iter") as mock_iter, patch(
        "pathlib.Path.is_relative_to"
    ) as mock_is_relative:
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 1234, "name": "test.exe", "exe": "C:/test.exe"}
        mock_proc.open_files.return_value = [MagicMock(path="C:/test/dir/file.txt")]

        mock_iter.return_value = [mock_proc]
        mock_is_relative.return_value = True

        processes = get_processes_using_directory(Path("C:/test/dir"))
        assert len(processes) == 1
        assert processes[0]["pid"] == 1234


def test_terminate_process_success():
    """Test successfully terminating a process"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        mock_proc = MagicMock()
        mock_process_class.return_value = mock_proc

        result = terminate_process(1234)
        assert result is True
        mock_proc.terminate.assert_called_once()


def test_terminate_process_force():
    """Test force terminating a process"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        mock_proc = MagicMock()
        mock_process_class.return_value = mock_proc

        result = terminate_process(1234, force=True)
        assert result is True
        mock_proc.kill.assert_called_once()


def test_terminate_process_not_exists():
    """Test terminating non-existent process"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        from psutil import NoSuchProcess

        mock_process_class.side_effect = NoSuchProcess(1234)

        result = terminate_process(1234)
        assert result is False


def test_terminate_process_access_denied():
    """Test terminating process with access denied"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        from psutil import AccessDenied

        mock_proc = MagicMock()
        mock_process_class.return_value = mock_proc
        mock_proc.terminate.side_effect = AccessDenied(1234)

        result = terminate_process(1234)
        assert result is False


def test_terminate_processes():
    """Test terminating multiple processes"""
    with patch("winlink.core.process_manager.terminate_process") as mock_terminate:
        mock_terminate.return_value = True

        processes = [{"pid": 1234}, {"pid": 5678}]
        result = terminate_processes(processes)
        assert result == 2
        assert mock_terminate.call_count == 2


def test_is_process_running_true():
    """Test checking if process is running"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = True
        mock_process_class.return_value = mock_proc

        result = is_process_running(1234)
        assert result is True


def test_is_process_running_false():
    """Test checking if process is not running"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        from psutil import NoSuchProcess

        mock_process_class.side_effect = NoSuchProcess(1234)

        result = is_process_running(1234)
        assert result is False


def test_get_process_info_success():
    """Test getting process info successfully"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.name.return_value = "test.exe"
        mock_proc.exe.return_value = "C:/test.exe"
        mock_proc.cwd.return_value = "C:/test"
        mock_proc.cmdline.return_value = ["test.exe"]
        mock_process_class.return_value = mock_proc

        info = get_process_info(1234)
        assert info is not None
        assert info["pid"] == 1234
        assert info["name"] == "test.exe"


def test_get_process_info_not_exists():
    """Test getting process info for non-existent process"""
    with patch("winlink.core.process_manager.psutil.Process") as mock_process_class:
        from psutil import NoSuchProcess

        mock_process_class.side_effect = NoSuchProcess(1234)

        info = get_process_info(1234)
        assert info is None


def test_suggest_processes_to_close():
    """Test suggesting processes to close for a file"""
    with patch("winlink.core.process_manager.get_processes_using_file") as mock_get:
        mock_get.return_value = [{"name": "code.exe"}, {"name": "unknown.exe"}]

        suggestions = suggest_processes_to_close(Path("C:/test/file.txt"))
        assert len(suggestions) == 2
        assert "Visual Studio Code" in suggestions
        assert "unknown.exe" in suggestions


def test_suggest_processes_to_close_for_directory():
    """Test suggesting processes to close for a directory"""
    with patch("winlink.core.process_manager.get_processes_using_directory") as mock_get:
        mock_get.return_value = [{"name": "explorer.exe"}]

        suggestions = suggest_processes_to_close_for_directory(Path("C:/test/dir"))
        assert len(suggestions) == 1
        assert "Windows Explorer" in suggestions
