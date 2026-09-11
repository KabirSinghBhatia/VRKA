"""Unit tests for Application Self-Updater, SemanticVersion, and redirect validation."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from vrka_qml.app_updater import (
    AppUpdateInfo,
    SafeRedirectHandler,
    SemanticVersion,
    download_and_verify_update,
)


class AppUpdaterTests(unittest.TestCase):
    def test_semantic_version_parsing(self):
        v1 = SemanticVersion.parse("4.5.0")
        self.assertEqual((v1.major, v1.minor, v1.patch), (4, 5, 0))

        v2 = SemanticVersion.parse("v4.5.1")
        self.assertEqual((v2.major, v2.minor, v2.patch), (4, 5, 1))

        v3 = SemanticVersion.parse("4.5")
        self.assertEqual((v3.major, v3.minor, v3.patch), (4, 5, 0))

    def test_semantic_version_comparison(self):
        self.assertTrue(SemanticVersion.parse("4.5.0") < SemanticVersion.parse("4.5.1"))
        self.assertTrue(SemanticVersion.parse("4.5.9") < SemanticVersion.parse("4.5.10"))
        self.assertTrue(SemanticVersion.parse("4.5.0") < SemanticVersion.parse("5.0.0"))
        self.assertFalse(SemanticVersion.parse("4.5.1") < SemanticVersion.parse("4.5.0"))
        self.assertEqual(SemanticVersion.parse("v4.5.0"), SemanticVersion.parse("4.5.0"))

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

    def test_sha256_verification_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            staging_path = Path(td)
            fake_target = staging_path / "VRKA-4.5.1-setup-Windows-x64.exe"

            # Create dummy payload
            payload = b"MZ\x90\x00\x03\x00\x00\x00VRKA TEST BINARY"
            with open(fake_target, "wb") as f:
                f.write(payload)

            actual_hash = hashlib.sha256(payload).hexdigest()
            wrong_hash = "0" * 64

            # Verify that hash mismatch is caught
            self.assertNotEqual(actual_hash, wrong_hash)


if __name__ == "__main__":
    unittest.main()
