"""Scanner for junctions and symbolic links"""

import os
import time
from pathlib import Path

import win32api
import win32con
import win32file
import winioctlcon
import winnt

from winlink.core.cache import CacheManager
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


def is_hard_link(path: Path) -> bool:
    """
    Check if a path is a hard link (has multiple hard link references).

    Args:
        path: Path to check

    Returns:
        True if path is a hard link (st_nlink > 1), False otherwise
    """
    try:
        stat = path.stat()
        return stat.st_nlink > 1
    except Exception as e:
        logger.warning(f"Failed to check hard link for {path}: {e}")
        return False


def get_reparse_target(path: Path) -> Path | None:
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
        if target_str.startswith("\\\\?\\UNC\\"):
            target_str = "\\\\" + target_str[8:]
        elif target_str.startswith("\\\\?\\"):
            target_str = target_str[4:]
        target = Path(target_str)
        return target if target.is_absolute() else path.parent / target
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
            if reparse_tag == (winnt.IO_REPARSE_TAG_MOUNT_POINT & 0xFFFFFFFF):
                # Mount point (junction)
                offset = int.from_bytes(buffer[8:10], byteorder="little")
                length = int.from_bytes(buffer[10:12], byteorder="little")
                if (
                    len(buffer) < 16
                    or not length
                    or offset % 2
                    or length % 2
                    or 16 + offset + length > len(buffer)
                ):
                    return None
                target_bytes = buffer[16 + offset : 16 + offset + length]
                target = target_bytes.decode("utf-16le").rstrip("\x00")
                # Remove leading \??\
                if target.startswith("\\??\\"):
                    target = target[4:]
                if target.startswith("UNC\\"):
                    target = "\\\\" + target[4:]
                return Path(target)

            # Symlink tag
            elif reparse_tag == 0xA000000C:
                # Symbolic link
                offset = int.from_bytes(buffer[8:10], byteorder="little")
                length = int.from_bytes(buffer[10:12], byteorder="little")
                if (
                    len(buffer) < 20
                    or not length
                    or offset % 2
                    or length % 2
                    or 20 + offset + length > len(buffer)
                ):
                    return None
                target_bytes = buffer[20 + offset : 20 + offset + length]
                target = target_bytes.decode("utf-16le").rstrip("\x00")
                # Remove leading \??\
                if target.startswith("\\??\\"):
                    target = target[4:]
                if target.startswith("UNC\\"):
                    target = "\\\\" + target[4:]
                resolved = Path(target)
                return resolved if resolved.is_absolute() else path.parent / resolved

        finally:
            win32file.CloseHandle(handle)

    except Exception as e:
        logger.warning(f"Failed to get reparse target for {path}: {e}")
        return None

    return None


