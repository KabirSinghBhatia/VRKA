"""Unit tests for the vrka_platform abstraction layer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import vrka_platform
from vrka_platform import (
    LinuxDriver,
    MacOSDriver,
    PlatformDriver,
    WindowsDriver,
    get_platform_driver,
    set_platform_driver,
)
from vrka_platform.browser import create_browser_driver
from vrka_platform.browser.cocoa_wkwebview import CocoaWKWebViewDriver
from vrka_platform.browser.linux import LinuxBrowserDriver
from vrka_platform.browser.webview2 import WebView2Driver


class TestVrkaPlatform(unittest.TestCase):
    def setUp(self):
        # Save original driver
        self.original_driver = vrka_platform._CURRENT_PLATFORM_DRIVER

    def tearDown(self):
        # Restore original driver
        vrka_platform.set_platform_driver(self.original_driver)

    def test_get_platform_driver_returns_appropriate_driver(self):
        set_platform_driver(None)
        driver = get_platform_driver()
        self.assertIsInstance(driver, PlatformDriver)
        if sys.platform == "win32":
            self.assertEqual(driver.name, "windows")
            self.assertTrue(driver.is_windows)
        elif sys.platform == "darwin":
            self.assertEqual(driver.name, "macos")
            self.assertTrue(driver.is_macos)
        else:
            self.assertEqual(driver.name, "linux")
            self.assertTrue(driver.is_linux)

    def test_set_platform_driver_override(self):
        mock_driver = MagicMock(spec=PlatformDriver)
        mock_driver.name = "mock_os"
        set_platform_driver(mock_driver)
        self.assertEqual(get_platform_driver().name, "mock_os")

    def test_windows_driver_behaviors(self):
        win = WindowsDriver()
        self.assertEqual(win.name, "windows")
        self.assertTrue(win.is_windows)
        self.assertFalse(win.is_macos)
        self.assertFalse(win.is_linux)

        # Binary naming
        self.assertEqual(win.get_binary_name("ffmpeg"), "ffmpeg.exe")
        self.assertEqual(win.get_binary_name("aria2c.exe"), "aria2c.exe")

        # Command formatting (Windows list2cmdline)
        cmd = ["echo", "hello world", "with quotes\""]
        self.assertIn("hello world", win.format_command_for_logging(cmd))

        # Subprocess kwargs
        kwargs = win.get_subprocess_kwargs(hidden=True)
        self.assertIn("creationflags", kwargs)
        self.assertEqual(win.get_subprocess_kwargs(hidden=False), {})

        # yt-dlp args
        self.assertIn("--windows-filenames", win.get_ytdlp_platform_args())

        # Browser driver
        browser_driver = win.get_browser_verification_driver()
        self.assertIsInstance(browser_driver, WebView2Driver)
        self.assertEqual(browser_driver.get_initial_url("https://example.com"), "about:blank")

    def test_macos_driver_behaviors(self):
        mac = MacOSDriver()
        self.assertEqual(mac.name, "macos")
        self.assertTrue(mac.is_macos)
        self.assertFalse(mac.is_windows)

        # Binary naming
        self.assertEqual(mac.get_binary_name("ffmpeg"), "ffmpeg")
        self.assertEqual(mac.get_binary_name("ffmpeg.exe"), "ffmpeg")

        # Command formatting (POSIX shlex.join)
        cmd = ["echo", "hello world"]
        self.assertEqual(mac.format_command_for_logging(cmd), "echo 'hello world'")

        # Subprocess kwargs
        self.assertEqual(mac.get_subprocess_kwargs(hidden=True), {})

        # Tool search paths
        paths = mac.get_system_tool_search_paths()
        self.assertIn(Path("/opt/homebrew/bin"), paths)
        self.assertIn(Path("/usr/local/bin"), paths)

        # Browser driver
        browser_driver = mac.get_browser_verification_driver()
        self.assertIsInstance(browser_driver, CocoaWKWebViewDriver)
        self.assertEqual(browser_driver.get_initial_url("https://example.com"), "https://example.com")
        self.assertTrue(callable(browser_driver.install_media_observer))
        self.assertTrue(callable(browser_driver.get_all_cookies))
        self.assertIsNone(browser_driver.get_all_cookies(None))

    def test_linux_driver_behaviors(self):
        lin = LinuxDriver()
        self.assertEqual(lin.name, "linux")
        self.assertTrue(lin.is_linux)
        self.assertFalse(lin.is_windows)

        # Binary naming
        self.assertEqual(lin.get_binary_name("deno"), "deno")
        self.assertEqual(lin.get_binary_name("deno.exe"), "deno")

        # Browser driver
        browser_driver = lin.get_browser_verification_driver()
        self.assertIsInstance(browser_driver, LinuxBrowserDriver)
        self.assertFalse(browser_driver.install_media_observer(None, lambda x: None))
        self.assertIsNone(browser_driver.get_all_cookies(None))

    def test_create_browser_driver_factory(self):
        driver = create_browser_driver()
        if sys.platform == "win32":
            self.assertIsInstance(driver, WebView2Driver)
        elif sys.platform == "darwin":
            self.assertIsInstance(driver, CocoaWKWebViewDriver)
        else:
            self.assertIsInstance(driver, LinuxBrowserDriver)

    def test_browser_cookie_rows_dict_handling(self):
        from vrka_downloader import _browser_cookie_rows

        dict_cookies = [
            {
                "name": "session_id",
                "value": "xyz123",
                "domain": ".vixcloud.co",
                "path": "/playlist",
                "secure": True,
                "expires": 1794741555,
            },
            {
                "name": "token",
                "value": "tok_456",
                "domain": "",
                "path": "/",
                "secure": False,
            }
        ]
        rows = _browser_cookie_rows(dict_cookies, "https://streamingunity.vip/watch")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "session_id")
        self.assertEqual(rows[0]["domain"], ".vixcloud.co")
        self.assertTrue(rows[0]["include_subdomains"])
        self.assertTrue(rows[0]["secure"])
        self.assertEqual(rows[0]["expires"], 1794741555)
        # Second cookie uses fallback domain from page_url
        self.assertEqual(rows[1]["name"], "token")
        self.assertEqual(rows[1]["domain"], "streamingunity.vip")
        self.assertFalse(rows[1]["include_subdomains"])


if __name__ == "__main__":
    unittest.main()
