"""Dedicated failure classification subsystem for VRKA Desktop.

Classifies yt-dlp execution failures into BROWSER_RECOVERABLE and
NON_BROWSER_RECOVERABLE actions with structured evidence, strict priority
ordering, and context verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RecoveryAction(str, Enum):
    BROWSER_RECOVERABLE = "browser_recoverable"
    NON_BROWSER_RECOVERABLE = "non_browser_recoverable"


class FailureCategory(str, Enum):
    # Non-browser-recoverable
    CANCELLATION = "cancellation"
    POST_TRANSFER = "post_transfer"
    FFMPEG = "ffmpeg"
    LOCAL_STORAGE = "local_storage"
    PERMISSION = "permission"
    MISSING_RUNTIME = "missing_runtime"
    DNS = "dns"
    CONNECTION = "connection"
    TLS = "tls"
    DRM = "drm"
    AUTHENTICATION = "authentication"
    INVALID_CONFIGURATION = "invalid_configuration"
    INTERNAL_ERROR = "internal_error"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"

    # Browser-recoverable
    FLASHVARS = "flashvars"
    KVS_PLAYER = "kvs_player"
    PLAYER_EXTRACTION = "player_extraction"
    CLIENT_SIDE_PLAYER = "client_side_player"
    EMBEDDED_PLAYER = "embedded_player"
    GENERIC_PARSER = "generic_parser"
    PAGE_UNSUPPORTED = "page_unsupported"
    CLOUDFLARE = "cloudflare"
    COOKIE_WALL = "cookies"
    HTTP_BLOCK = "http"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ClassificationResult:
    action: RecoveryAction
    category: FailureCategory
    reason: str
    is_recoverable: bool
    friendly_message: str


# Markers indicating that actual media transfer or post-extraction began
_TRANSFER_STARTED_MARKERS = (
    "__vrka_title__",
    "__vrka_output__",
    "[download] destination:",
)

_TRANSFER_PROGRESS_RE = re.compile(
    r"\[download\]\s+\d{1,3}(?:\.\d+)?%", re.IGNORECASE
)

_FFMPEG_STAGE_MARKERS = (
    "[merger]",
    "[extractaudio]",
    "[videoconvertor]",
    "[embedthumbnail]",
    "[embedsubtitle]",
    "[metadata]",
)

_GENERIC_EXTRACTOR_FETCH_MARKERS = (
    "falling back on generic information extractor",
    "downloading webpage",
    "extracting information",
)

_STORAGE_ERRNO_RE = re.compile(r"\b(?:errno\s*(?:28|36)|enospc|enametoolong)\b", re.IGNORECASE)
_PERMISSION_ERRNO_RE = re.compile(r"\b(?:errno\s*(?:13|1)\b|eacces|eperm)\b", re.IGNORECASE)
_RUNTIME_ERRNO_RE = re.compile(r"\b(?:winerror\s*2|enoent)\b", re.IGNORECASE)



def has_transfer_started(output: str) -> bool:
    """Return True if output proves media resolution succeeded and transfer began."""
    lowered = output.lower()
    return any(marker in lowered for marker in _TRANSFER_STARTED_MARKERS) or bool(
        _TRANSFER_PROGRESS_RE.search(lowered)
    )


def classify_failure(
    output: str,
    *,
    stage: str = "",
    transferred: bool = False,
    is_cancelled: bool = False,
    prior_categories: tuple[str, ...] = (),
) -> ClassificationResult:
    """Classify a yt-dlp execution failure using strict priority ordering.

    Priority:
    1. Cancellation
    2. Post-transfer / media-transfer failures
    3. FFmpeg / post-processing failures
    4. Local / filesystem / runtime executable failures
    5. DNS / connection / TLS failures
    6. DRM / authentic authentication locks
    7. Browser-recoverable extraction failures (direct extraction only)
    8. Terminal unsupported / unknown
    """
    text = str(output or "").strip()
    lowered = text.lower()
    stage_lowered = str(stage or "").strip().lower()

    # ------------------------------------------------------------------
    # Priority 1: Cancellation
    # ------------------------------------------------------------------
    if is_cancelled or any(
        m in lowered
        for m in (
            "task cancellation requested",
            "download was cancelled",
            "downloadcanceled",
            "processcancelled",
            "taskcancelled",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.CANCELLATION,
            reason="Task or process was explicitly cancelled",
            is_recoverable=False,
            friendly_message="The download task was cancelled.",
        )

    # ------------------------------------------------------------------
    # Priority 2: Post-transfer / media-transfer failures
    # ------------------------------------------------------------------
    if transferred or has_transfer_started(text):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.POST_TRANSFER,
            reason="Failure occurred after media transfer had already started",
            is_recoverable=False,
            friendly_message="The download was interrupted during media transfer.",
        )

    # ------------------------------------------------------------------
    # Priority 3: FFmpeg / post-processing failures
    # ------------------------------------------------------------------
    is_ffmpeg_stage = stage_lowered in (
        "merging",
        "converting",
        "finalizing",
        "post_processing",
    )
    has_ffmpeg_markers = any(m in lowered for m in _FFMPEG_STAGE_MARKERS) or any(
        m in lowered
        for m in (
            "ffmpeg error",
            "ffmpeg exited with code",
            "non-zero return code from ffmpeg",
            "conversion failed!",
            "error while opening encoder",
            "error while decoding",
            "invalid data found when processing input",
        )
    )
    if is_ffmpeg_stage or has_ffmpeg_markers:
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.FFMPEG,
            reason="FFmpeg media processing or conversion failed",
            is_recoverable=False,
            friendly_message="Media processing with FFmpeg failed.",
        )

    # ------------------------------------------------------------------
    # Priority 4: Local / filesystem / runtime executable failures
    # ------------------------------------------------------------------
    if any(
        m in lowered
        for m in (
            "no space left on device",
            "disk is full",
            "disk full",
            "file name too long",
            "filename too long",
            "read-only file system",
            "cannot allocate memory",
        )
    ) or bool(_STORAGE_ERRNO_RE.search(text)):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.LOCAL_STORAGE,
            reason="Local disk or storage write error",
            is_recoverable=False,
            friendly_message="Insufficient disk space or filesystem error.",
        )

    if any(
        m in lowered
        for m in (
            "permission denied",
            "access is denied",
            "permissionerror",
            "operation not permitted",
        )
    ) or bool(_PERMISSION_ERRNO_RE.search(text)):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.PERMISSION,
            reason="Local file permission denied",
            is_recoverable=False,
            friendly_message="Permission denied when writing to destination.",
        )

    if any(
        m in lowered
        for m in (
            "ffmpeg not found",
            "ffprobe not found",
            "executable not found",
            "no such file or directory: 'yt-dlp'",
            "no such file or directory: 'ffmpeg'",
            "filenotfounderror",
        )
    ) or bool(_RUNTIME_ERRNO_RE.search(text)):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.MISSING_RUNTIME,
            reason="Required runtime executable not found on system",
            is_recoverable=False,
            friendly_message="A required helper executable was not found.",
        )

    if any(
        m in lowered
        for m in (
            "the selected output path is not a folder",
            "notadirectoryerror",
            "invalid custom command",
            "impersonation target is unavailable",
            "unsupported impersonation target",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.INVALID_CONFIGURATION,
            reason="Invalid local configuration or output path",
            is_recoverable=False,
            friendly_message="Invalid local task configuration.",
        )

    # ------------------------------------------------------------------
    # Priority 5: DNS / connection / TLS failures
    # ------------------------------------------------------------------
    if any(
        m in lowered
        for m in (
            "getaddrinfo failed",
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname provided",
            "dns_probe_finished_nxdomain",
            "failed to resolve",
            "could not resolve host",
            "name resolution failed",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.DNS,
            reason="Domain name resolution (DNS) failed before reaching host",
            is_recoverable=False,
            friendly_message="Could not resolve server address (DNS failure).",
        )

    if any(
        m in lowered
        for m in (
            "connection refused",
            "network is unreachable",
            "no route to host",
            "failed to establish a new connection",
            "connection reset by peer",
            "unable to connect to",
            "connection closed prematurely",
            "newconnectionerror",
            "connecttimeouterror",
            "timed out",
            "read operation timed out",
            "the read operation timed out",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.CONNECTION,
            reason="Network connection could not be established or timed out",
            is_recoverable=False,
            friendly_message="Could not establish connection to the remote server.",
        )

    if any(
        m in lowered
        for m in (
            "certificate verify failed",
            "certificate_verify_failed",
            "self-signed certificate",
            "unable to get local issuer certificate",
            "ssl: handshake_failure",
            "sslv3_alert_handshake_failure",
            "tlsv1 alert",
            "sslerror",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.TLS,
            reason="TLS/SSL certificate validation or handshake failed",
            is_recoverable=False,
            friendly_message="Secure TLS connection to the server failed.",
        )

    # ------------------------------------------------------------------
    # Priority 6: DRM / authentic authentication locks
    # ------------------------------------------------------------------
    if any(
        m in lowered
        for m in (
            "drm protected",
            "protected by drm",
            "digital rights management",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.DRM,
            reason="Content is DRM-protected and cannot be decrypted",
            is_recoverable=False,
            friendly_message="This media is DRM-protected; VRKA will not bypass DRM.",
        )

    # Authentic authentication requirement (must NOT match bot challenges)
    if (
        any(
            m in lowered
            for m in (
                "this video is private",
                "private video. sign in",
                "sign in if you've been granted access",
                "this video is only available to registered users",
                "this video is only available to premium users",
                "invalid password",
                "account has been terminated",
                "login required to view this content",
            )
        )
        and "confirm you’re not a bot" not in lowered
        and "confirm you're not a bot" not in lowered
    ):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.AUTHENTICATION,
            reason="Content requires account credentials or is private",
            is_recoverable=False,
            friendly_message="This content requires account login credentials.",
        )

    # ------------------------------------------------------------------
    # Priority 7: Browser-recoverable extraction failures
    # (Direct extraction only, before transfer)
    # ------------------------------------------------------------------

    # 7A: Flashvars extraction failures (Android reference benchmark)
    if any(
        m in lowered
        for m in (
            "unable to extract flashvars",
            "flashvars not found",
            "could not find flashvars",
            "failed to extract flashvars",
            "none: flashvars",
        )
    ) or ("flashvars" in lowered and any(p in lowered for p in ("unable", "failed", "could not", "not found", "error"))):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.FLASHVARS,
            reason="Webpage uses flashvars player configuration requiring browser rendering",
            is_recoverable=True,
            friendly_message="Player configuration requires browser-assisted extraction.",
        )

    # 7B: KVS player extraction failures (requires player/extraction context)
    kvs_markers = ("kvs", "kt_player", "kvs_player", "kvsplayer", "kernel video sharing")
    has_kvs = any(m in lowered for m in kvs_markers)
    extraction_context = any(
        ctx in lowered
        for ctx in (
            "player",
            "flashvars",
            "extract",
            "failed",
            "unable",
            "could not",
            "config",
            "json",
            "license",
            "video_url",
            "playlist",
            "format",
        )
    )
    if has_kvs and extraction_context:
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.KVS_PLAYER,
            reason="Kernel Video Sharing (KVS) player requires browser rendering",
            is_recoverable=True,
            friendly_message="KVS player media requires browser-assisted extraction.",
        )

    # 7C: JSON parsing failure in player / manifest / config context
    has_json_error = any(
        m in lowered
        for m in (
            "failed to parse json",
            "unable to parse json",
            "jsondecodeerror",
            "could not parse json",
        )
    )
    json_player_context = any(
        ctx in lowered
        for ctx in (
            "player",
            "kvs",
            "generic",
            "webpage",
            "config",
            "manifest",
            "flashvars",
            "extract",
            "video",
            "data",
            "jwplayer",
            "videojs",
        )
    )
    if has_json_error and json_player_context:
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.PLAYER_EXTRACTION,
            reason="Player JSON configuration could not be parsed directly",
            is_recoverable=True,
            friendly_message="Media player data could not be parsed directly.",
        )

    # 7D: Client-side player extraction failures (requires player context)
    client_player_patterns = (
        "could not find js player",
        "unable to extract js player",
        "could not extract js player",
        "could not find player configuration",
        "unable to find player config",
        "player config not found",
        "player configuration not found",
        "could not find player",
        "unable to find player",
    )
    has_client_player_error = any(p in lowered for p in client_player_patterns)
    has_named_player_error = (
        any(np in lowered for np in ("jwplayer", "videojs", "flowplayer", "plyr"))
        and any(err in lowered for err in ("failed", "unable", "could not", "error", "extract", "not found"))
    )
    if has_client_player_error or has_named_player_error:
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.CLIENT_SIDE_PLAYER,
            reason="Client-side media player requires browser JavaScript execution",
            is_recoverable=True,
            friendly_message="Client-side media player requires browser execution.",
        )

    # 7E: Embedded player extraction failures
    if any(
        m in lowered
        for m in (
            "embedded player",
            "embedded video",
            "embedded iframe",
            "could not find embedded",
            "unable to extract embedded",
            "failed to extract embedded",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.EMBEDDED_PLAYER,
            reason="Embedded iframe or player was not directly resolvable",
            is_recoverable=True,
            friendly_message="Embedded media player requires browser observation.",
        )

    # 7F: Generic parser / stream extraction failures where webpage was reached
    generic_parser_patterns = (
        "unable to extract video url",
        "unable to extract media url",
        "unable to extract stream url",
        "unable to extract video data",
        "no video formats found",
        "no media formats found",
        "[generic] unable to extract",
        "[generic] none:",
    )
    if any(p in lowered for p in generic_parser_patterns):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.GENERIC_PARSER,
            reason="Direct parser could not extract media stream URLs from the page",
            is_recoverable=True,
            friendly_message="Media stream could not be extracted directly from webpage.",
        )

    # 7G: Webpage fetched successfully but generic extractor gave up on JS page
    fetched_page = any(m in lowered for m in _GENERIC_EXTRACTOR_FETCH_MARKERS)
    unsupported_or_no_video = any(
        m in lowered
        for m in (
            "unsupported url",
            "no suitable extractor",
            "there's no video in this url",
            "no video found",
        )
    )
    if fetched_page and unsupported_or_no_video:
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.PAGE_UNSUPPORTED,
            reason="Webpage loaded successfully but media requires client-side browser execution",
            is_recoverable=True,
            friendly_message="Webpage loaded but media requires browser execution.",
        )

    # 7H: Cloudflare / bot protection challenge on webpage
    if any(
        m in lowered
        for m in (
            "cloudflare",
            "cf-chl-",
            "just a moment...",
            "attention required",
            "turnstile",
            "ddos protection by cloudflare",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.CLOUDFLARE,
            reason="Site returned Cloudflare challenge during direct page fetch",
            is_recoverable=True,
            friendly_message="Website verification challenge detected.",
        )

    # 7I: Webpage cookie wall or anti-bot check
    if any(
        m in lowered
        for m in (
            "cookies-from-browser",
            "sign in to confirm you’re not a bot",
            "sign in to confirm you're not a bot",
            "could not find chrome cookie",
            "could not find edge cookie",
            "could not copy chrome cookie database",
            "could not copy edge cookie database",
            "database is locked",
            "failed to decrypt",
            "no useful cookies",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.COOKIE_WALL,
            reason="Site requires browser cookies or anti-bot verification session",
            is_recoverable=True,
            friendly_message="Site requires browser session or cookies.",
        )

    # 7J: Webpage-level HTTP block (403, 429, 503 during webpage fetch)
    webpage_block_markers = (
        "unable to download webpage",
        "403 forbidden",
        "http error 403",
        "http error 429",
        "429 too many requests",
        "http error 503",
        "503 service temporarily unavailable",
        "503 service unavailable",
    )
    if any(m in lowered for m in webpage_block_markers):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.HTTP_BLOCK,
            reason="Website blocked direct HTTP request; browser access may proceed",
            is_recoverable=True,
            friendly_message="Website rejected direct HTTP request.",
        )

    # 7K: Expired media address
    if any(
        m in lowered
        for m in (
            "url has expired",
            "expired url",
            "signature has expired",
        )
    ):
        return ClassificationResult(
            action=RecoveryAction.BROWSER_RECOVERABLE,
            category=FailureCategory.EXPIRED,
            reason="Media address has expired; fresh browser session required",
            is_recoverable=True,
            friendly_message="Media URL expired; new session required.",
        )

    # 7L: Prior category recovery (e.g. initial 403 led to unsupported retry)
    if prior_categories:
        recoverable_prior = {
            FailureCategory.CLOUDFLARE.value,
            FailureCategory.COOKIE_WALL.value,
            FailureCategory.HTTP_BLOCK.value,
            FailureCategory.EXPIRED.value,
            FailureCategory.FLASHVARS.value,
            FailureCategory.KVS_PLAYER.value,
            FailureCategory.PLAYER_EXTRACTION.value,
            FailureCategory.CLIENT_SIDE_PLAYER.value,
            FailureCategory.EMBEDDED_PLAYER.value,
            FailureCategory.GENERIC_PARSER.value,
            FailureCategory.PAGE_UNSUPPORTED.value,
        }
        if any(str(cat).lower() in recoverable_prior for cat in prior_categories):
            return ClassificationResult(
                action=RecoveryAction.BROWSER_RECOVERABLE,
                category=FailureCategory.PAGE_UNSUPPORTED,
                reason="Direct extraction retry followed an earlier browser-recoverable failure",
                is_recoverable=True,
                friendly_message="Direct extraction failed after recoverable error.",
            )

    # ------------------------------------------------------------------
    # Priority 8: Terminal Unsupported / Unknown
    # ------------------------------------------------------------------
    if any(m in lowered for m in ("unsupported url", "no suitable extractor")):
        return ClassificationResult(
            action=RecoveryAction.NON_BROWSER_RECOVERABLE,
            category=FailureCategory.UNSUPPORTED,
            reason="URL is not supported by yt-dlp and no page was fetched",
            is_recoverable=False,
            friendly_message="This address is not supported by yt-dlp.",
        )

    return ClassificationResult(
        action=RecoveryAction.NON_BROWSER_RECOVERABLE,
        category=FailureCategory.UNKNOWN,
        reason="Unclassified terminal failure",
        is_recoverable=False,
        friendly_message=str(output).strip() or "Download failed.",
    )


def is_browser_recoverable(
    exc_or_output: Any,
    *,
    stage: str = "",
    transferred: bool = False,
    is_cancelled: bool = False,
) -> bool:
    """Return True if an exception or output string represents a browser-recoverable failure."""
    if is_cancelled:
        return False

    output = ""
    prior: tuple[str, ...] = ()

    if isinstance(exc_or_output, str):
        output = exc_or_output
    else:
        output = str(getattr(exc_or_output, "output", "") or "")
        if not output:
            output = str(exc_or_output)
        prior = tuple(getattr(exc_or_output, "prior_categories", ()) or ())

    result = classify_failure(
        output,
        stage=stage,
        transferred=transferred,
        is_cancelled=is_cancelled,
        prior_categories=prior,
    )
    return result.is_recoverable
