"""Linux platform driver for VRKA."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from vrka_platform.base import PlatformDriver, ProcessLike
from vrka_platform.browser.base import BrowserVerificationDriver
from vrka_platform.browser.linux import LinuxBrowserDriver


class LinuxDriver(PlatformDriver):
    """Platform implementation for Linux (x86_64, aarch64)."""

    @property
    def name(self) -> str:
        return "linux"

    def get_local_cache_dir(self) -> Path:
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / "vrka"
        return Path.home() / ".cache" / "vrka"

    def get_subprocess_kwargs(self, hidden: bool = True) -> dict[str, Any]:
        return {}

    def format_command_for_logging(self, command: list[str]) -> str:
        return shlex.join(command)

    def terminate_process_tree(self, process: ProcessLike) -> None:
        if process.poll() is not None:
            return
        pid = int(process.pid)
        if pid <= 0:
            return
        import signal
        try:
            pgid = os.getpgid(pid)
            if pgid != os.getpid():
                os.killpg(pgid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except (subprocess.TimeoutExpired, Exception):
            try:
                pgid = os.getpgid(pid)
                if pgid != os.getpid():
                    os.killpg(pgid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
            process.kill()
            try:
                process.wait(timeout=2.0)
            except Exception:
                pass

    def open_path(self, path: str | Path) -> None:
        subprocess.Popen(["xdg-open", str(path)])

    def reveal_in_file_manager(self, path: str | Path) -> None:
        p = Path(path)
        folder = p.parent if p.is_file() else p
        subprocess.Popen(["xdg-open", str(folder)])

    def configure_app_identity(self, app_id: str) -> None:
        pass

    def register_custom_fonts(self, font_paths: list[Path]) -> bool:
        return False

    def get_binary_name(self, base_name: str) -> str:
        return base_name.removesuffix(".exe")

    def get_system_tool_search_paths(self) -> list[Path]:
        return [
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/bin"),
            Path.home() / ".local" / "bin",
        ]

    def get_ytdlp_platform_args(self) -> list[str]:
        return []

    def get_browser_verification_driver(self) -> BrowserVerificationDriver:
        return LinuxBrowserDriver()
