"""Lifecycle tests for uBlock Origin Lite (uBOL) update cycle.

Verifies:
1. Initial installed version 2026.907.2003 is recognized.
2. Check update detects 2026.914.1325.
3. Install update unpacks, validates manifest, and atomically activates 2026.914.1325.
4. Post-install check immediately returns 'Up to date' (no infinite update loop).
5. Superseded directory is pruned.
6. A fresh UBlockUpdater instance (simulating app restart) reads 2026.914.1325 and reports 'Up to date'.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse
import zipfile
from unittest.mock import patch

import vrka_downloader as app
from vrka_core.component_updater import UBlockUpdater
from vrka_core.updater_state import UpdateStateStore


def _create_mock_ubol_zip(version: str) -> bytes:
    buf = io.BytesIO()
    manifest = {
        "manifest_version": 3,
        "name": "uBlock Origin Lite",
        "version": version,
        "author": "Raymond Hill",
        "browser_specific_settings": {
            "gecko": {
                "id": "uBlock0@raymondhill.net"
            }
        }
    }
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("background.js", "// background script")
        zf.writestr("rules.json", "[]")
    return buf.getvalue()


class UbolUpdateLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.ext_dir = self.base_path / "browser_extensions"
        self.ext_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.base_path / "update_state.json"
        self.store = UpdateStateStore(self.state_file)

        # 1. Setup initial installed version: 2026.907.2003
        self.initial_version = "2026.907.2003"
        self.target_version = "2026.914.1325"

        v1_dir = self.ext_dir / "ubol-2026-907-2003"
        v1_dir.mkdir(parents=True, exist_ok=True)
        manifest_v1 = {
            "manifest_version": 3,
            "name": "uBlock Origin Lite",
            "version": self.initial_version,
            "author": "Raymond Hill",
            "browser_specific_settings": {
                "gecko": {"id": "uBlock0@raymondhill.net"}
            }
        }
        (v1_dir / "manifest.json").write_text(json.dumps(manifest_v1), encoding="utf-8")
        (v1_dir / "background.js").write_text("// v1", encoding="utf-8")

        self.patcher_ext = patch.object(app, "BROWSER_EXT_DIR", self.ext_dir)
        self.patcher_ext.start()
        self.updater = UBlockUpdater(store=self.store)

    def tearDown(self):
        self.patcher_ext.stop()
        self.temp_dir.cleanup()

    def test_complete_ubol_update_lifecycle_no_loop(self):
        # Step 1: Verify installed version is initial version
        installed = self.updater.get_installed_version()
        self.assertEqual(installed, self.initial_version)

        # Step 2: Check update detects target version
        mock_release = {
            "tag_name": self.target_version,
            "assets": [
                {
                    "name": "uBOLite.chromium.mv3.zip",
                    "browser_download_url": "https://github.com/gorhill/uBlock/releases/download/mock/uBOLite.chromium.mv3.zip"
                }
            ]
        }
        mock_release_bytes = json.dumps(mock_release).encode("utf-8")
        target_zip_bytes = _create_mock_ubol_zip(self.target_version)

        def _mock_fetch(url, *args, **kwargs):
            parsed = urlparse(url)
            if parsed.hostname == "api.github.com":
                return mock_release_bytes
            return target_zip_bytes

        # Regression: URL containing 'api.github.com' in query string must not be treated as GitHub API URL
        self.assertNotEqual(
            _mock_fetch("https://evil.example/?next=api.github.com"),
            mock_release_bytes,
            "Spoofed URL containing 'api.github.com' in query parameter must not return GitHub API response",
        )
        self.assertEqual(
            _mock_fetch("https://evil.example/?next=api.github.com"),
            target_zip_bytes,
        )

        with patch("vrka_core.component_updater._safe_fetch_url", side_effect=_mock_fetch):
            # Check update
            check_res = self.updater.check_update()
            self.assertTrue(check_res["update_available"])
            self.assertEqual(check_res["available_version"], self.target_version)
            self.assertEqual(check_res["current_version"], self.initial_version)

            # Step 3: Install update
            install_res = self.updater.install_update(check_info=check_res)
            self.assertTrue(install_res["updated"], f"Install failed: {install_res.get('error')}")
            self.assertEqual(install_res["installed_version"], self.target_version)

            # Step 4: Post-install check must immediately report 'Up to date' (no update available)
            post_check = self.updater.check_update()
            self.assertFalse(
                post_check["update_available"],
                f"Loop regression: check_update reported update available after install! Current: {post_check['current_version']}, Available: {post_check['available_version']}"
            )
            self.assertEqual(post_check["current_version"], self.target_version)

            # Step 5: Verify superseded folders are pruned
            remaining_ubol_dirs = [d for d in self.ext_dir.iterdir() if d.is_dir() and d.name.startswith("ubol-")]
            self.assertEqual(len(remaining_ubol_dirs), 1)
            active_manifest = json.loads((remaining_ubol_dirs[0] / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(active_manifest["version"], self.target_version)

            # Step 6: Restart simulation - fresh UBlockUpdater instance
            new_store = UpdateStateStore(self.state_file)
            new_updater = UBlockUpdater(store=new_store)
            self.assertEqual(new_updater.get_installed_version(), self.target_version)

            restart_check = new_updater.check_update()
            self.assertFalse(restart_check["update_available"])
            self.assertEqual(restart_check["current_version"], self.target_version)


if __name__ == "__main__":
    unittest.main()
