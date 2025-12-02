"""
Compatibility helpers wrapping Blender version-specific logic.

Anything that differs between Blender 4.2 LTS, 4.5 LTS, and 5.0+ should live here
so the main add-on stays focused on user-facing behavior.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

try:
    import bpy  # type: ignore
    from bpy.utils import register_class, unregister_class  # type: ignore
except ImportError:  # pragma: no cover - for static tooling
    bpy = None  # type: ignore
    register_class = unregister_class = lambda cls: None  # type: ignore

from . import version


# -- Registration helpers --------------------------------------------------
def safe_register_class(cls) -> bool:
    try:
        register_class(cls)
        return True
    except Exception as exc:  # pragma: no cover - Blender runtime logging
        print(f"[BasedPlayblast] register fail: {cls.__name__}: {exc}")
        return False


def safe_unregister_class(cls) -> bool:
    try:
        unregister_class(cls)
        return True
    except Exception as exc:  # pragma: no cover
        print(f"[BasedPlayblast] unregister fail: {cls.__name__}: {exc}")
        return False


# -- Scene/helpers ---------------------------------------------------------
def get_compositor_tree(scene):
    """
    Return the compositor node tree, accounting for Blender 5.0 renames.
    """
    if version.is_version_at_least(5, 0, 0):
        return getattr(scene, "compositing_node_tree", None)
    return getattr(scene, "node_tree", None)


def is_geometry_nodes_modifier(modifier) -> bool:
    return getattr(modifier, "type", None) == "NODES"


def get_geometry_nodes_node_group(modifier):
    if is_geometry_nodes_modifier(modifier):
        return getattr(modifier, "node_group", None)
    return None


# -- Render IO -------------------------------------------------------------
def set_video_file_format(scene) -> bool:
    """
    Force Blender onto a video-friendly output. Returns True if a usable
    format was chosen; False means callers should warn/abort.
    """
    if not scene or not getattr(scene, "render", None):
        return False

    render = scene.render
    is_blender_5 = version.is_version_at_least(5, 0, 0)

    if not is_blender_5:
        try:
            render.image_settings.file_format = "FFMPEG"
            return True
        except Exception as exc:
            print(f"[BasedPlayblast] FFMPEG set failed: {exc}")
            return False

    candidates = ["AVI_JPEG", "AVI_RAW", "H264", "THEORA", "XVID", "FFMPEG"]
    for fmt in candidates:
        try:
            render.image_settings.file_format = fmt
            print(f"[BasedPlayblast] video format -> {fmt}")
            return True
        except Exception:
            continue

    # Last resort: PNG series with manual encode step
    try:
        render.image_settings.file_format = "PNG"
        print("[BasedPlayblast] video fallback -> PNG sequence")
        return False
    except Exception as exc:
        print(f"[BasedPlayblast] PNG fallback failed: {exc}")
        return False


def viewport_opengl_render(context, area=None, region=None):
    """
    Invoke viewport OpenGL animation render with overrides tuned per version.
    """
    if bpy is None:
        raise RuntimeError("bpy unavailable")

    is_blender_5 = version.is_version_at_least(5, 0, 0)

    def _call(**override_kwargs):
        with context.temp_override(**override_kwargs):
            bpy.ops.render.opengl(
                "INVOKE_DEFAULT",
                animation=True,
                sequencer=False,
                write_still=False,
                **({"view_context": True} if not is_blender_5 else {}),
            )

    def _resolve_region(target_area, candidate_region):
        if candidate_region and getattr(candidate_region, "type", None) == "WINDOW":
            return candidate_region
        if target_area:
            for reg in target_area.regions:
                if getattr(reg, "type", None) == "WINDOW":
                    return reg
        return None

    target_region = _resolve_region(area, region)
    try:
        if area and target_region:
            override = context.copy()
            override["area"] = area
            override["region"] = target_region
            _call(**override)
            return True
        bpy.ops.render.opengl(
            "INVOKE_DEFAULT", animation=True, sequencer=False, write_still=False
        )
        return True
    except TypeError:
        # Blender 5 requires explicit view_context flag in some builds
        if area and target_region:
            override = context.copy()
            override["area"] = area
            override["region"] = target_region
            with context.temp_override(**override):
                bpy.ops.render.opengl(
                    "INVOKE_DEFAULT",
                    animation=True,
                    sequencer=False,
                    write_still=False,
                    view_context=False,
                )
                return True
        bpy.ops.render.opengl(
            "INVOKE_DEFAULT",
            animation=True,
            sequencer=False,
            write_still=False,
            view_context=False,
        )
        return True
    except Exception as exc:
        print(f"[BasedPlayblast] OpenGL render failed: {exc}")
        raise


# -- Studio lights helpers --------------------------------------------------
def iter_studio_light_dirs(blender_binary_path: Optional[str]) -> Iterable[str]:
    if not blender_binary_path:
        return []

    blender_dir = os.path.dirname(blender_binary_path)
    version_token = version.get_version_category().split("+")[0]
    candidates = [
        os.path.join(blender_dir, "datafiles", "studiolights", "world"),
        os.path.join(blender_dir, version_token, "datafiles", "studiolights", "world"),
        os.path.join(os.path.dirname(blender_dir), version_token, "datafiles", "studiolights", "world"),
        os.path.join(os.path.dirname(os.path.dirname(blender_binary_path)), version_token, "datafiles", "studiolights", "world"),
        os.path.join("C:\\Program Files\\Blender Foundation", f"Blender {version_token}", version_token, "datafiles", "studiolights", "world"),
    ]
    seen = set()
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            yield path


def find_first_existing_path(paths: Iterable[str]) -> Optional[str]:
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def resolve_hdri_path(studio_dir: Optional[str]) -> Optional[str]:
    if not studio_dir:
        return None

    preferred = [
        "forest.exr",
        "studio.exr",
        "city.exr",
        "courtyard.exr",
        "night.exr",
        "sunrise.exr",
        "sunset.exr",
    ]

    for fname in preferred:
        candidate = os.path.join(studio_dir, fname)
        if os.path.exists(candidate):
            return candidate

    try:
        for entry in os.listdir(studio_dir):
            if entry.lower().endswith(".exr"):
                return os.path.join(studio_dir, entry)
    except Exception as exc:
        print(f"[BasedPlayblast] Studio dir listing failed: {exc}")
    return None

