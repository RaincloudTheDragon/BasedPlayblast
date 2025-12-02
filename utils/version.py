"""
Blender version helpers for BasedPlayblast.

Keeps the add-on logic clean by centralizing all version comparisons and
common constants for the supported tracks (4.4 LTS, 4.5 LTS, 5.0+).
"""

from __future__ import annotations

try:  # Blender runtime
    import bpy  # type: ignore
except ImportError:  # During static analysis or packaging
    bpy = None  # type: ignore

# Targeted LTS anchors
VERSION_4_4_LTS = (4, 4, 0)
VERSION_4_5_LTS = (4, 5, 0)
VERSION_5_0 = (5, 0, 0)


def _current_version() -> tuple[int, int, int]:
    """Return Blender's version tuple or a fallback."""
    if bpy and getattr(bpy.app, "version", None):
        return bpy.app.version  # type: ignore[return-value]
    return (0, 0, 0)


def get_blender_version() -> tuple[int, int, int]:
    return _current_version()


def get_version_string() -> str:
    v = _current_version()
    return f"{v[0]}.{v[1]}.{v[2]}"


def is_version_at_least(major: int, minor: int = 0, patch: int = 0) -> bool:
    current = _current_version()
    return current >= (major, minor, patch)


def is_version_less_than(major: int, minor: int = 0, patch: int = 0) -> bool:
    current = _current_version()
    return current < (major, minor, patch)


def get_version_category() -> str:
    """
    Collapse Blender versions into the compatibility buckets we actively test.
    """
    major, minor, _ = _current_version()
    if major < 4:
        return f"{major}.{minor}"
    if major == 4 and minor < 5:
        return "4.4"
    if major == 4:
        return "4.5"
    return "5.0+"


def is_supported() -> bool:
    """Check if the detected version is at least our minimum target."""
    return not is_version_less_than(*VERSION_4_4_LTS)


