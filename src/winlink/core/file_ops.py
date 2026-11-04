"""File operations for junction management"""

import os
import shutil
from collections.abc import Callable
from pathlib import Path

from winlink.utils.logger import get_logger

logger = get_logger(__name__)


def copy_directory_with_metadata(
    source: Path,
    destination: Path,
    preserve_attributes: bool = True,
    check_cancelled: Callable[[], None] | None = None,
) -> bool:
    """
    Copy a directory with all metadata preserved.

    Args:
        source: Source directory
        destination: Destination directory
        preserve_attributes: Whether to preserve file attributes

    Returns:
        True if successful, False otherwise
    """
    try:
        source_resolved, destination_resolved = source.resolve(), destination.resolve()
        if (
            source_resolved == destination_resolved
            or source_resolved in destination_resolved.parents
            or destination_resolved in source_resolved.parents
        ):
            logger.error("Cannot copy overlapping directory trees")
            return False
        if destination.is_symlink() or destination.is_junction():
            raise OSError("A pasta de destino da cópia foi substituída por um link")
        # Inspect all collisions before copytree can overwrite any existing data.
        if destination.exists():
            for root, directories, filenames in os.walk(source):
                relative = Path(root).relative_to(source)
                for name in filenames:
                    existing = destination / relative / name
                    if os.path.lexists(existing):
                        logger.error(f"Copy conflict; destination already exists: {existing}")
                        return False
                for name in directories:
                    existing = destination / relative / name
                    if os.path.lexists(existing) and (
                        not existing.is_dir() or existing.is_symlink() or existing.is_junction()
                    ):
                        logger.error(f"Copy directory conflict: {existing}")
                        return False
                directories[:] = [
                    name
                    for name in directories
                    if not (Path(root) / name).is_junction()
                    and not (Path(root) / name).is_symlink()
                ]

        def copy_checked(src, dst):
            if check_cancelled is not None:
                check_cancelled()
            from uuid import uuid4

            destination_path = Path(dst)
            temporary = destination_path.with_name(f".{destination_path.name}.{uuid4().hex}.tmp")
            try:
                if check_cancelled is not None and Path(src).stat().st_size > 8 * 1024 * 1024:
                    with open(src, "rb") as reader, temporary.open("xb") as writer:
                        while chunk := reader.read(1024 * 1024):
                            check_cancelled()
                            writer.write(chunk)
                    if preserve_attributes:
                        shutil.copystat(src, temporary)
                else:
                    copy = shutil.copy2 if preserve_attributes else shutil.copy
                    copy(src, temporary)
                if check_cancelled is not None:
                    check_cancelled()
                # Windows rename refuses to replace a file created during the copy.
                temporary.rename(destination_path)
                return str(destination_path)
            finally:
                if temporary.exists():
                    temporary.unlink()

        if check_cancelled is not None:
            check_cancelled()

        def preserve_junctions(root, names):
            from winlink.core.operations import create_junction

            ignored = []
            for name in names:
                entry = Path(root) / name
                if entry.is_junction():
                    if check_cancelled is not None:
                        check_cancelled()
                    copied_link = destination / entry.relative_to(source)
                    copied_link.parent.mkdir(parents=True, exist_ok=True)
                    if not create_junction(Path(os.readlink(entry)), copied_link):
                        raise OSError(f"Cannot preserve junction: {entry}")
                    ignored.append(name)
            return ignored

        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
            copy_function=copy_checked,
            symlinks=True,
            ignore=preserve_junctions,
        )

        logger.info(f"Copied directory: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Error copying directory {source} to {destination}: {e}")
        return False


def copy_file_with_metadata(
    source: Path,
    destination: Path,
    preserve_attributes: bool = True,
) -> bool:
    """
    Copy a file with metadata preserved.

    Args:
        source: Source file
        destination: Destination file
        preserve_attributes: Whether to preserve file attributes

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        if preserve_attributes:
            # shutil.copy2 preserves metadata
            shutil.copy2(source, destination)
        else:
            shutil.copy(source, destination)

        logger.info(f"Copied file: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Error copying file {source} to {destination}: {e}")
        return False


def move_directory(
    source: Path,
    destination: Path,
) -> bool:
    """
    Move a directory.

    Args:
        source: Source directory
        destination: Destination directory

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source), str(destination))
        logger.info(f"Moved directory: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Error moving directory {source} to {destination}: {e}")
        return False


