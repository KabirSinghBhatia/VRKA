"""Download submission presentation adapter for VRKA 4.5.

The single QML-facing entry point into the download workflow.
Validates input media URLs, custom HTTP headers, destination directory,
and video/audio quality options before submitting to the durable TaskScheduler.
"""

from __future__ import annotations

import os
import uuid

from PySide6.QtCore import Property, QObject, Signal, Slot

import vrka_downloader as app
from vrka_core.header_security import parse_custom_headers, validate_header_value
from vrka_core.quality_ranker import build_ytdlp_format_spec

DOWNLOAD_OPTION_DEFAULTS = {
    "quality": "Best Available",
    "fps60": True,
    "audio_format": "MP3",
    "mp3_bitrate": "320 kbps",
    "impersonation": "Automatic",
    "download_subs": False,
    "sub_langs": app.DEFAULT_SUBTITLE_LANGUAGE_PATTERN,
    "embed_subs": False,
    "auto_captions": False,
    "is_playlist": False,
    "playlist_start": "",
    "playlist_end": "",
    "trim_enabled": False,
    "start_time": "",
    "end_time": "",
    "referer": "",
    "origin": "",
    "custom_headers": {},
    "cookie_mode": "none",
    "cookie_browser": "Chrome",
    "cookie_profile": "",
    "cookie_file": "",
    "session_cookie_file": "",
    "session_media_candidates": [],
    "session_drm_detected": False,
    "session_user_agent": "",
    "session_referer": "",
    "session_origin": "",
    "session_page_title": "",
    "embed_thumbnail": False,
    "embed_metadata": False,
    "sponsorblock": False,
    "sponsorblock_categories": "",
    "proxy": "",
    "rate_limit": "",
    "force_ipv4": False,
    "restrict_filenames": False,
    "output_template": app.DEFAULT_OUTPUT_TEMPLATE,
    "use_archive": False,
    "format_sort": "",
    "allow_remote_components": False,
    "use_custom_command": False,
    "browser_fallback_enabled": True,
    "custom_command": "",
}

_DOWNLOAD_PAGE_MODES = ("video", "audio")


