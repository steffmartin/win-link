"""Process management for handling files in use"""

from pathlib import Path

import psutil

from winlink.utils.logger import get_logger

logger = get_logger(__name__)

# Known processes that commonly block files
KNOWN_BLOCKING_PROCESSES = {
    "code.exe": "Visual Studio Code",
    "Code.exe": "Visual Studio Code",
    "explorer.exe": "Windows Explorer",
    "chrome.exe": "Google Chrome",
    "firefox.exe": "Mozilla Firefox",
    "msedge.exe": "Microsoft Edge",
    "docker.exe": "Docker Desktop",
    "docker-desktop.exe": "Docker Desktop",
    "git.exe": "Git",
    "bash.exe": "Git Bash",
    "python.exe": "Python",
    "pythonw.exe": "Python (GUI)",
    "notepad.exe": "Notepad",
    "notepad++.exe": "Notepad++",
    "sublime_text.exe": "Sublime Text",
    "idea64.exe": "IntelliJ IDEA",
    "devenv.exe": "Visual Studio",
}


def get_processes_using_file(file_path: Path) -> list[dict]:
    """
    Get list of processes that are using a specific file.

    Args:
        file_path: Path to file

    Returns:
        List of process information dictionaries
    """
    processes = []

    try:
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                # Get all open files for the process
                open_files = proc.open_files()
                for open_file in open_files:
                    if Path(open_file.path) == file_path:
                        processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "exe": proc.info["exe"],
                            }
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Error getting processes using file {file_path}: {e}")

    return processes


def get_processes_using_directory(directory: Path) -> list[dict]:
    """
    Get list of processes that are using files in a directory.

    Args:
        directory: Path to directory

    Returns:
        List of process information dictionaries
    """
    processes = []

    try:
        directory_str = str(directory).lower()

        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                # Get all open files for the process
                open_files = proc.open_files()
                for open_file in open_files:
                    file_path = Path(open_file.path)
                    # Check if file is in the directory
                    try:
                        if file_path.is_relative_to(directory):
                            processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "exe": proc.info["exe"],
                                }
                            )
                            break  # Add process only once
                    except ValueError:
                        # is_relative_to may raise ValueError on different drives
                        continue
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Error getting processes using directory {directory}: {e}")

    return processes


def get_known_blocking_processes() -> dict[str, str]:
    """
    Get dictionary of known blocking processes.

    Returns:
        Dictionary mapping process names to friendly names
    """
    return KNOWN_BLOCKING_PROCESSES.copy()


def get_friendly_process_name(process_name: str) -> str:
    """
    Get friendly name for a process.

    Args:
        process_name: Process executable name

    Returns:
        Friendly name or original name if not known
    """
    return KNOWN_BLOCKING_PROCESSES.get(process_name, process_name)


def terminate_process(pid: int, force: bool = False) -> bool:
    """
    Terminate a process by PID.

    Args:
        pid: Process ID
        force: If True, force kill the process

    Returns:
        True if successful, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        if force:
            proc.kill()
        else:
            proc.terminate()
        logger.info(f"Terminated process {pid}")
        return True
    except psutil.NoSuchProcess:
        logger.warning(f"Process {pid} does not exist")
        return False
    except psutil.AccessDenied:
        logger.error(f"Access denied when trying to terminate process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {e}")
        return False


def terminate_processes(processes: list[dict], force: bool = False) -> int:
    """
    Terminate multiple processes.

    Args:
        processes: List of process dictionaries
        force: If True, force kill processes

    Returns:
        Number of processes successfully terminated
    """
    terminated = 0
    for proc_info in processes:
        pid = proc_info["pid"]
        if terminate_process(pid, force):
            terminated += 1
    return terminated


def is_process_running(pid: int) -> bool:
    """
    Check if a process is running.

    Args:
        pid: Process ID

    Returns:
        True if running, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        return proc.is_running()
    except psutil.NoSuchProcess:
        return False
    except Exception:
        return False


def get_process_info(pid: int) -> dict | None:
    """
    Get information about a process.

    Args:
        pid: Process ID

    Returns:
        Process information dictionary or None
    """
    try:
        proc = psutil.Process(pid)
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "exe": proc.exe(),
            "cwd": proc.cwd(),
            "cmdline": proc.cmdline(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None
    except Exception as e:
        logger.error(f"Error getting process info for {pid}: {e}")
        return None


def suggest_processes_to_close(file_path: Path) -> list[str]:
    """
    Suggest processes to close for a given file.

    Args:
        file_path: Path to file

    Returns:
        List of friendly process names
    """
    processes = get_processes_using_file(file_path)
    suggestions = []

    for proc_info in processes:
        name = proc_info.get("name", "")
        friendly_name = get_friendly_process_name(name)
        suggestions.append(friendly_name)

    return suggestions


def suggest_processes_to_close_for_directory(directory: Path) -> list[str]:
    """
    Suggest processes to close for a given directory.

    Args:
        directory: Path to directory

    Returns:
        List of friendly process names
    """
    processes = get_processes_using_directory(directory)
    suggestions = []

    for proc_info in processes:
        name = proc_info.get("name", "")
        friendly_name = get_friendly_process_name(name)
        suggestions.append(friendly_name)

    return suggestions