def move_file(
    source: Path,
    destination: Path,
) -> bool:
    """
    Move a file.

    Args:
        source: Source file
        destination: Destination file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source), str(destination))
        logger.info(f"Moved file: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Error moving file {source} to {destination}: {e}")
        return False


def duplicate_directory(
    source: Path,
    destination: Path,
) -> bool:
    """
    Duplicate a directory (copy without removing source).

    Args:
        source: Source directory
        destination: Destination directory

    Returns:
        True if successful, False otherwise
    """
    return copy_directory_with_metadata(source, destination, preserve_attributes=True)


def duplicate_file(
    source: Path,
    destination: Path,
) -> bool:
    """
    Duplicate a file (copy without removing source).

    Args:
        source: Source file
        destination: Destination file

    Returns:
        True if successful, False otherwise
    """
    return copy_file_with_metadata(source, destination, preserve_attributes=True)


def is_file_in_use(file_path: Path) -> bool:
    """
    Check if a file is in use by another process.

    Args:
        file_path: Path to file

    Returns:
        True if file is in use, False otherwise
    """
    try:
        import win32file

        if not file_path.exists():
            return False
        handle = win32file.CreateFile(
            str(file_path),
            win32file.GENERIC_READ,
            0,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        handle.Close()
        return False
    except PermissionError:
        # File is likely in use
        return True
    except FileNotFoundError:
        # File doesn't exist
        return False
    except Exception as e:
        logger.warning(f"Error checking if file {file_path} is in use: {e}")
        return True


def calculate_directory_size_recursive(path: Path) -> int:
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


def calculate_disk_space_required(path: Path) -> int:
    """
    Calculate disk space required for a directory/file.

    Args:
        path: Path to calculate

    Returns:
        Space required in bytes
    """
    if path.is_file():
        try:
            return path.stat().st_size
        except (OSError, PermissionError):
            return 0
    elif path.is_dir():
        return calculate_directory_size_recursive(path)
    return 0


def get_available_disk_space(path: Path) -> int:
    """
    Get available disk space for a path.

    Args:
        path: Path to check disk space

    Returns:
        Available space in bytes
    """
    try:
        usage = shutil.disk_usage(path)
        return usage.free
    except Exception as e:
        logger.error(f"Error getting disk space for {path}: {e}")
        return 0


def has_sufficient_disk_space(path: Path, required_bytes: int) -> bool:
    """
    Check if there is sufficient disk space.

    Args:
        path: Path to check
        required_bytes: Required space in bytes

    Returns:
        True if sufficient space, False otherwise
    """
    available = get_available_disk_space(path)
    return available >= required_bytes


def delete_directory(path: Path) -> bool:
    """
    Delete a directory and all its contents.

    Args:
        path: Path to directory

    Returns:
        True if successful, False otherwise
    """
    try:
        shutil.rmtree(path)
        logger.info(f"Deleted directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting directory {path}: {e}")
        return False


def delete_file(path: Path) -> bool:
    """
    Delete a file.

    Args:
        path: Path to file

    Returns:
        True if successful, False otherwise
    """
    try:
        path.unlink()
        logger.info(f"Deleted file: {path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        return False


def ensure_directory_exists(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def is_directory_empty(path: Path) -> bool:
    """
    Check if a directory is empty.

    Args:
        path: Path to directory

    Returns:
        True if empty, False otherwise
    """
    try:
        return not any(path.iterdir())
    except Exception as e:
        logger.warning(f"Error checking if directory {path} is empty: {e}")
        return False


def tree_signature(path: Path) -> dict[str, tuple[int, int, int, int]]:
    """Capture identities and modification times without following directory links."""
    entries = {}

    def record(entry):
        stat = entry.lstat()
        entries[str(entry.relative_to(path))] = (
            stat.st_dev,
            stat.st_ino,
            stat.st_size,
            stat.st_mtime_ns,
        )

    record(path)
    for root, directories, files in os.walk(path):
        for name in directories + files:
            record(Path(root) / name)
        directories[:] = [
            name
            for name in directories
            if not (Path(root) / name).is_junction() and not (Path(root) / name).is_symlink()
        ]
    return entries
