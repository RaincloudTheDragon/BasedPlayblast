"""Deploy BasedPlayblast job compiler scripts to a Flamenco Manager install."""

from __future__ import annotations

import json
import os
import re
import shutil
import urllib.error
import urllib.request

MANAGER_CONFIG_NAME = "flamenco-manager.yaml"
SCRIPTS_DIR_NAME = "scripts"

SCRIPT_FILENAMES = (
    "BasedPlayblast.js",
    "BasedPlayblast_Optix_GPU.js",
)

# Flamenco 3.7+ loads job compiler scripts on demand (no Manager restart).
LIVE_SCRIPTS_MIN_VERSION = (3, 7, 0)


def addon_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundled_scripts_dir() -> str:
    return os.path.join(addon_root(), "flamenco")


def manager_config_path(manager_dir: str) -> str:
    return os.path.join(manager_dir, MANAGER_CONFIG_NAME)


def manager_scripts_dir(manager_dir: str) -> str:
    return os.path.join(manager_dir, SCRIPTS_DIR_NAME)


def read_manager_config(manager_dir: str) -> str:
    path = manager_config_path(manager_dir)
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def validate_manager_dir(manager_dir: str) -> tuple[bool, str]:
    manager_dir = os.path.normpath(manager_dir)
    if not manager_dir or not os.path.isdir(manager_dir):
        return False, "Selected path is not a directory"

    config_path = manager_config_path(manager_dir)
    if not os.path.isfile(config_path):
        return (
            False,
            f"{MANAGER_CONFIG_NAME} not found. Select the folder that contains the Flamenco Manager executable.",
        )

    return True, config_path


def _parse_listen_host_port(config_text: str) -> tuple[str, int]:
    match = re.search(r"^listen:\s*['\"]?([^'\"\n#]+)", config_text, re.MULTILINE)
    listen = match.group(1).strip() if match else ":8080"

    if listen.startswith(":"):
        return "127.0.0.1", int(listen[1:])

    if "://" in listen:
        listen = listen.split("://", 1)[1]

    if ":" in listen:
        host, port_text = listen.rsplit(":", 1)
        host = host or "127.0.0.1"
        return host, int(port_text)

    return listen or "127.0.0.1", 8080


def _parse_version_string(version_text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_text)
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return major, minor, patch


def query_manager_version(manager_dir: str) -> tuple[int, int, int] | None:
    """Best-effort Manager version lookup via the local HTTP API."""
    try:
        config_text = read_manager_config(manager_dir)
    except OSError:
        return None

    host, port = _parse_listen_host_port(config_text)
    endpoints = (
        f"http://{host}:{port}/api/v3/meta/version",
        f"http://{host}:{port}/api/v2/meta/version",
        f"http://{host}:{port}/version",
    )

    for url in endpoints:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
            continue

        for key in ("version", "Version", "manager_version"):
            if key in payload:
                parsed = _parse_version_string(str(payload[key]))
                if parsed:
                    return parsed

        if isinstance(payload, dict) and "name" in payload and "version" in payload:
            parsed = _parse_version_string(str(payload["version"]))
            if parsed:
                return parsed

    return None


def needs_manager_restart(version: tuple[int, int, int] | None) -> bool:
    if version is None:
        return False
    return version < LIVE_SCRIPTS_MIN_VERSION


def deploy_scripts(manager_dir: str) -> tuple[bool, str, list[str], bool, tuple[int, int, int] | None]:
    """
    Copy bundled Flamenco scripts into <manager>/scripts.

    Returns:
        ok, user_message, copied_files, restart_recommended, detected_version
    """
    ok, detail = validate_manager_dir(manager_dir)
    if not ok:
        return False, detail, [], False, None

    source_dir = bundled_scripts_dir()
    missing_sources = [
        name for name in SCRIPT_FILENAMES
        if not os.path.isfile(os.path.join(source_dir, name))
    ]
    if missing_sources:
        return False, f"Missing bundled scripts: {', '.join(missing_sources)}", [], False, None

    try:
        read_manager_config(manager_dir)
    except OSError as exc:
        return False, f"Could not read {MANAGER_CONFIG_NAME}: {exc}", [], False, None

    scripts_dir = manager_scripts_dir(manager_dir)
    os.makedirs(scripts_dir, exist_ok=True)

    copied: list[str] = []
    for name in SCRIPT_FILENAMES:
        shutil.copy2(os.path.join(source_dir, name), os.path.join(scripts_dir, name))
        copied.append(name)

    version = query_manager_version(manager_dir)
    restart = needs_manager_restart(version)

    if version and restart:
        version_label = ".".join(str(part) for part in version)
        message = (
            f"Deployed {len(copied)} script(s) to {scripts_dir}. "
            f"Flamenco Manager {version_label} requires a restart to load new scripts "
            f"(live reload was added in 3.7)."
        )
    elif version:
        version_label = ".".join(str(part) for part in version)
        message = (
            f"Deployed {len(copied)} script(s) to {scripts_dir}. "
            f"Flamenco Manager {version_label} will load them on the next job compile."
        )
    else:
        message = (
            f"Deployed {len(copied)} script(s) to {scripts_dir}. "
            "Flamenco 3.7+ loads scripts on demand; restart Manager if you are on an older version."
        )

    return True, message, copied, restart, version
