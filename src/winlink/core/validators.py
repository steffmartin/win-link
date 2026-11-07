"""Validation functions for junction operations"""

import os
from pathlib import Path

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
    errors: list[str] = []
    warnings: list[str] = []

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
    errors: list[str] = []
    warnings: list[str] = []

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
    errors: list[str] = []
    warnings: list[str] = []

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
    errors: list[str] = []
    warnings: list[str] = []

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
    errors: list[str] = []
    warnings: list[str] = []

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
    errors: list[str] = []
    warnings: list[str] = []

    if not os.path.lexists(path):
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
    errors: list[str] = []
    warnings: list[str] = []

    if os.path.lexists(path) and is_reparse_point(path):
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
    errors: list[str] = []
    warnings: list[str] = []

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
    *,
    is_directory: bool | None = None,
    calculate_storage: bool = True,
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
    errors: list[str] = []
    warnings: list[str] = []

    # Validate paths
    path_result = validate_path(source)
    errors.extend(path_result.errors)
    warnings.extend(path_result.warnings)

    path_result = validate_path(target)
    errors.extend(path_result.errors)
    warnings.extend(path_result.warnings)

    # Compare resolved paths so aliases and parent components cannot bypass safety checks.
    try:
        resolved_source = source.resolve()
        resolved_target = target.resolve()
        if resolved_source == resolved_source.parent or resolved_target == resolved_target.parent:
            errors.append("Volume roots cannot be used for migration operations")
        if (
            resolved_source == resolved_target
            or resolved_source in resolved_target.parents
            or resolved_target in resolved_source.parents
        ):
            errors.append("Source and target must be distinct, non-overlapping paths")
    except (OSError, RuntimeError) as exc:
        errors.append(f"Cannot resolve paths safely: {exc}")

    if not source.is_absolute() or not target.is_absolute():
        errors.append("Source and target must be absolute paths")
    if source == source.parent or target == target.parent:
        errors.append("Volume roots cannot be used for migration operations")

    if errors:
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # File links never replace existing user files.
    is_file_link = junction_type == JunctionType.HARDLINK or (
        junction_type == JunctionType.SYMLINK
        and (is_directory is False or (is_directory is None and source.is_file()))
    )
    if is_file_link:
        if not source.is_file():
            errors.append(
                "Hard links exigem um arquivo existente"
                if junction_type == JunctionType.HARDLINK
                else "Symlinks de arquivo exigem um arquivo de Dados Físicos existente"
            )
        if os.path.lexists(target):
            errors.append("O caminho do link já existe; escolha um novo nome")
        parent = target.parent
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        if junction_type == JunctionType.HARDLINK and source.exists():
            if source.stat().st_dev != parent.stat().st_dev:
                errors.append("Hard links devem estar no mesmo volume")
        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)

    if is_directory is False:
        errors.append("Selecione Hardlink ou Symlink para criar um link de arquivo")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    if junction_type == JunctionType.SYMLINK and target.exists() and not target.is_dir():
        errors.append("Para migrar um diretório, o destino deve ser uma pasta")

    # Validate source exists
    if junction_type == JunctionType.JUNCTION:
        if source.exists() and not source.is_dir():
            errors.append("Junction source must be a directory")
        if target.exists() and not target.is_dir():
            errors.append("Junction target must be a directory")
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    if not source.exists():
        warnings.append(f"Source does not exist and will be created: {source}")

    # Validate target is not already a junction
    if os.path.lexists(target) and is_reparse_point(target):
        errors.append(f"Target is already a junction or symlink: {target}")

    # Note: Target directory can have files - they will be copied to source
    # This is intentional behavior based on the specification

    # Check if source contains junctions (nested junctions) - warning only
    if source.exists() and source.is_dir():
        from winlink.core.config import get_settings
        from winlink.core.scanner import scan_directory

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
    if calculate_storage and target.exists():
        required = calculate_disk_space_required(target)
        disk_path = source
        while not disk_path.exists() and disk_path != disk_path.parent:
            disk_path = disk_path.parent
        space_result = validate_disk_space(disk_path, required)
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
    errors: list[str] = []
    warnings: list[str] = []

    # Validate target exists
    if not os.path.lexists(junction.target):
        errors.append(f"Junction target does not exist: {junction.target}")

    # Validate it's actually a junction
    if os.path.lexists(junction.target) and not is_reparse_point(junction.target):
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
    *,
    calculate_storage: bool = True,
) -> ValidationResult:
    """
    Validate undo operation.

    Args:
        junction: Junction to undo
        strategy: Undo strategy

    Returns:
        ValidationResult
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Validate junction exists
    if not junction.target.exists():
        errors.append(f"Junction does not exist: {junction.target}")

    # Validate strategy
    valid_strategies = ["REMOVE_ONLY", "MOVE_BACK", "DUPLICATE", "KEEP_SOURCE"]
    if strategy not in valid_strategies:
        errors.append(f"Invalid undo strategy: {strategy}")

    # Check disk space for move back or duplicate
    if calculate_storage and strategy in ["MOVE_BACK", "DUPLICATE"]:
        if junction.source.exists():
            required = calculate_disk_space_required(junction.source)
            space_result = validate_disk_space(junction.target.parent, required)
            errors.extend(space_result.errors)
            warnings.extend(space_result.warnings)

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