class DownloadController(QObject):
    submissionAccepted = Signal(str, str)  # task_id, url
    submissionFailed = Signal(str, str)  # short title, user-facing message
    outputFolderChanged = Signal()
    prefillRequested = Signal(str)  # url from history "Again" action

    def __init__(self, engine_host, settings_state=None, parent=None):
        super().__init__(parent)
        self._engine = engine_host
        self._settings = settings_state

    @Property(str, notify=outputFolderChanged)
    def outputFolder(self) -> str:
        return self._engine.output_folder

    @outputFolder.setter
    def outputFolder(self, value: str) -> None:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned == self._engine.output_folder:
            return
        self._engine.output_folder = cleaned
        self.outputFolderChanged.emit()

    @Slot(str, "QVariantMap", result=bool)
    def submitDownload(self, url: str, options) -> bool:
        """Validate and submit one download through the existing backend path."""
        use_custom = False
        custom_cmd = ""
        if self._settings is not None and bool(getattr(self._settings, "useCustomCommand", False)):
            custom_cmd = str(getattr(self._settings, "customCommand", "") or "").strip()
            if custom_cmd:
                import shlex
                try:
                    app.validate_custom_ytdlp_arguments(shlex.split(custom_cmd))
                except ValueError as exc:
                    self.submissionFailed.emit("Custom Command Is Not Allowed", str(exc))
                    return False
                use_custom = True
                mode = "custom"
            else:
                self.submissionFailed.emit(
                    "Custom Command Is Empty",
                    "Either enter yt-dlp arguments in the custom command box or turn off the custom-command checkbox.",
                )
                return False

        try:
            clean_url = app.validate_media_url(url)
            options = dict(options or {})
            if not use_custom:
                mode = str(options.get("mode", "video"))
                if mode not in _DOWNLOAD_PAGE_MODES:
                    raise ValueError("Choose video or audio mode.")
        except ValueError as exc:
            self.submissionFailed.emit("Check Download Settings", str(exc))
            return False

        # Validate Custom Headers & Network Security
        referer = str(options.get("referer", "")).strip()
        origin = str(options.get("origin", "")).strip()
        raw_headers = options.get("custom_headers", "")

        if referer and not validate_header_value(referer):
            self.submissionFailed.emit("Invalid Referer", "Referer header contains CRLF injection or invalid characters.")
            return False

        if origin and not validate_header_value(origin):
            self.submissionFailed.emit("Invalid Origin", "Origin header contains CRLF injection or invalid characters.")
            return False

        parsed_headers, header_errors = parse_custom_headers(raw_headers)
        if header_errors:
            self.submissionFailed.emit("Invalid Custom Header", header_errors[0])
            return False

        # Effective defaults
        if self._settings is not None:
            base = dict(DOWNLOAD_OPTION_DEFAULTS)
            base.update(self._settings.download_defaults())
        else:
            base = dict(DOWNLOAD_OPTION_DEFAULTS)
        merged = dict(base)
        for key, value in dict(options).items():
            if key in merged or key == "mode":
                merged[str(key)] = value
        merged.pop("mode", None)

        # Output Folder handling
        dest_override = str(options.get("output_folder", "")).strip()
        if dest_override and os.path.exists(dest_override):
            merged["output_folder"] = dest_override
        else:
            merged["output_folder"] = self._engine.output_folder

        # Apply validated network headers
        if referer:
            merged["referer"] = referer
        if origin:
            merged["origin"] = origin
        if parsed_headers:
            merged["custom_headers"] = parsed_headers

        # Apply video/audio quality format specifications
        if not use_custom:
            q_label = str(merged.get("quality", "Best Available"))
            p_fps60 = bool(merged.get("fps60", True))
            f_spec, s_crit = build_ytdlp_format_spec(mode, q_label, p_fps60)
            merged["format_selector"] = f_spec
            if not merged.get("format_sort"):
                merged["format_sort"] = s_crit

        if use_custom:
            merged["use_custom_command"] = True
            merged["custom_command"] = custom_cmd
            merged["browser_fallback_enabled"] = False
        else:
            merged["use_custom_command"] = False
            merged["custom_command"] = ""

        try:
            app.validate_output_template(merged.get("output_template", ""))
        except ValueError as exc:
            self.submissionFailed.emit("Check Download Settings", str(exc))
            return False

        task = app.DownloadTask(
            id=str(uuid.uuid4()), url=clean_url, mode=mode, options=merged,
        )
        try:
            self._engine.submit(task)
        except (RuntimeError, ValueError) as exc:
            self.submissionFailed.emit("Queue Unavailable", str(exc))
            return False

        self._engine.ui_queue.put(("log", f"Added to queue: {clean_url}"))
        self.submissionAccepted.emit(str(task.id), clean_url)
        if use_custom and self._settings is not None:
            try:
                self._settings.useCustomCommand = False
            except Exception:
                pass
        return True

    @Slot(str)
    def redownloadFromHistory(self, url: str) -> None:
        self.prefillRequested.emit(str(url))

    @Slot(result=str)
    def getClipboardText(self) -> str:
        from PySide6.QtGui import QGuiApplication
        cb = QGuiApplication.clipboard()
        if cb is not None:
            text = cb.text()
            return str(text or "").strip()
        return ""

    @Slot()
    def clearCompleted(self) -> None:
        if hasattr(self._engine, "_queue_controller") and self._engine._queue_controller:
            self._engine._queue_controller.clearCompleted()

    @Slot()
    def clearAllHistory(self) -> None:
        if hasattr(self._engine, "history"):
            self._engine.history = []
            if hasattr(self._engine, "save_history"):
                self._engine.save_history()
            if hasattr(self._engine, "ui_queue"):
                self._engine.ui_queue.put(("history_refresh", None))

    @Slot()
    def clearHistory(self) -> None:
        self.clearAllHistory()

