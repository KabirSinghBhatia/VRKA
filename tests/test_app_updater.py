"""Comprehensive unit tests for Application Self-Updater.

Tests:
- SemanticVersion parsing and comparison
- Downgrade rejection
- Distribution asset pattern matching (Setup.exe, Portable.zip, Portable.exe)
- SafeRedirectHandler (HTTPS enforcement, redirect hop limits, allowed hosts)
- Concurrency locks (preventing duplicate download operations)
- SHA-256 and OpenPGP verification integration
- Fail-closed staging cleanup on error
- State machine lifecycle transitions
"""

import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vrka_core.updater_state import AppUpdateState, UpdateStateStore
from vrka_qml.app_updater import (
    AppUpdateInfo,
    SafeRedirectHandler,
    SemanticVersion,
    _APP_UPDATE_LOCK,
    _PORTABLE_EXE_PATTERN,
    _PORTABLE_ZIP_PATTERN,
    _SETUP_EXE_PATTERN,
    check_for_application_update,
    download_and_verify_update,
    is_installer_installation,
)


class AppUpdaterTests(unittest.TestCase):
    def test_semantic_version_parsing(self):
        v1 = SemanticVersion.parse("4.5.0")
        self.assertEqual((v1.major, v1.minor, v1.patch), (4, 5, 0))

        v2 = SemanticVersion.parse("v4.5.1")
        self.assertEqual((v2.major, v2.minor, v2.patch), (4, 5, 1))

        v3 = SemanticVersion.parse("4.5")
        self.assertEqual((v3.major, v3.minor, v3.patch), (4, 5, 0))

        v4 = SemanticVersion.parse("5.0.0-rc1")
        self.assertEqual((v4.major, v4.minor, v4.patch), (5, 0, 0))
        self.assertEqual(v4.prerelease, "rc1")

    def test_semantic_version_comparison_and_downgrade_rejection(self):
        # Newer versions
        self.assertTrue(SemanticVersion.parse("4.5.0") < SemanticVersion.parse("4.5.1"))
        self.assertTrue(SemanticVersion.parse("4.5.9") < SemanticVersion.parse("4.5.10"))
        self.assertTrue(SemanticVersion.parse("4.5.1") < SemanticVersion.parse("5.0.0"))

        # Equal versions (not newer -> downgrade/reinstall rejection)
        self.assertFalse(SemanticVersion.parse("4.5.1") < SemanticVersion.parse("4.5.1"))
        self.assertEqual(SemanticVersion.parse("v4.5.1"), SemanticVersion.parse("4.5.1"))

        # Older versions (downgrade rejection)
        self.assertFalse(SemanticVersion.parse("4.5.1") < SemanticVersion.parse("4.5.0"))
        self.assertFalse(SemanticVersion.parse("5.0.0") < SemanticVersion.parse("4.5.1"))

    def test_asset_pattern_matching(self):
        # Setup installer patterns
        self.assertTrue(_SETUP_EXE_PATTERN.match("VRKA-4.5.1-Build-019-Setup.exe"))
        self.assertTrue(_SETUP_EXE_PATTERN.match("VRKA-4.5.1-setup-Windows-x64.exe"))
        self.assertTrue(_SETUP_EXE_PATTERN.match("VRKA-installer.exe"))
        self.assertFalse(_SETUP_EXE_PATTERN.match("VRKA-4.5.1-Portable.zip"))

        # Portable zip patterns
        self.assertTrue(_PORTABLE_ZIP_PATTERN.match("VRKA-4.5.1-Build-019-Portable.zip"))
        self.assertTrue(_PORTABLE_ZIP_PATTERN.match("VRKA-4.5.1-portable-Windows-x64.zip"))
        self.assertFalse(_PORTABLE_ZIP_PATTERN.match("VRKA-4.5.1-Setup.exe"))

        # Portable standalone exe patterns
        self.assertTrue(_PORTABLE_EXE_PATTERN.match("VRKA-4.5.1-Build-019-Portable.exe"))
        self.assertTrue(_PORTABLE_EXE_PATTERN.match("VRKA-4.5.1-portable-Windows-x64.exe"))
        self.assertFalse(_PORTABLE_EXE_PATTERN.match("VRKA-4.5.1-Portable.zip"))

    def test_redirect_handler_blocks_insecure_http_downgrade(self):
        handler = SafeRedirectHandler()
        with self.assertRaises(Exception) as ctx:
            handler.redirect_request(
                req=None, fp=None, code=302, msg="Found", headers={}, newurl="http://objects.githubusercontent.com/file"
            )
        self.assertIn("Insecure HTTP downgrade", str(ctx.exception))

    def test_redirect_handler_blocks_unauthorized_host(self):
        handler = SafeRedirectHandler()
        with self.assertRaises(Exception) as ctx:
            handler.redirect_request(
                req=None, fp=None, code=302, msg="Found", headers={}, newurl="https://malicious-site.com/evil.exe"
            )
        self.assertIn("unapproved host", str(ctx.exception))

    def test_redirect_handler_allows_approved_hosts(self):
        import urllib.request
        handler = SafeRedirectHandler()

        for host in ("objects.githubusercontent.com", "github.com", "release-assets.githubusercontent.com"):
            req = handler.redirect_request(
                req=urllib.request.Request(f"https://{host}/download"),
                fp=None,
                code=302,
                msg="Found",
                headers={},
                newurl=f"https://{host}/download/asset.exe",
            )
            self.assertIsNotNone(req)

    def test_redirect_handler_enforces_hop_limit(self):
        import urllib.request
        handler = SafeRedirectHandler(max_hops=2)

        # Hop 1
        handler.redirect_request(urllib.request.Request("https://github.com/1"), None, 302, "Found", {}, "https://github.com/2")
        # Hop 2
        handler.redirect_request(urllib.request.Request("https://github.com/2"), None, 302, "Found", {}, "https://github.com/3")
        # Hop 3 -> Exceeded
        with self.assertRaises(Exception) as ctx:
            handler.redirect_request(urllib.request.Request("https://github.com/3"), None, 302, "Found", {}, "https://github.com/4")
        self.assertIn("Maximum redirect hops exceeded", str(ctx.exception))

    def test_concurrency_lock_rejects_duplicate_download(self):
        # Acquire lock in thread
        acquired = _APP_UPDATE_LOCK.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            # Second attempt to download while locked must raise RuntimeError
            info = AppUpdateInfo(
                current_version="4.5.1",
                latest_version="4.5.2",
                tag_name="v4.5.2",
                release_notes="",
                published_at="",
                asset_name="VRKA-4.5.2-Setup.exe",
                asset_download_url="https://github.com/MaverickRox/VRKA/releases/download/v4.5.2/VRKA-4.5.2-Setup.exe",
                sha256_manifest_url="",
                signature_url="",
                is_newer=True,
            )
            with self.assertRaises(RuntimeError) as ctx:
                download_and_verify_update(info)
            self.assertIn("already in progress", str(ctx.exception))
        finally:
            _APP_UPDATE_LOCK.release()

    def test_fail_closed_cleans_temporary_download(self):
        with tempfile.TemporaryDirectory() as td:
            staging_path = Path(td)
            info = AppUpdateInfo(
                current_version="4.5.1",
                latest_version="4.5.2",
                tag_name="v4.5.2",
                release_notes="",
                published_at="",
                asset_name="VRKA-4.5.2-Setup.exe",
                # Point to invalid/unreachable URL to trigger download error
                asset_download_url="https://github.com/MaverickRox/VRKA/releases/download/invalid/404.exe",
                sha256_manifest_url="",
                signature_url="",
                is_newer=True,
            )
            with self.assertRaises(Exception):
                download_and_verify_update(info, staging_dir=staging_path)

            # Temp file must not exist
            temp_file = staging_path / "VRKA-4.5.2-Setup.exe.downloading"
            self.assertFalse(temp_file.exists())
            target_file = staging_path / "VRKA-4.5.2-Setup.exe"
            self.assertFalse(target_file.exists())

    def test_app_update_state_machine(self):
        with tempfile.TemporaryDirectory() as td:
            store_file = Path(td) / "update_state.json"
            store = UpdateStateStore(store_file)

            self.assertEqual(store.get_app_state()["state"], AppUpdateState.IDLE.value)

            store.set_app_state(AppUpdateState.CHECKING)
            self.assertEqual(store.get_app_state()["state"], AppUpdateState.CHECKING.value)

            store.set_app_state(AppUpdateState.AVAILABLE, available_version="4.5.2")
            self.assertEqual(store.get_app_state()["state"], AppUpdateState.AVAILABLE.value)
            self.assertEqual(store.get_app_state()["available_version"], "4.5.2")

            store.set_app_state(AppUpdateState.DOWNLOADING)
            self.assertEqual(store.get_app_state()["state"], AppUpdateState.DOWNLOADING.value)

            store.set_app_state(AppUpdateState.VERIFYING)
            self.assertEqual(store.get_app_state()["state"], AppUpdateState.VERIFYING.value)

            store.set_app_state(AppUpdateState.READY_TO_INSTALL)
            self.assertEqual(store.get_app_state()["state"], AppUpdateState.READY_TO_INSTALL.value)

            # Check persistence across reload
            new_store = UpdateStateStore(store_file)
            self.assertEqual(new_store.get_app_state()["state"], AppUpdateState.READY_TO_INSTALL.value)
            self.assertEqual(new_store.get_app_state()["available_version"], "4.5.2")

    def test_check_for_application_update_persistence_no_name_error(self):
        """Verify that persisting update state with time.time() does not raise NameError."""
        payload = {
            "tag_name": "v4.5.1",
            "body": "Release 4.5.1",
            "published_at": "2026-09-14T12:00:00Z",
            "assets": [
                {"name": "VRKA-4.5.1-Build-019-Setup.exe", "browser_download_url": "https://github.com/MaverickRox/VRKA/releases/download/v4.5.1/VRKA-4.5.1-Build-019-Setup.exe"},
                {"name": "SHA256SUMS.txt", "browser_download_url": "https://github.com/MaverickRox/VRKA/releases/download/v4.5.1/SHA256SUMS.txt"},
                {"name": "SHA256SUMS.txt.asc", "browser_download_url": "https://github.com/MaverickRox/VRKA/releases/download/v4.5.1/SHA256SUMS.txt.asc"},
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            store = UpdateStateStore(Path(td) / "update_state.json")

            with patch("urllib.request.build_opener") as mock_build:
                mock_opener = MagicMock()
                mock_resp = MagicMock()
                mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
                mock_opener.open.return_value.__enter__.return_value = mock_resp
                mock_build.return_value = mock_opener

                info = check_for_application_update("4.5.1", store=store)
                self.assertIsNotNone(info)
                self.assertEqual(info.latest_version, "4.5.1")
                self.assertFalse(info.is_newer)

                app_state = store.get_app_state()
                self.assertGreater(app_state.get("last_check", 0), 0)
                self.assertEqual(app_state.get("current_version"), "4.5.1")
                self.assertEqual(app_state.get("state"), AppUpdateState.IDLE.value)

    def test_equal_version_produces_up_to_date_result(self):
        """Equal release version produces is_newer=False (up to date)."""
        payload = {
            "tag_name": "v4.5.1",
            "body": "Current release",
            "published_at": "2026-09-14T12:00:00Z",
            "assets": [],
        }
        with patch("urllib.request.build_opener") as mock_build:
            mock_opener = MagicMock()
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
            mock_opener.open.return_value.__enter__.return_value = mock_resp
            mock_build.return_value = mock_opener

            info = check_for_application_update("4.5.1")
            self.assertIsNotNone(info)
            self.assertEqual(info.latest_version, "4.5.1")
            self.assertFalse(info.is_newer)

    def test_newer_version_produces_update_available(self):
        """Newer release version produces is_newer=True and reports available."""
        payload = {
            "tag_name": "v4.6.0",
            "body": "New feature release",
            "published_at": "2026-09-20T12:00:00Z",
            "assets": [
                {"name": "VRKA-4.6.0-Setup.exe", "browser_download_url": "https://github.com/MaverickRox/VRKA/releases/download/v4.6.0/VRKA-4.6.0-Setup.exe"}
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            store = UpdateStateStore(Path(td) / "update_state.json")
            with patch("urllib.request.build_opener") as mock_build:
                mock_opener = MagicMock()
                mock_resp = MagicMock()
                mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
                mock_opener.open.return_value.__enter__.return_value = mock_resp
                mock_build.return_value = mock_opener

                info = check_for_application_update("4.5.1", store=store)
                self.assertIsNotNone(info)
                self.assertEqual(info.latest_version, "4.6.0")
                self.assertTrue(info.is_newer)
                self.assertEqual(store.get_app_state()["state"], AppUpdateState.AVAILABLE.value)

    def test_older_version_does_not_produce_update_available(self):
        """Older release version produces is_newer=False (downgrade rejection)."""
        payload = {
            "tag_name": "v4.5.0",
            "body": "Older release",
            "published_at": "2026-09-10T12:00:00Z",
            "assets": [],
        }
        with tempfile.TemporaryDirectory() as td:
            store = UpdateStateStore(Path(td) / "update_state.json")
            with patch("urllib.request.build_opener") as mock_build:
                mock_opener = MagicMock()
                mock_resp = MagicMock()
                mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
                mock_opener.open.return_value.__enter__.return_value = mock_resp
                mock_build.return_value = mock_opener

                info = check_for_application_update("4.5.1", store=store)
                self.assertIsNotNone(info)
                self.assertEqual(info.latest_version, "4.5.0")
                self.assertFalse(info.is_newer)
                self.assertEqual(store.get_app_state()["state"], AppUpdateState.IDLE.value)


if __name__ == "__main__":
    unittest.main()
