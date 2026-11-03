"""File operations for junction management"""

import os
import shutil
from pathlib import Path

from winlink.utils.logger import get_logger

logger = get_logger(__name__)


def copy_directory_with_metadata(
    source: Path,
    destination: Path,
    preserve_attributes: bool = True,
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
        # Use shutil.copytree for directory copy
        if preserve_attributes:
            # shutil.copytree preserves metadata by default
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copytree(source, destination, dirs_exist_ok=True, copy_function=shutil.copy)

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
        # Try to open the file in exclusive mode
        with open(file_path, "rb") as f:
            pass
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
