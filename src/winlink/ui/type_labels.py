"""Consistent user-facing labels for link types."""

from winlink.core.models import JunctionType


def link_type_label(junction_type: JunctionType, is_directory: bool) -> str:
    if junction_type == JunctionType.JUNCTION:
        return "Junção"
    if junction_type == JunctionType.SYMLINK:
        return f"Symlink ({'pasta' if is_directory else 'arquivo'})"
    if junction_type == JunctionType.HARDLINK:
        return "Hardlink"
    return junction_type.value
