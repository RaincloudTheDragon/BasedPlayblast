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
_ENCODER_PRIORITY = _NVENC_ENCODERS + ('libx264',)

_ENCODER_CACHE: dict[str, str] = {}

_NVENC_DRIVER_MARKERS = (
    'does not support the required nvenc api version',
    'minimum required nvidia driver',
    'no nvenc capable devices found',
    'driver does not support',
)


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


def list_encoder_candidates(ffmpeg_path: str) -> list[str]:
    """Return available encoders in preference order (NVENC family, then libx264).

    A previously successful encoder for this ffmpeg path is tried first.
    """
    encoders = _encoder_list_text(ffmpeg_path)
    available = [name for name in _ENCODER_PRIORITY if name in encoders]
    if not available:
        available = ['libx264']

    cached = _ENCODER_CACHE.get(ffmpeg_path)
    if cached and cached in available:
        return [cached] + [name for name in available if name != cached]
    return available


def detect_video_encoder(ffmpeg_path: str) -> str:
    """Pick the best available encoder: av1_nvenc, hevc_nvenc, h264_nvenc, then libx264."""
    return list_encoder_candidates(ffmpeg_path)[0]


def remember_working_encoder(ffmpeg_path: str, encoder: str) -> None:
    """Cache an encoder that successfully encoded on this machine."""
    _ENCODER_CACHE[ffmpeg_path] = encoder


def is_nvenc_encoder(encoder: str) -> bool:
    return encoder in _NVENC_ENCODERS


def is_nvenc_driver_error(stderr: str) -> bool:
    """True when FFmpeg failed because the NVIDIA driver is too old / incompatible."""
    text = (stderr or '').lower()
    return any(marker in text for marker in _NVENC_DRIVER_MARKERS)


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


def build_video_encode_args_for(
    encoder: str,
    encode_speed: str = 'SLOWEST',
    bitrate_limit_mbps: int = 0,
) -> list[str]:
    """Build FFmpeg video encode args for a specific encoder."""
    if encoder in _NVENC_ENCODERS:
        return _nvenc_encode_args(encoder, encode_speed, bitrate_limit_mbps)

    # CRF/QP 0 is true lossless and forces High 4:4:4 Predictive (breaks WMP).
    # CRF 1 is the lowest lossy setting that stays High + yuv420p — nearest to NVENC cq 0.
    speed = encode_speed if encode_speed in _LIBX264_PRESETS else 'SLOWEST'
    return [
        '-c:v', 'libx264',
        '-preset', _LIBX264_PRESETS[speed],
        '-crf', '1',
        '-profile:v', 'high',
    ]


def build_video_encode_args(
    ffmpeg_path: str,
    encode_speed: str = 'SLOWEST',
    bitrate_limit_mbps: int = 0,
) -> list[str]:
    """Build FFmpeg video encode args for visually lossless playblast output."""
    encoder = detect_video_encoder(ffmpeg_path)
    return build_video_encode_args_for(
        encoder,
        encode_speed=encode_speed,
        bitrate_limit_mbps=bitrate_limit_mbps,
    )


def default_custom_ffmpeg_args(ffmpeg_path: str, encode_speed: str = 'SLOWEST') -> str:
    """Serialize the auto-detected encode args for the custom-args text field."""
    return ' '.join(build_video_encode_args(ffmpeg_path, encode_speed=encode_speed))
