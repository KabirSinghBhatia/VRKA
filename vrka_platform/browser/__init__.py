"""Browser verification driver package."""

from __future__ import annotations

import sys
from typing import Any

from vrka_platform.browser.base import BrowserVerificationDriver
from vrka_platform.browser.cocoa_wkwebview import CocoaWKWebViewDriver
from vrka_platform.browser.linux import LinuxBrowserDriver
from vrka_platform.browser.webview2 import WebView2Driver

__all__ = [
    "BrowserVerificationDriver",
    "CocoaWKWebViewDriver",
    "LinuxBrowserDriver",
    "WebView2Driver",
    "create_browser_driver",
]


def create_browser_driver(**kwargs: Any) -> BrowserVerificationDriver:
    """Factory creating the appropriate BrowserVerificationDriver for current OS."""
    if sys.platform == "win32":
        return WebView2Driver(**kwargs)
    elif sys.platform == "darwin":
        return CocoaWKWebViewDriver()
    else:
        return LinuxBrowserDriver()
