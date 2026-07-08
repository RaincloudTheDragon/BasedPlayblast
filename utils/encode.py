"""FFmpeg video encode helpers for BasedPlayblast."""

from __future__ import annotations

import subprocess

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

_NVENC_ENCODERS = ('av1_nvenc', 'hevc_nvenc', 'h264_nvenc')

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
    """Pick the best available encoder: av1_nvenc, hevc_nvenc, h264_nvenc, then libx264."""
    cached = _ENCODER_CACHE.get(ffmpeg_path)
    if cached:
        return cached

    encoders = _encoder_list_text(ffmpeg_path)
    for candidate in _NVENC_ENCODERS + ('libx264',):
        if candidate in encoders:
            _ENCODER_CACHE[ffmpeg_path] = candidate
            return candidate

    _ENCODER_CACHE[ffmpeg_path] = 'libx264'
    return 'libx264'


def _vbr_bitrate_args(bitrate_limit_mbps: int) -> list[str]:
    """Optional NVENC VBR bitrate cap. 0 = uncapped."""
    if bitrate_limit_mbps <= 0:
        return []
    return [
        '-b:v', f'{bitrate_limit_mbps}M',
        '-maxrate', f'{bitrate_limit_mbps}M',
        '-bufsize', f'{bitrate_limit_mbps * 2}M',
    ]


def _nvenc_encode_args(
    encoder: str,
    encode_speed: str,
    bitrate_limit_mbps: int,
) -> list[str]:
    """GigaMux-style NVENC VBR: hq tune, spatial AQ, cq 0; optional bitrate cap."""
    speed = encode_speed if encode_speed in _NVENC_PRESETS else 'SLOWEST'
    args = [
        '-c:v', encoder,
        '-preset', _NVENC_PRESETS[speed],
        '-tune', 'hq',
        '-rc', 'vbr',
        '-rc-lookahead', '32',
        '-spatial-aq', '1',
        '-aq-strength', '15',
        '-cq', '0',
    ]
    args.extend(_vbr_bitrate_args(bitrate_limit_mbps))
    return args


def build_video_encode_args(
    ffmpeg_path: str,
    encode_speed: str = 'SLOWEST',
    bitrate_limit_mbps: int = 0,
) -> list[str]:
    """Build FFmpeg video encode args for visually lossless playblast output."""
    encoder = detect_video_encoder(ffmpeg_path)

    if encoder in _NVENC_ENCODERS:
        return _nvenc_encode_args(encoder, encode_speed, bitrate_limit_mbps)

    speed = encode_speed if encode_speed in _LIBX264_PRESETS else 'SLOWEST'
    return [
        '-c:v', 'libx264',
        '-preset', _LIBX264_PRESETS[speed],
        '-crf', '0',
    ]


def default_custom_ffmpeg_args(ffmpeg_path: str, encode_speed: str = 'SLOWEST') -> str:
    """Serialize the auto-detected encode args for the custom-args text field."""
    return ' '.join(build_video_encode_args(ffmpeg_path, encode_speed=encode_speed))
