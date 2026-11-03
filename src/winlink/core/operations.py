"""Operations for creating and managing junctions and links"""

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

        if result:
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

        if result:
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
    # Try using Python's junction function first (mklink via subprocess)
    try:
        import subprocess

        # Remove existing directory if it exists
        if link.exists():
            if link.is_dir():
                if any(link.iterdir()):
                    logger.error(f"Cannot create junction: {link} is not empty")
                    return False
                link.rmdir()
            else:
                link.unlink()

        # Use mklink command
        result = subprocess.run(
            ["mklink", "/J", str(link), str(target)],
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"Created junction: {link} -> {target}")
            return True
        else:
            logger.error(f"mklink failed: {result.stderr}")
            return False

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
        if not link.exists():
            logger.warning(f"Cannot remove junction: {link} does not exist")
            return False

        # Check if it's a reparse point
        attrs = win32api.GetFileAttributes(str(link))
        if not (attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT):
            logger.warning(f"Cannot remove junction: {link} is not a reparse point")
            return False

        # Remove the directory
        if link.is_dir():
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
        # Remove existing junction if it exists
        if junction.target.exists():
            remove_junction(junction.target)

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
