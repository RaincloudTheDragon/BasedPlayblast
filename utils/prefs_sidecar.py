"""
Sidecar JSON for BasedPlayblast addon preferences.

Survives Blender disable/enable (VS Code Reload Addons) via user CONFIG dir.
"""

import json
import os

import bpy

SIDECAR_VERSION = 1
SIDECAR_FILENAME = "bpl_prefs.json"

_FLAT_KEYS = (
    "default_encode_speed",
    "default_video_bitrate_limit",
    "default_audio_codec",
    "default_use_custom_ffmpeg_args",
    "default_ffmpeg_args",
    "ffmpeg_path",
    "show_flamenco_button",
    "use_flamenco_optix_for_cycles",
    "flamenco_manager_dir",
    "repo_initialized",
)

_restoring = False
_last_written = None


def is_restoring():
    return _restoring


def sidecar_path():
    base = bpy.utils.user_resource("CONFIG")
    if not base:
        return None
    return os.path.join(base, SIDECAR_FILENAME)


def _get_addon_prefs():
    # bl_idname is the addon module name (__name__ of package root)
    for name, addon in bpy.context.preferences.addons.items():
        ap = getattr(addon, "preferences", None)
        if ap and hasattr(ap, "default_encode_speed") and hasattr(ap, "ffmpeg_path"):
            return ap
    return None


def prefs_snapshot(prefs):
    if prefs is None:
        return None
    out = {"version": SIDECAR_VERSION}
    for key in _FLAT_KEYS:
        if hasattr(prefs, key):
            out[key] = getattr(prefs, key)
    return out


def apply_snapshot(data, prefs):
    if not data or prefs is None:
        return False

    global _restoring
    _restoring = True
    try:
        for key in _FLAT_KEYS:
            if key in data and hasattr(prefs, key):
                try:
                    setattr(prefs, key, data[key])
                except Exception as e:
                    print(f"[BPL] Sidecar skip {key}: {e}")
        return True
    finally:
        _restoring = False


def load_sidecar():
    path = sidecar_path()
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[BPL] Could not read prefs sidecar {path}: {e}")
        return None


def save_sidecar(prefs=None):
    global _last_written
    if _restoring:
        return False

    prefs = prefs or _get_addon_prefs()
    path = sidecar_path()
    if not prefs or not path:
        return False

    snapshot = prefs_snapshot(prefs)
    if snapshot is None:
        return False

    # Enums/bools need JSON-friendly values
    encoded = json.dumps(snapshot, indent=2, sort_keys=True, default=str)
    if encoded == _last_written:
        return False

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.write("\n")
        _last_written = encoded
        return True
    except Exception as e:
        print(f"[BPL] Could not write prefs sidecar {path}: {e}")
        return False


def restore_sidecar_into_prefs(prefs=None):
    prefs = prefs or _get_addon_prefs()
    data = load_sidecar()
    if not data or not prefs:
        return False

    ok = apply_snapshot(data, prefs)
    if ok:
        global _last_written
        try:
            _last_written = json.dumps(
                prefs_snapshot(prefs), indent=2, sort_keys=True, default=str
            )
        except Exception:
            _last_written = None
    return ok
