"""Validation functions for junction operations"""

import os
import shutil
from pathlib import Path
from typing import Optional

from winlink.core.file_ops import (
    calculate_disk_space_required,
    get_available_disk_space,
    is_directory_empty,
)
from winlink.core.models import Junction, JunctionType, ValidationResult
from winlink.core.scanner import is_reparse_point
from winlink.utils.logger import get_logger

logger = get_logger(__name__)


def validate_path(path: Path) -> ValidationResult:
    """
    Validate a path.

    Args:
        path: Path to validate

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Check if path is empty
    if not path or str(path).strip() == "" or str(path) == ".":
        errors.append("Path cannot be empty")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Check for invalid characters (excluding colon after drive letter)
    path_str = str(path)
    invalid_chars = '<>"|?*'
    # For Windows paths, check for invalid chars except colon in drive letter position
    if len(path_str) >= 2 and path_str[1] == ":":
        # Skip drive letter colon
        rest_of_path = path_str[2:]
        if any(char in rest_of_path for char in invalid_chars + ":"):
            errors.append(f"Path contains invalid characters: {invalid_chars}")
    else:
        if any(char in path_str for char in invalid_chars):
            errors.append(f"Path contains invalid characters: {invalid_chars}")

    # Check path length (Windows MAX_PATH is 260, but can be extended)
    if len(path_str) > 260 and not path_str.startswith("\\\\?\\"):
        warnings.append("Path exceeds 260 characters and may cause issues")

    # Check if path is absolute
    if not path.is_absolute():
        warnings.append("Path is not absolute")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_path_exists(path: Path) -> ValidationResult:
    """
    Validate that a path exists.

    Args:
        path: Path to validate

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if not path.exists():
        errors.append(f"Path does not exist: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_path_not_exists(path: Path) -> ValidationResult:
    """
    Validate that a path does not exist.

    Args:
        path: Path to validate

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if path.exists():
        errors.append(f"Path already exists: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_permissions(path: Path, write: bool = False) -> ValidationResult:
    """
    Validate permissions for a path.

    Args:
        path: Path to validate
        write: Whether write permission is required

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if not path.exists():
        errors.append(f"Path does not exist: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Check read permission
    if not os.access(path, os.R_OK):
        errors.append(f"No read permission for: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Check write permission if required
    if write and not os.access(path, os.W_OK):
        errors.append(f"No write permission for: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_disk_space(path: Path, required_bytes: int) -> ValidationResult:
    """
    Validate sufficient disk space.

    Args:
        path: Path to check disk space
        required_bytes: Required space in bytes

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    available = get_available_disk_space(path)

    if available < required_bytes:
        errors.append(
            f"Insufficient disk space. Required: {required_bytes:,} bytes, Available: {available:,} bytes"
        )
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Warn if less than 1GB remaining
    if available < 1024 * 1024 * 1024:
        warnings.append("Less than 1GB of disk space remaining")

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_is_junction(path: Path) -> ValidationResult:
    """
    Validate that a path is a junction/reparse point.

    Args:
        path: Path to validate

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if not path.exists():
        errors.append(f"Path does not exist: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    if not is_reparse_point(path):
        errors.append(f"Path is not a junction or symlink: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_is_not_junction(path: Path) -> ValidationResult:
    """
    Validate that a path is NOT a junction/reparse point.

    Args:
        path: Path to validate

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if path.exists() and is_reparse_point(path):
        errors.append(f"Path is already a junction or symlink: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_directory_empty(path: Path) -> ValidationResult:
    """
    Validate that a directory is empty.

    Args:
        path: Path to directory

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if not path.exists():
        errors.append(f"Directory does not exist: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    if not path.is_dir():
        errors.append(f"Path is not a directory: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    if not is_directory_empty(path):
        errors.append(f"Directory is not empty: {path}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    is_valid = True
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_junction_creation(
    source: Path,
    target: Path,
    junction_type: JunctionType,
) -> ValidationResult:
    """
    Validate junction creation operation.

    Args:
        source: Source path
        target: Target path (junction location)
        junction_type: Type of junction to create

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Validate paths
    path_result = validate_path(source)
    errors.extend(path_result.errors)
    warnings.extend(path_result.warnings)

    path_result = validate_path(target)
    errors.extend(path_result.errors)
    warnings.extend(path_result.warnings)

    # Validate source exists
    if not source.exists():
        warnings.append(f"Source does not exist and will be created: {source}")

    # Validate target is not already a junction
    if target.exists() and is_reparse_point(target):
        errors.append(f"Target is already a junction or symlink: {target}")

    # Validate target directory is empty if it exists
    if target.exists() and target.is_dir():
        if not is_directory_empty(target):
            errors.append(f"Target directory is not empty: {target}")

    # Check if source contains junctions (nested junctions) - warning only
    if source.exists() and source.is_dir():
        from winlink.core.scanner import scan_directory
        from winlink.core.config import get_settings

        settings = get_settings()
        if settings.warn_nested_junctions:
            nested_junctions = scan_directory(source, recursive=False)
            if nested_junctions:
                warnings.append(
                    f"Source directory contains {len(nested_junctions)} junction(s). "
                    "Windows will redirect correctly, but this may cause confusion."
                )
                warnings.append(
                    f"Found junctions in source: {[j.target.name for j in nested_junctions]}"
                )

    # Check disk space
    if source.exists():
        required = calculate_disk_space_required(source)
        space_result = validate_disk_space(target.parent, required)
        errors.extend(space_result.errors)
        warnings.extend(space_result.warnings)

    # Additional validation for hard links
    if junction_type == JunctionType.HARDLINK:
        if not source.is_file():
            errors.append("Hard links can only be created for files")
        if source.exists() and target.exists():
            # Hard links must be on same volume
            if source.stat().st_dev != target.stat().st_dev:
                errors.append("Hard links must be on the same volume")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_junction_removal(junction: Junction) -> ValidationResult:
    """
    Validate junction removal operation.

    Args:
        junction: Junction to remove

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Validate target exists
    if not junction.target.exists():
        errors.append(f"Junction target does not exist: {junction.target}")

    # Validate it's actually a junction
    if junction.target.exists() and not is_reparse_point(junction.target):
        errors.append(f"Target is not a junction or symlink: {junction.target}")

    # Check for files in use
    if junction.target.exists() and junction.target.is_dir():
        # Would need to check for processes using files in directory
        warnings.append("Ensure no processes are using files in the junction")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_undo_operation(
    junction: Junction,
    strategy: str,
) -> ValidationResult:
    """
    Validate undo operation.

    Args:
        junction: Junction to undo
        strategy: Undo strategy

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Validate junction exists
    if not junction.target.exists():
        errors.append(f"Junction does not exist: {junction.target}")

    # Validate strategy
    valid_strategies = ["REMOVE_ONLY", "MOVE_BACK", "DUPLICATE", "KEEP_SOURCE"]
    if strategy not in valid_strategies:
        errors.append(f"Invalid undo strategy: {strategy}")

    # Check disk space for move back or duplicate
    if strategy in ["MOVE_BACK", "DUPLICATE"]:
        if junction.source.exists():
            required = calculate_disk_space_required(junction.source)
            space_result = validate_disk_space(junction.target.parent, required)
            errors.extend(space_result.errors)
            warnings.extend(space_result.warnings)

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
