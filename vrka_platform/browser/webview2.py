"""Windows WebView2 browser verification driver.

Encapsulates EdgeChromium / WebView2 specific behavior including runtime
detection, uBlock Origin Lite extension installation via .NET reflection,
WinForms UI-thread invocation, and native MediaBodyCapture attachment.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any

from vrka_platform.browser.base import BrowserVerificationDriver


def find_webview2_runtime_folder() -> str | None:
    """Locate an installed WebView2 runtime folder when registry detection misses it."""
    if os.name != "nt":
        return None
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(os.path.join(
            local_app_data, "Microsoft", "EdgeUpdate", "CustomInstall", "EdgeWebView"
        ))
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(os.path.join(
            program_files, "Microsoft", "EdgeWebView", "Application"
        ))
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidates.append(os.path.join(
            program_files_x86, "Microsoft", "EdgeWebView", "Application"
        ))
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidates.append(os.path.join(system_root, "System32", "Microsoft-Edge-WebView"))

    for folder in candidates:
        if folder and os.path.isfile(os.path.join(folder, "msedgewebview2.exe")):
            return folder
    return None


class WebView2Driver(BrowserVerificationDriver):
    """Browser verification driver using Microsoft Edge WebView2 on Windows."""

    def __init__(self, ubol_dir: Path | str | None = None, observer_dir: Path | str | None = None) -> None:
        self.ubol_dir = str(ubol_dir) if ubol_dir else None
        self.observer_dir = str(observer_dir) if observer_dir else None
        self.ubol_ready = threading.Event()

    def prepare_environment(self) -> None:
        """Configure pywebview settings and patch for extension support."""
        try:
            import webview
            if not webview.settings.get("WEBVIEW2_RUNTIME_PATH"):
                runtime_folder = find_webview2_runtime_folder()
                if runtime_folder:
                    webview.settings["WEBVIEW2_RUNTIME_PATH"] = runtime_folder
        except Exception:
            pass

    def get_initial_url(self, start_url: str) -> str:
        """Windows starts on about:blank until uBOL and session guards are installed."""
        return "about:blank"

    def install_security_guards(self, window: Any, popup_stats: dict[str, Any]) -> None:
        """Install WebView2 session guard, new window blocker, and uBOL extension."""
        if popup_stats.get("native_guard_installed"):
            return

        def _worker():
            deadline = time.time() + 90
            while time.time() < deadline:
                try:
                    browser_view = getattr(window, "gui", None)
                    if browser_view and hasattr(browser_view, "BrowserView"):
                        view_instance = browser_view.BrowserView.instances.get(window.uid)
                    else:
                        view_instance = None

                    if view_instance is not None and getattr(view_instance, "browser", None):
                        browser = view_instance.browser
                        if getattr(browser, "webview", None) and getattr(browser.webview, "CoreWebView2", None):
                            self._install_on_core(browser, view_instance, popup_stats)
                            return
                except Exception:
                    pass
                time.sleep(0.05)
            self.ubol_ready.set()

        threading.Thread(target=_worker, name="vrka-webview2-guard", daemon=True).start()

    def _install_on_core(self, browser: Any, browser_view: Any, popup_stats: dict[str, Any]) -> None:
        """Perform installation on the CoreWebView2 object via UI thread."""
        try:
            from System import Action

            def _on_ui():
                try:
                    core = browser.webview.CoreWebView2

                    def handle_new_window(sender, args):
                        args.set_Handled(True)
                        try:
                            uri = str(getattr(args, "Uri", "") or "")
                            if not uri and hasattr(args, "get_Uri"):
                                uri = str(args.get_Uri() or "")
                            popup_stats.setdefault("blocked_urls", []).append(uri)
                            popup_stats["blocked"] = popup_stats.get("blocked", 0) + 1
                        except Exception:
                            popup_stats["blocked"] = popup_stats.get("blocked", 0) + 1

                    try:
                        core.NewWindowRequested -= browser.on_new_window_request
                    except Exception:
                        pass
                    browser._vrka_popup_handler = handle_new_window
                    core.NewWindowRequested += browser._vrka_popup_handler
                    popup_stats["native_guard_installed"] = True

                    # Install uBOL if present
                    if self.ubol_dir:
                        try:
                            ext_task = core.Profile.AddBrowserExtensionAsync(self.ubol_dir)

                            def _ubol_done(task):
                                self.ubol_ready.set()

                            from System import Action as NetAction
                            from System.Threading.Tasks import Task as NetTask
                            from Microsoft.Web.WebView2.Core import CoreWebView2BrowserExtension
                            ext_task.ContinueWith(NetAction[NetTask[CoreWebView2BrowserExtension]](_ubol_done))
                        except Exception:
                            self.ubol_ready.set()
                    else:
                        self.ubol_ready.set()
                except Exception as exc:
                    popup_stats["guard_error"] = str(exc)
                    self.ubol_ready.set()

            if getattr(browser_view, "InvokeRequired", False):
                browser_view.Invoke(Action(_on_ui))
            else:
                _on_ui()
        except Exception as exc:
            popup_stats["guard_error"] = str(exc)
            self.ubol_ready.set()

    def navigate_to_target(self, window: Any, target_url: str) -> None:
        """Safely navigate to requested page using UI thread invoke."""
        try:
            browser_view = getattr(window, "gui", None)
            view_instance = None
            if browser_view and hasattr(browser_view, "BrowserView"):
                view_instance = browser_view.BrowserView.instances.get(window.uid)

            if view_instance is not None and getattr(view_instance, "InvokeRequired", False):
                from System import Action

                def _go():
                    try:
                        window.load_url(target_url)
                    except Exception:
                        pass

                view_instance.Invoke(Action(_go))
            else:
                window.load_url(target_url)
        except Exception:
            try:
                window.load_url(target_url)
            except Exception:
                pass

    def start_media_capture(self, window: Any, result_path: Path, holder: dict[str, Any]) -> bool:
        """Attach native media body capture on Windows CoreWebView2."""
        try:
            from System import Action
            from vrka_core.browser_capture import MediaBodyCapture

            browser_view = getattr(window, "gui", None)
            view_instance = None
            if browser_view and hasattr(browser_view, "BrowserView"):
                view_instance = browser_view.BrowserView.instances.get(window.uid)

            if view_instance is None:
                holder["error"] = "browser view unavailable"
                return False

            objects_dir = result_path.parent / ("media-objects-" + result_path.stem.replace("browser-", ""))
            temp_holder = {"capture": None, "error": ""}

            def _attach():
                try:
                    browser = view_instance.browser
                    if not browser or not browser.webview or not browser.webview.CoreWebView2:
                        temp_holder["error"] = "CoreWebView2 not ready"
                        return
                    capture = MediaBodyCapture(browser.webview.CoreWebView2, objects_dir)
                    if capture.attach():
                        temp_holder["capture"] = capture
                    else:
                        temp_holder["error"] = "attach failed"
                except Exception as exc:
                    temp_holder["error"] = str(exc)

            if getattr(view_instance, "InvokeRequired", False):
                view_instance.Invoke(Action(_attach))
            else:
                _attach()

            if temp_holder["capture"] is not None:
                holder["capture"] = temp_holder["capture"]
                return True
            holder["error"] = temp_holder["error"] or "capture initialization failed"
            return False
        except Exception as exc:
            holder["error"] = str(exc)
            return False
