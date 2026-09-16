"""Abstract Base Classes for VRKA Platform Abstraction Layer.

Defines the contract for OS-specific operations including process execution,
desktop shell integration, font registration, binary tool discovery,
and browser verification engines.
"""

from __future__ import annotations

import abc
import os
import shlex
import stat
import subprocess
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class ProcessLike(Protocol):
    """Protocol for subprocess.Popen or mock process objects."""
    pid: int

    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...


class BrowserVerificationDriver(abc.ABC):
    """Abstract strategy for OS-specific browser fallback and security verification."""

    @abc.abstractmethod
    def prepare_environment(self) -> None:
        """Configure runtime environment settings (e.g., WebView2 runtime paths or extensions)."""
        pass

    @abc.abstractmethod
    def get_initial_url(self, start_url: str) -> str:
        """Return the initial URL to load into the verification window."""
        pass

    @abc.abstractmethod
    def install_security_guards(self, window: Any, popup_stats: dict[str, Any]) -> None:
        """Install native session guards, popup firewalls, or content filter delegates."""
        pass

    @abc.abstractmethod
    def navigate_to_target(self, window: Any, target_url: str) -> None:
        """Safely navigate the browser view to the target URL on the appropriate UI thread."""
        pass

    @abc.abstractmethod
    def start_media_capture(self, window: Any, result_path: Path, holder: dict[str, Any]) -> bool:
        """Attach native media body capture if supported by the engine."""
        pass

    def install_media_observer(
        self,
        window: Any,
        observation_callback: Callable[[dict[str, Any]], None],
        playable_callback: Callable[[str], None] | None = None,
    ) -> bool:
        """Install native or cross-frame media observer if supported by the platform engine."""
        return False

    def get_all_cookies(self, window: Any) -> list[dict[str, Any]] | None:
        """Extract all cookies across all domains from the browser datastore if supported."""
        return None


class PlatformDriver(abc.ABC):
    """Abstract strategy defining OS-specific operations across VRKA."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Canonical platform name ('windows', 'macos', 'linux')."""
        pass

    @property
    def is_windows(self) -> bool:
        return self.name == "windows"

    @property
    def is_macos(self) -> bool:
        return self.name == "macos"

    @property
    def is_linux(self) -> bool:
        return self.name == "linux"

    # --- Directories and Filesystem ---

    def get_app_data_dir(self) -> Path:
        """Return root user configuration directory (~/.vrka)."""
        return Path.home() / ".vrka"

    def get_local_cache_dir(self) -> Path:
        """Return local cache / runtime directory."""
        return self.get_app_data_dir()

    def ensure_executable(self, path: Path | str) -> None:
        """Ensure the specified file has executable permissions on POSIX systems."""
        p = Path(path)
        if not p.is_file():
            return
        try:
            current_mode = p.stat().st_mode
            p.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

    # --- Subprocesses & Commands ---

    def get_subprocess_kwargs(self, hidden: bool = True) -> dict[str, Any]:
        """Return kwargs suitable for subprocess.Popen / run."""
        return {}

    def format_command_for_logging(self, command: list[str]) -> str:
        """Format an argument list into a safe, platform-idiomatic command string."""
        return shlex.join(command)

    @abc.abstractmethod
    def terminate_process_tree(self, process: ProcessLike) -> None:
        """Cleanly terminate a running process and all its child processes."""
        pass

    # --- Desktop & Shell Integration ---

    @abc.abstractmethod
    def open_path(self, path: str | Path) -> None:
        """Open a file or folder using the default OS handler."""
        pass

    @abc.abstractmethod
    def reveal_in_file_manager(self, path: str | Path) -> None:
        """Reveal a file in the system file manager (Explorer, Finder, Nautilus)."""
        pass

    def configure_app_identity(self, app_id: str) -> None:
        """Configure OS application identity (AppUserModelID on Windows, Dock policy on macOS)."""
        pass

    def register_custom_fonts(self, font_paths: list[Path]) -> bool:
        """Dynamically register custom font files into the OS font table."""
        return False

    # --- CLI & Tool Resolution ---

    def get_binary_name(self, base_name: str) -> str:
        """Return platform executable filename."""
        return base_name

    def get_system_tool_search_paths(self) -> list[Path]:
        """Return standard directories where CLI tools (ffmpeg, aria2c, etc.) reside."""
        return []

    def get_ytdlp_platform_args(self) -> list[str]:
        """Return yt-dlp arguments required specifically for this platform."""
        return []

    # --- Browser Verification Strategy ---

    @abc.abstractmethod
    def get_browser_verification_driver(self) -> BrowserVerificationDriver:
        """Return browser verification driver for this platform."""
        pass
