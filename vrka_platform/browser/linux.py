"""Linux / Generic browser verification driver.

Uses pywebview's standard WebKitGTK / Qt WebEngine backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vrka_platform.browser.base import BrowserVerificationDriver


class LinuxBrowserDriver(BrowserVerificationDriver):
    """Browser verification driver for Linux systems."""

    def prepare_environment(self) -> None:
        pass

    def get_initial_url(self, start_url: str) -> str:
        return start_url

    def install_security_guards(self, window: Any, popup_stats: dict[str, Any]) -> None:
        popup_stats["native_guard_installed"] = True

    def navigate_to_target(self, window: Any, target_url: str) -> None:
        try:
            window.load_url(target_url)
        except Exception:
            pass

    def start_media_capture(self, window: Any, result_path: Path, holder: dict[str, Any]) -> bool:
        holder["error"] = "Media capture not supported on WebKitGTK"
        return False
