"""Scanner for junctions and symbolic links"""

import os
import time
from pathlib import Path
from typing import Optional

import win32api
import win32con
import win32file
import winioctlcon
import winnt

from winlink.core.models import Creator, Junction, JunctionStatus, JunctionType, ScanResult
from winlink.utils.logger import get_logger

logger = get_logger(__name__)


def is_reparse_point(path: Path) -> bool:
    """
    Check if a path is a reparse point (junction or symlink).

    Args:
        path: Path to check

    Returns:
        True if path is a reparse point, False otherwise
    """
    try:
        attrs = win32api.GetFileAttributes(str(path))
        return bool(attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception as e:
        logger.warning(f"Failed to check reparse point for {path}: {e}")
        return False


def get_reparse_target(path: Path) -> Optional[Path]:
    """
    Get the target of a reparse point.

    Args:
        path: Path to the reparse point

    Returns:
        Target path if successful, None otherwise
    """
    # First try Python's os.readlink (works for symlinks and junctions)
    try:
        import os

        target_str = os.readlink(path)
        # Remove \\?\ prefix if present
        if target_str.startswith("\\\\?\\"):
            target_str = target_str[4:]
        return Path(target_str)
    except (OSError, NotImplementedError, AttributeError):
        pass

    # Fallback to Windows API
    try:
        handle = win32file.CreateFileW(
            str(path),
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )

        try:
            buffer_size = winnt.MAXIMUM_REPARSE_DATA_BUFFER_SIZE
            buffer = win32file.DeviceIoControl(
                handle,
                winioctlcon.FSCTL_GET_REPARSE_POINT,
                None,
                buffer_size,
            )

            # Parse the reparse data buffer
            if len(buffer) < 8:
                return None

            reparse_tag = int.from_bytes(buffer[0:4], byteorder="little")

            # Junction tag
            if reparse_tag == winnt.IO_REPARSE_TAG_MOUNT_POINT:
                # Mount point (junction)
                offset = int.from_bytes(buffer[8:12], byteorder="little")
                length = int.from_bytes(buffer[12:16], byteorder="little")
                target_bytes = buffer[offset : offset + length]
                target = target_bytes.decode("utf-16le").rstrip("\x00")
                # Remove leading \??\
                if target.startswith("\\??\\"):
                    target = target[4:]
                return Path(target)

            # Symlink tag
            elif reparse_tag == winnt.IO_REPARSE_TAG_SYMBOLIC_LINK:
                # Symbolic link
                offset = int.from_bytes(buffer[16:20], byteorder="little")
                length = int.from_bytes(buffer[20:24], byteorder="little")
                target_bytes = buffer[offset : offset + length]
                target = target_bytes.decode("utf-16le").rstrip("\x00")
                # Remove leading \??\
                if target.startswith("\\??\\"):
                    target = target[4:]
                return Path(target)

        finally:
            win32file.CloseHandle(handle)

    except Exception as e:
        logger.warning(f"Failed to get reparse target for {path}: {e}")
        return None

    return None


def get_junction_type(path: Path) -> Optional[JunctionType]:
    """
    Determine the type of junction/link.

    Args:
        path: Path to check

    Returns:
        JunctionType if identified, None otherwise
    """
    # Try Windows API first
    try:
        handle = win32file.CreateFileW(
            str(path),
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )

        try:
            buffer_size = winnt.MAXIMUM_REPARSE_DATA_BUFFER_SIZE
            buffer = win32file.DeviceIoControl(
                handle,
                winioctlcon.FSCTL_GET_REPARSE_POINT,
                None,
                buffer_size,
            )

            if len(buffer) < 8:
                return None

            reparse_tag = int.from_bytes(buffer[0:4], byteorder="little")

            if reparse_tag == winnt.IO_REPARSE_TAG_MOUNT_POINT:
                return JunctionType.JUNCTION
            elif reparse_tag == winnt.IO_REPARSE_TAG_SYMBOLIC_LINK:
                return JunctionType.SYMLINK

        finally:
            win32file.CloseHandle(handle)

    except Exception as e:
        logger.debug(f"Windows API failed for {path}: {e}")

    # Fallback: Use Python's os.readlink and infer type
    try:
        import os

        target = os.readlink(path)
        # If we can read it with os.readlink, it's likely a symlink
        # NTFS junctions are also readable via os.readlink on modern Windows
        # We can differentiate by checking if it's a directory vs file
        if path.is_dir():
            return JunctionType.JUNCTION
        else:
            return JunctionType.SYMLINK
    except (OSError, NotImplementedError, AttributeError):
        pass

    return None


def calculate_directory_size(path: Path) -> int:
    """
    Calculate total size of a directory recursively.

    Args:
        path: Path to directory

    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                try:
                    total_size += filepath.stat().st_size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError) as e:
        logger.warning(f"Error calculating size for {path}: {e}")

    return total_size


def check_junction_status(junction: Junction) -> JunctionStatus:
    """
    Check the status of a junction.

    Args:
        junction: Junction to check

    Returns:
        JunctionStatus
    """
    # Check if target exists
    if not junction.target.exists():
        return JunctionStatus.BROKEN

    # Check if source exists
    if not junction.source.exists():
        return JunctionStatus.BROKEN

    # Check if accessible
    try:
        # Try to access the target
        if junction.is_directory:
            list(junction.target.iterdir())
        else:
            junction.target.read_bytes()
    except (PermissionError, OSError):
        return JunctionStatus.INACCESSIBLE

    return JunctionStatus.ACTIVE


def classify_creator(junction: Junction, known_junctions: set[Path]) -> Creator:
    """
    Classify who created the junction based on history.

    Args:
        junction: Junction to classify
        known_junctions: Set of junction paths known to be created by the app

    Returns:
        Creator classification
    """
    if junction.target in known_junctions:
        return Creator.APP
    return Creator.EXISTING


def scan_directory(
    path: Path,
    recursive: bool = True,
    known_junctions: Optional[set[Path]] = None,
) -> list[Junction]:
    """
    Scan a directory for junctions and symlinks.

    Args:
        path: Directory to scan
        recursive: Whether to scan recursively
        known_junctions: Set of junction paths known to be created by the app

    Returns:
        List of found junctions
    """
    if known_junctions is None:
        known_junctions = set()

    junctions = []

    if not path.exists() or not path.is_dir():
        logger.warning(f"Path does not exist or is not a directory: {path}")
        return junctions

    try:
        # Walk through directory
        for item in path.iterdir():
            try:
                if is_reparse_point(item):
                    # Get junction type
                    junction_type = get_junction_type(item)
                    if junction_type is None:
                        continue

                    # Get target
                    target = get_reparse_target(item)
                    if target is None:
                        continue

                    # Determine if it's a directory
                    is_directory = item.is_dir()

                    # Create junction object
                    junction = Junction(
                        source=target,
                        target=item,
                        junction_type=junction_type,
                        is_directory=is_directory,
                    )

                    # Check status
                    junction.status = check_junction_status(junction)

                    # Classify creator
                    junction.creator = classify_creator(junction, known_junctions)

                    # Calculate size if active
                    if junction.status == JunctionStatus.ACTIVE and junction.source.exists():
                        if junction.is_directory:
                            junction.size_bytes = calculate_directory_size(junction.source)
                        else:
                            try:
                                junction.size_bytes = junction.source.stat().st_size
                            except (OSError, PermissionError):
                                pass

                    junctions.append(junction)
                    logger.info(f"Found junction: {item} -> {target}")

                # Recursively scan subdirectories
                elif recursive and item.is_dir():
                    try:
                        junctions.extend(scan_directory(item, recursive, known_junctions))
                    except Exception as e:
                        logger.warning(f"Error scanning subdirectory {item}: {e}")
                        continue

            except (PermissionError, OSError) as e:
                logger.warning(f"Permission error accessing {item}: {e}")
                continue

    except (PermissionError, OSError) as e:
        logger.error(f"Error scanning directory {path}: {e}")

    return junctions


def scan_directories(
    directories: list[Path],
    recursive: bool = True,
    known_junctions: Optional[set[Path]] = None,
) -> ScanResult:
    """
    Scan multiple directories for junctions.

    Args:
        directories: List of directories to scan
        recursive: Whether to scan recursively
        known_junctions: Set of junction paths known to be created by the app

    Returns:
        ScanResult with found junctions and metadata
    """
    start_time = time.time()
    all_junctions = []
    scanned_dirs = []
    errors = []

    if known_junctions is None:
        known_junctions = set()

    for directory in directories:
        logger.info(f"Scanning directory: {directory}")
        try:
            junctions = scan_directory(directory, recursive, known_junctions)
            all_junctions.extend(junctions)
            scanned_dirs.append(directory)
        except Exception as e:
            error_msg = f"Error scanning {directory}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    duration = time.time() - start_time

    result = ScanResult(
        junctions=all_junctions,
        scanned_directories=scanned_dirs,
        scan_duration_seconds=duration,
        errors=errors,
    )

    logger.info(f"Scan complete: found {len(all_junctions)} junctions in {duration:.2f}s")

    return result
