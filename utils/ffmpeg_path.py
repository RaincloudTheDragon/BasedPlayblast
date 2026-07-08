"""Locate an ffmpeg executable for BasedPlayblast."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

_FFMPEG_BOOTSTRAP_ATTEMPTED = False

# Official Windows essentials build recommended for Blender-adjacent tooling.
_FFMPEG_ESSENTIALS_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)


def addon_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundled_ffmpeg_path() -> str:
    return os.path.join(addon_root(), "tools", "ffmpeg.exe")


def iter_blender_bundled_ffmpeg_paths():
    """Yield likely paths to ffmpeg shipped with this Blender install."""
    try:
        import bpy  # type: ignore

        binary = bpy.app.binary_path
        if not binary:
            return
        binary_dir = os.path.dirname(binary)
        version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
        names = ("ffmpeg.exe", "ffmpeg") if sys.platform == "win32" else ("ffmpeg",)

        roots = [binary_dir]
        parent = os.path.dirname(binary_dir)
        if parent:
            roots.append(parent)
        if sys.platform == "darwin":
            resources = os.path.join(os.path.dirname(binary_dir), "Resources")
            if os.path.isdir(resources):
                roots.append(resources)
                roots.append(os.path.join(resources, version))

        subdirs = (
            "",
            version,
            "ffmpeg",
            os.path.join(version, "ffmpeg"),
            os.path.join(version, "ffmpeg", "bin"),
            os.path.join("ffmpeg", "bin"),
        )

        seen = set()
        for root in roots:
            for sub in subdirs:
                for name in names:
                    path = os.path.normpath(
                        os.path.join(root, sub, name) if sub else os.path.join(root, name)
                    )
                    if path not in seen:
                        seen.add(path)
                        yield path
    except Exception:
        return


def _bootstrap_bundled_ffmpeg() -> str | None:
    """Download ffmpeg essentials into addon tools/ when no executable is found."""
    global _FFMPEG_BOOTSTRAP_ATTEMPTED
    if _FFMPEG_BOOTSTRAP_ATTEMPTED or sys.platform != "win32":
        return None
    _FFMPEG_BOOTSTRAP_ATTEMPTED = True

    target = bundled_ffmpeg_path()
    if os.path.isfile(target):
        return target

    tools_dir = os.path.dirname(target)
    os.makedirs(tools_dir, exist_ok=True)

    print("[BasedPlayblast] No ffmpeg found; downloading essentials build to addon tools/...")
    try:
        with tempfile.TemporaryDirectory(prefix="basedplayblast_ffmpeg_") as tmp_dir:
            zip_path = os.path.join(tmp_dir, "ffmpeg-essentials.zip")
            with urllib.request.urlopen(_FFMPEG_ESSENTIALS_URL, timeout=120) as response:
                with open(zip_path, "wb") as handle:
                    shutil.copyfileobj(response, handle)

            with zipfile.ZipFile(zip_path) as archive:
                member = next(
                    (name for name in archive.namelist() if name.endswith("/bin/ffmpeg.exe")),
                    None,
                )
                if not member:
                    print("[BasedPlayblast] ffmpeg bootstrap failed: ffmpeg.exe not found in archive")
                    return None
                archive.extract(member, tmp_dir)
                extracted = os.path.join(tmp_dir, member.replace("/", os.sep))
                shutil.copy2(extracted, target)

        if os.path.isfile(target):
            print(f"[BasedPlayblast] Installed bundled ffmpeg: {target}")
            return target
    except Exception as exc:
        print(f"[BasedPlayblast] ffmpeg bootstrap failed: {exc}")

    return None


def resolve_ffmpeg_path() -> str:
    """Resolve ffmpeg: addon override, addon bundle, Blender, bootstrap, then PATH."""
    try:
        import bpy  # type: ignore

        for addon_name in (
            "BasedPlayblast",
            "basedplayblast",
            "bl_ext.basedplayblast",
            "bl_ext.user_local.basedplayblast",
        ):
            prefs = bpy.context.preferences.addons.get(addon_name)
            if not prefs or not prefs.preferences:
                continue
            if hasattr(prefs.preferences, "ffmpeg_path"):
                custom = getattr(prefs.preferences, "ffmpeg_path", "").strip()
                if custom and os.path.isfile(custom):
                    return custom
    except Exception:
        pass

    bundled = bundled_ffmpeg_path()
    if os.path.isfile(bundled):
        return bundled

    for candidate in iter_blender_bundled_ffmpeg_paths():
        if os.path.isfile(candidate):
            return candidate

    bootstrapped = _bootstrap_bundled_ffmpeg()
    if bootstrapped and os.path.isfile(bootstrapped):
        return bootstrapped

    exe = shutil.which("ffmpeg")
    if exe:
        print(
            f"[BasedPlayblast] Warning: no addon-bundled ffmpeg; falling back to PATH: {exe}"
        )
        return exe

    for candidate in (
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ):
        if candidate and os.path.isfile(candidate):
            return candidate

    return "ffmpeg"
