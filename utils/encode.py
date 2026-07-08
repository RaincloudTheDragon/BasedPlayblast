"""FFmpeg video encode helpers for BasedPlayblast."""

from __future__ import annotations

import subprocess
from typing import Iterable

ENCODE_SPEED_ITEMS = [
    ('FASTEST', "Fastest", "Fastest encode; lowest quality preset"),
    ('FAST', "Fast", "Fast encode"),
    ('MEDIUM', "Medium", "Balanced encode speed"),
    ('SLOW', "Slow", "Slower encode with better compression efficiency"),
    ('SLOWEST', "Slowest", "Slowest preset; best detail preservation (default)"),
]

_NVENC_PRESETS = {
    'FASTEST': 'p1',
    'FAST': 'p3',
    'MEDIUM': 'p5',
    'SLOW': 'p6',
    'SLOWEST': 'p7',
}

_LIBX264_PRESETS = {
    'FASTEST': 'ultrafast',
    'FAST': 'veryfast',
    'MEDIUM': 'medium',
    'SLOW': 'slow',
    'SLOWEST': 'veryslow',
}

_ENCODER_CACHE: dict[str, str] = {}


def _encoder_list_text(ffmpeg_path: str) -> str:
    try:
        result = subprocess.run(
            [ffmpeg_path, '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return (result.stdout or '') + (result.stderr or '')
    except (OSError, subprocess.SubprocessError):
        return ''


def detect_video_encoder(ffmpeg_path: str) -> str:
    """Pick the best available encoder: av1_nvenc, h264_nvenc, then libx264."""
    cached = _ENCODER_CACHE.get(ffmpeg_path)
    if cached:
        return cached

    encoders = _encoder_list_text(ffmpeg_path)
    for candidate in ('av1_nvenc', 'h264_nvenc', 'libx264'):
        if candidate in encoders:
            _ENCODER_CACHE[ffmpeg_path] = candidate
            return candidate

    _ENCODER_CACHE[ffmpeg_path] = 'libx264'
    return 'libx264'


def _bitrate_limit_args(bitrate_limit_mbps: int) -> list[str]:
    if bitrate_limit_mbps <= 0:
        return []
    limit = str(bitrate_limit_mbps)
    return ['-maxrate', f'{limit}M', '-bufsize', f'{bitrate_limit_mbps * 2}M']


def build_video_encode_args(
    ffmpeg_path: str,
    encode_speed: str = 'SLOWEST',
    bitrate_limit_mbps: int = 0,
) -> list[str]:
    """Build FFmpeg video encode args with CQ/CRF 0 defaults and encoder fallback."""
    encoder = detect_video_encoder(ffmpeg_path)
    speed = encode_speed if encode_speed in _NVENC_PRESETS else 'SLOWEST'

    if encoder == 'av1_nvenc':
        args = [
            '-c:v', 'av1_nvenc',
            '-preset', _NVENC_PRESETS[speed],
            '-rc', 'constqp',
            '-cq', '0',
        ]
    elif encoder == 'h264_nvenc':
        args = [
            '-c:v', 'h264_nvenc',
            '-preset', _NVENC_PRESETS[speed],
            '-rc', 'constqp',
            '-cq', '0',
        ]
    else:
        args = [
            '-c:v', 'libx264',
            '-preset', _LIBX264_PRESETS[speed],
            '-crf', '0',
        ]

    args.extend(_bitrate_limit_args(bitrate_limit_mbps))
    return args


def default_custom_ffmpeg_args(ffmpeg_path: str, encode_speed: str = 'SLOWEST') -> str:
    """Serialize the auto-detected encode args for the custom-args text field."""
    return ' '.join(build_video_encode_args(ffmpeg_path, encode_speed=encode_speed))
