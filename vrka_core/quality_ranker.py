"""Deterministic Video and Audio Quality Ranking System for VRKA 4.5.

Ranks viable media formats based on holistic visual fidelity:
- Resolution & dimension constraints
- Effective video bitrate (vbr/tbr)
- High frame rate (50/60 FPS preference)
- High Dynamic Range / 10-bit color depth (HDR10, HLG, Dolby Vision)
- Codec efficiency (contextual weighting without blind codec favoritism)
- Companion audio fidelity (abr, Opus/AAC)
- Deterministic format-ID tie-breaking
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RESOLUTION_HEIGHT_MAP: dict[str, int] = {
    "best available": 0,
    "best": 0,
    "8k (4320p)": 4320,
    "4320p": 4320,
    "4k (2160p)": 2160,
    "2160p": 2160,
    "1440p (2k)": 1440,
    "1440p (qhd)": 1440,
    "1440p": 1440,
    "1080p (full hd)": 1080,
    "1080p (fhd)": 1080,
    "1080p": 1080,
    "720p (hd)": 720,
    "720p": 720,
    "480p (sd)": 480,
    "480p": 480,
    "360p": 360,
    "240p": 240,
}

# Codec relative efficiency multipliers for comparable-bitrate scenarios
_CODEC_EFFICIENCY_MULTIPLIERS: dict[str, float] = {
    "av01": 1.30,  # AV1
    "av1": 1.30,
    "vp9": 1.20,
    "vp09": 1.20,
    "hevc": 1.22,  # H.265
    "h265": 1.22,
    "hvc1": 1.22,
    "avc1": 1.00,  # H.264
    "h264": 1.00,
}


@dataclass(frozen=True)
class QualityProfile:
    target_quality: str = "Best Available"
    prefer_60fps: bool = True
    prefer_hdr: bool = True
    audio_format: str = "MP3"
    mp3_bitrate: str = "320 kbps"

    @property
    def target_height(self) -> int:
        norm = self.target_quality.strip().lower()
        for key, height in RESOLUTION_HEIGHT_MAP.items():
            if key in norm or norm in key:
                return height
        return 0


def calculate_format_score(fmt: dict[str, Any], profile: QualityProfile) -> float:
    """Calculate deterministic holistic quality score for a format candidate."""
    height = fmt.get("height") or 0
    width = fmt.get("width") or 0
    fps = fmt.get("fps") or 30.0
    vbr = float(fmt.get("vbr") or fmt.get("tbr") or 0.0)
    abr = float(fmt.get("abr") or 0.0)
    vcodec = str(fmt.get("vcodec") or "").lower()
    dynamic_range = str(fmt.get("dynamic_range") or "").lower()

    target_h = profile.target_height

    # 1. Resolution constraint & fit
    if target_h > 0:
        if height > target_h:
            # Over-resolution: heavily penalized
            return -10000.0 + height
        # Higher matching resolution up to target
        res_score = height * 10.0
    else:
        # Best available: unbounded height preference
        res_score = height * 10.0

    # 2. Visual Bitrate Score (Foundation of fidelity)
    # If bitrate metadata is absent, approximate baseline by resolution
    if vbr <= 0.0 and height > 0:
        vbr = height * 2.5
    bitrate_score = vbr * 1.5

    # 3. High Frame Rate Score
    fps_score = 0.0
    if profile.prefer_60fps and fps >= 50.0:
        fps_score = 350.0
    elif fps > 30.0:
        fps_score = 100.0

    # 4. HDR / High Dynamic Range Score
    hdr_score = 0.0
    if profile.prefer_hdr and any(k in dynamic_range for k in ("hdr", "hlg", "dolby", "10bit", "10-bit")):
        hdr_score = 250.0

    # 5. Codec Efficiency Weighting
    # Subtle efficiency boost applied to bitrate score (never overcomes massive bitrate gaps)
    codec_mult = 1.0
    for prefix, mult in _CODEC_EFFICIENCY_MULTIPLIERS.items():
        if prefix in vcodec:
            codec_mult = mult
            break
    adjusted_bitrate_score = bitrate_score * codec_mult

    # 6. Companion Audio Score
    audio_score = abr * 0.8

    total_score = res_score + adjusted_bitrate_score + fps_score + hdr_score + audio_score
    return round(total_score, 3)


def rank_formats(formats: list[dict[str, Any]], profile: QualityProfile) -> list[dict[str, Any]]:
    """Sort viable formats deterministically in descending order of holistic quality."""
    if not formats:
        return []

    def sort_key(fmt: dict[str, Any]) -> tuple[float, str]:
        score = calculate_format_score(fmt, profile)
        fid = str(fmt.get("format_id") or "")
        # Score descending, format_id ascending as tiebreaker
        return (score, fid)

    return sorted(formats, key=sort_key, reverse=True)


def build_ytdlp_format_spec(mode: str, quality_label: str, prefer_60fps: bool = True) -> tuple[str, str]:
    """Generate yt-dlp format selector string and sorting arguments.

    Returns:
        (format_selector, format_sort_criteria)
    """
    if mode == "audio":
        return "bestaudio/best", "abr,acodec"

    target_h = 0
    norm = quality_label.strip().lower()
    for key, h in RESOLUTION_HEIGHT_MAP.items():
        if key in norm or norm in key:
            target_h = h
            break

    fps_crit = "fps:60" if prefer_60fps else "fps"
    sort_criteria = f"res,hdr:12,{fps_crit},vbr,codec,abr"

    if target_h <= 0:
        # Best available
        selector = "bv*+ba/b/best"
    else:
        # Exact height or highest available under target limit
        selector = f"bv*[height<={target_h}]+ba/b[height<={target_h}]/best"

    return selector, sort_criteria
