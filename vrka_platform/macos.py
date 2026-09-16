"""macOS platform driver for VRKA."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from vrka_platform.base import PlatformDriver, ProcessLike
from vrka_platform.browser.base import BrowserVerificationDriver
from vrka_platform.browser.cocoa_wkwebview import CocoaWKWebViewDriver


class MacOSDriver(PlatformDriver):
    """Platform implementation for macOS (Apple Silicon arm64 & Intel x86_64)."""

    @property
    def name(self) -> str:
        return "macos"

    def get_local_cache_dir(self) -> Path:
        return self.get_app_data_dir()

    def get_subprocess_kwargs(self, hidden: bool = True) -> dict[str, Any]:
        # On POSIX, no special creationflags exist; subprocesess inherit stdio or pipe
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
        path_str = str(path)
        if path_str.startswith(("http://", "https://")):
            subprocess.Popen(["open", path_str])
            return

        p = Path(path_str)
        # Prevent LaunchServices errors when non-POSIX mock/windows paths are passed
        if not p.exists() and (":" in path_str or "\\" in path_str):
            return

        target = str(p.resolve()) if p.exists() else path_str
        subprocess.Popen(["open", target])

    def reveal_in_file_manager(self, path: str | Path) -> None:
        p = Path(path)
        if p.exists():
            subprocess.Popen(["open", "-R", str(p.resolve())])
        elif p.parent.exists():
            subprocess.Popen(["open", str(p.parent.resolve())])

    def configure_app_identity(self, app_id: str) -> None:
        try:
            from AppKit import NSApplication, NSApplicationActivationPolicyRegular
            app = NSApplication.sharedApplication()
            app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        except Exception:
            pass

    def register_custom_fonts(self, font_paths: list[Path]) -> bool:
        if not font_paths or not all(p.is_file() for p in font_paths):
            return False
        try:
            import ctypes
            core_foundation = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
            )
            core_text = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/CoreText.framework/CoreText"
            )
            make_url = core_foundation.CFURLCreateFromFileSystemRepresentation
            make_url.argtypes = (
                ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool,
            )
            make_url.restype = ctypes.c_void_p
            release = core_foundation.CFRelease
            release.argtypes = (ctypes.c_void_p,)
            register_url = core_text.CTFontManagerRegisterFontsForURL
            register_url.argtypes = (
                ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p),
            )
            register_url.restype = ctypes.c_bool

            results = []
            for path in font_paths:
                encoded = os.fsencode(str(path))
                url = make_url(None, encoded, len(encoded), False)
                if not url:
                    results.append(False)
                    continue
                error = ctypes.c_void_p()
                try:
                    results.append(bool(register_url(url, 1, ctypes.byref(error))))
                finally:
                    release(url)
            return all(results)
        except Exception:
            return False

    def get_binary_name(self, base_name: str) -> str:
        return base_name.removesuffix(".exe")

    def get_system_tool_search_paths(self) -> list[Path]:
        return [
            Path("/opt/homebrew/bin"),
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/bin"),
        ]

    def get_ytdlp_platform_args(self) -> list[str]:
        return []

    def get_browser_verification_driver(self) -> BrowserVerificationDriver:
        return CocoaWKWebViewDriver()