def get_junction_type(path: Path) -> JunctionType | None:
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

            if reparse_tag == (winnt.IO_REPARSE_TAG_MOUNT_POINT & 0xFFFFFFFF):
                return JunctionType.JUNCTION
            elif reparse_tag == 0xA000000C:
                return JunctionType.SYMLINK

        finally:
            win32file.CloseHandle(handle)

    except Exception as e:
        logger.debug(f"Windows API failed for {path}: {e}")

    # Fallback: Use Python's os.readlink and infer type
    try:
        import os

        os.readlink(path)
        # If we can read it with os.readlink, it's likely a symlink
        # NTFS junctions are also readable via os.readlink on modern Windows
        # We can differentiate by checking if it's a directory vs file
        if path.is_junction():
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
        for dirpath, directories, filenames in os.walk(path):
            directories[:] = [
                name
                for name in directories
                if not (Path(dirpath) / name).is_junction()
                and not (Path(dirpath) / name).is_symlink()
            ]
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
    try:
        junction.target.stat()
        junction.source.stat()
    except FileNotFoundError:
        return JunctionStatus.BROKEN
    except OSError:
        return JunctionStatus.INACCESSIBLE

    # Check if accessible
    try:
        # Try to access the target
        if junction.is_directory:
            with os.scandir(junction.target) as entries:
                next(entries, None)
        else:
            with junction.target.open("rb") as stream:
                stream.read(1)
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
    known_junctions: set[Path] | None = None,
) -> list[Junction]:
    """
    Scan a directory for junctions, symlinks, and hard links.

    Args:
        path: Directory to scan
        recursive: Whether to scan recursively
        known_junctions: Set of junction paths known to be created by the app

    Returns:
        List of found junctions
    """
    if known_junctions is None:
        known_junctions = set()

    junctions: list[Junction] = []

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
                    is_directory = bool(
                        win32api.GetFileAttributes(str(item)) & win32con.FILE_ATTRIBUTE_DIRECTORY
                    )

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
                        # Directory totals are calculated lazily in Properties.
                        if not junction.is_directory:
                            try:
                                junction.size_bytes = junction.source.stat().st_size
                            except (OSError, PermissionError):
                                pass

                    junctions.append(junction)
                    logger.info(f"Found junction: {item} -> {target}")

                # Check for hard links (files only)
                elif item.is_file() and is_hard_link(item):
                    # All hard link names are peers. Keep another name as the
                    # source so removing the selected name can preserve a peer.
                    try:
                        stat = item.stat()
                        is_directory = False

                        # Create junction object for hard link
                        junction = Junction(
                            source=next(
                                (
                                    Path(item.anchor) / name.lstrip("\\/")
                                    for name in win32file.FindFileNames(str(item))
                                    if Path(item.anchor) / name.lstrip("\\/") != item
                                ),
                                item,
                            ),
                            target=item,
                            junction_type=JunctionType.HARDLINK,
                            is_directory=is_directory,
                        )

                        # Check status
                        junction.status = check_junction_status(junction)

                        # Classify creator
                        junction.creator = classify_creator(junction, known_junctions)

                        # Calculate size
                        try:
                            junction.size_bytes = stat.st_size
                        except (OSError, PermissionError):
                            pass

                        junctions.append(junction)
                        logger.info(f"Found hard link: {item} (nlink={stat.st_nlink})")
                    except Exception as e:
                        logger.warning(f"Error processing hard link {item}: {e}")

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
    known_junctions: set[Path] | None = None,
    use_cache: bool = False,
    cache_max_age_seconds: float = 3600,
) -> ScanResult:
    """
    Scan multiple directories for junctions, symlinks, and hard links.

    Args:
        directories: List of directories to scan
        recursive: Whether to scan recursively
        known_junctions: Set of junction paths known to be created by the app
        use_cache: Whether to use cached results if available
        cache_max_age_seconds: Maximum age of cache in seconds to consider valid

    Returns:
        ScanResult with found junctions and metadata
    """
    start_time = time.time()
    all_junctions: list[Junction] = []
    scanned_dirs = []
    errors = []

    if known_junctions is None:
        known_junctions = set()

    cache_manager = CacheManager()
    if use_cache:
        cached = cache_manager.load()
        if (
            cached
            and recursive
            and cached.scan_directories == [str(d) for d in directories]
            and cache_manager.is_cache_valid(cache_max_age_seconds)
        ):
            junctions = cached.to_junctions()
            for junction in junctions:
                junction.creator = classify_creator(junction, known_junctions)
            return ScanResult(
                junctions=junctions,
                scanned_directories=directories,
                scan_duration_seconds=time.time() - start_time,
            )

    # Perform actual scan
    for directory in directories:
        logger.info(f"Scanning directory: {directory}")
        try:
            junctions = scan_directory(directory, recursive, known_junctions)
            existing = {j.target for j in all_junctions}
            all_junctions.extend(j for j in junctions if j.target not in existing)
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

    # Save to cache
    if use_cache and recursive and not errors:
        cache_manager = CacheManager()
        cache_manager.save(result)

    return result
