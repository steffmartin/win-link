"""Operations for creating and managing junctions and links"""

import os
from pathlib import Path

import win32api
import win32con
import win32file

from winlink.core.models import Junction, JunctionStatus, JunctionType
from winlink.utils.logger import get_logger

logger = get_logger(__name__)

# Constants not in pywin32
SYMBOLIC_LINK_FLAG_DIRECTORY = 0x1
SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE = 0x2


def create_symbolic_link(
    target: Path,
    link: Path,
    is_directory: bool = True,
) -> bool:
    """
    Create a symbolic link using Windows API.

    Args:
        target: Target path (where files actually exist)
        link: Link path (the symbolic link to create)
        is_directory: Whether this is a directory link

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        link.parent.mkdir(parents=True, exist_ok=True)

        # Call CreateSymbolicLink
        # For directory links, the SYMBOLIC_LINK_FLAG_DIRECTORY flag must be set
        flags = SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE
        if is_directory:
            flags |= SYMBOLIC_LINK_FLAG_DIRECTORY

        result = win32file.CreateSymbolicLink(
            str(link),
            str(target),
            flags,
        )

        if result is None or result:
            logger.info(f"Created symbolic link: {link} -> {target}")
            return True
        else:
            error = win32api.GetLastError()
            logger.error(f"Failed to create symbolic link: {error}")
            return False

    except Exception as e:
        logger.error(f"Error creating symbolic link {link} -> {target}: {e}")
        return False


def create_hard_link(
    target: Path,
    link: Path,
) -> bool:
    """
    Create a hard link using Windows API.

    Args:
        target: Target file (where data actually exists)
        link: Link path (the hard link to create)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        link.parent.mkdir(parents=True, exist_ok=True)

        # Call CreateHardLinkW
        result = win32file.CreateHardLink(
            str(link),
            str(target),
            None,
        )

        if result is None or result:
            logger.info(f"Created hard link: {link} -> {target}")
            return True
        else:
            error = win32api.GetLastError()
            logger.error(f"Failed to create hard link: {error}")
            return False

    except Exception as e:
        logger.error(f"Error creating hard link {link} -> {target}: {e}")
        return False


def create_junction(
    target: Path,
    link: Path,
) -> bool:
    """
    Create an NTFS junction (mount point) using Windows API.

    Args:
        target: Target directory (where files actually exist)
        link: Link directory (the junction to create)

    Returns:
        True if successful, False otherwise
    """
    try:
        import _winapi

        # Remove existing directory if it exists
        if os.path.lexists(link):
            if link.is_symlink() or link.is_junction():
                logger.error(f"Cannot replace an existing link: {link}")
                return False
            if link.is_dir():
                if any(link.iterdir()):
                    logger.error(f"Cannot create junction: {link} is not empty")
                    return False
                link.rmdir()
            else:
                logger.error(f"Cannot replace an existing file: {link}")
                return False

        link.parent.mkdir(parents=True, exist_ok=True)
        _winapi.CreateJunction(str(target.absolute()), str(link.absolute()))
        logger.info(f"Created junction: {link} -> {target}")
        return True

    except Exception as e:
        logger.error(f"Error creating junction {link} -> {target}: {e}")
        return False


def remove_junction(link: Path) -> bool:
    """
    Remove a junction or symbolic link safely.

    Args:
        link: Path to the junction/link to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.lexists(link):
            logger.warning(f"Cannot remove junction: {link} does not exist")
            return False

        # Check if it's a reparse point
        attrs = win32api.GetFileAttributes(str(link))
        if not (attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT):
            logger.warning(f"Cannot remove junction: {link} is not a reparse point")
            return False

        # Remove the directory
        if attrs & win32con.FILE_ATTRIBUTE_DIRECTORY:
            link.rmdir()
        else:
            link.unlink()

        logger.info(f"Removed junction: {link}")
        return True

    except Exception as e:
        logger.error(f"Error removing junction {link}: {e}")
        return False


def verify_junction_integrity(junction: Junction) -> bool:
    """
    Verify the integrity of a junction.

    Args:
        junction: Junction to verify

    Returns:
        True if junction is intact, False otherwise
    """
    try:
        if junction.junction_type == JunctionType.HARDLINK:
            intact = (
                junction.source.is_file()
                and junction.target.is_file()
                and junction.source.samefile(junction.target)
            )
            junction.status = JunctionStatus.ACTIVE if intact else JunctionStatus.BROKEN
            return intact
        # Check if target exists
        if not junction.target.exists():
            logger.warning(f"Junction target does not exist: {junction.target}")
            junction.status = JunctionStatus.BROKEN
            return False

        # Check if source exists
        if not junction.source.exists():
            logger.warning(f"Junction source does not exist: {junction.source}")
            junction.status = JunctionStatus.BROKEN
            return False

        # Check if target is still a reparse point
        attrs = win32api.GetFileAttributes(str(junction.target))
        if not (attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT):
            logger.warning(f"Target is no longer a reparse point: {junction.target}")
            junction.status = JunctionStatus.BROKEN
            return False

        if not junction.source.samefile(junction.target):
            junction.status = JunctionStatus.BROKEN
            return False
        # Update status
        junction.status = JunctionStatus.ACTIVE
        return True

    except Exception as e:
        logger.error(f"Error verifying junction {junction.target}: {e}")
        junction.status = JunctionStatus.BROKEN
        return False


def recreate_junction(junction: Junction) -> bool:
    """
    Recreate a broken junction.

    Args:
        junction: Junction to recreate

    Returns:
        True if successful, False otherwise
    """
    try:
        if junction.junction_type == JunctionType.HARDLINK:
            if os.path.lexists(junction.target):
                return verify_junction_integrity(junction)
            return create_hard_link(junction.source, junction.target)
        # Remove existing junction if it exists
        if os.path.lexists(junction.target):
            if not remove_junction(junction.target):
                return False

        # Recreate based on type
        if junction.junction_type == JunctionType.JUNCTION:
            return create_junction(junction.source, junction.target)
        elif junction.junction_type == JunctionType.SYMLINK:
            return create_symbolic_link(junction.source, junction.target, junction.is_directory)
        elif junction.junction_type == JunctionType.HARDLINK:
            return create_hard_link(junction.source, junction.target)
        else:
            logger.error(f"Unknown junction type: {junction.junction_type}")
            return False

    except Exception as e:
        logger.error(f"Error recreating junction {junction.target}: {e}")
        return False


def verify_directory_link_reference(junction: Junction) -> bool:
    """Verify a directory reparse reference even when its data location is missing.

    Removing only the link must never require deleting or probing its data tree.
    Copy/move restoration still requires the stricter live integrity check.
    """
    try:
        if not junction.is_directory:
            return False
        if junction.junction_type == JunctionType.JUNCTION:
            if not junction.target.is_junction():
                return False
        elif junction.junction_type == JunctionType.SYMLINK:
            if not junction.target.is_symlink():
                return False
        else:
            return False
        reference = os.readlink(junction.target)
        if reference.startswith("\\\\?\\UNC\\"):
            reference = "\\\\" + reference[8:]
        elif reference.startswith(("\\\\?\\", "\\??\\")):
            reference = reference[4:]
        if not os.path.isabs(reference):
            reference = str(junction.target.parent / reference)
        return os.path.normcase(os.path.abspath(reference)) == os.path.normcase(
            os.path.abspath(junction.source)
        )
    except OSError:
        return False
