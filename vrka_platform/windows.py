"""Windows platform driver for VRKA."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from vrka_platform.base import PlatformDriver, ProcessLike
from vrka_platform.browser.base import BrowserVerificationDriver
from vrka_platform.browser.webview2 import WebView2Driver


class WindowsDriver(PlatformDriver):
    """Platform implementation for Windows (10, 11, Server)."""

    @property
    def name(self) -> str:
        return "windows"

    def get_local_cache_dir(self) -> Path:
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            return Path(local_app)
        return Path.home() / "AppData" / "Local"

    def get_subprocess_kwargs(self, hidden: bool = True) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if hidden:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        return kwargs

    def format_command_for_logging(self, command: list[str]) -> str:
        return subprocess.list2cmdline(command)

    def terminate_process_tree(self, process: ProcessLike) -> None:
        if process.poll() is not None:
            return
        pid = int(process.pid)
        if pid <= 0:
            return
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass

    def open_path(self, path: str | Path) -> None:
        try:
            os.startfile(str(path))
        except Exception:
            subprocess.Popen(["explorer.exe", str(path)])

    def reveal_in_file_manager(self, path: str | Path) -> None:
        subprocess.Popen(["explorer.exe", f"/select,{str(path)}"])

    def configure_app_identity(self, app_id: str) -> None:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    def register_custom_fonts(self, font_paths: list[Path]) -> bool:
        if not font_paths or not all(p.is_file() for p in font_paths):
            return False
        try:
            import ctypes
            add_font = ctypes.windll.gdi32.AddFontResourceExW
            add_font.argtypes = (ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p)
            add_font.restype = ctypes.c_int
            return all(add_font(str(p), 0x10, None) > 0 for p in font_paths)
        except Exception:
            return False

    def get_binary_name(self, base_name: str) -> str:
        return f"{base_name}.exe" if not base_name.endswith(".exe") else base_name

    def get_system_tool_search_paths(self) -> list[Path]:
        paths = []
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            paths.append(Path(local_app) / "Programs")
        return paths

    def get_ytdlp_platform_args(self) -> list[str]:
        return ["--windows-filenames"]

    def get_browser_verification_driver(self) -> BrowserVerificationDriver:
        return WebView2Driver()
