"""Regression test suite for release signature and manifest line-ending invariants.

Guarantees:
1. SHA256SUMS.txt contains LF (\n) line endings only; zero CRLF (\r\n) or CR (\r).
2. RELEASE-MANIFEST.json contains LF (\n) line endings only; zero CRLF (\r\n) or CR (\r).
3. Detached OpenPGP signatures verify directly against the EXACT un-normalized file bytes.
4. Tampering or converting bytes to CRLF fails closed (rejected by OpenPGP engine).
5. All four release packages verify authentic and unaltered against the signed manifests.
"""

from pathlib import Path
import unittest

from vrka_core.release_verifier import (
    TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
    TRUSTED_VRKA_RELEASE_KEY_PEM,
    verify_openpgp_signature,
    verify_release_artifact,
)

RELEASE_DIR = Path(__file__).resolve().parent.parent / "releases" / "VRKA-4.5.1-Build-019"
SHA256_FILE = RELEASE_DIR / "SHA256SUMS.txt"
SHA256_SIG_FILE = RELEASE_DIR / "SHA256SUMS.txt.asc"
MANIFEST_FILE = RELEASE_DIR / "RELEASE-MANIFEST.json"
MANIFEST_SIG_FILE = RELEASE_DIR / "RELEASE-MANIFEST.json.asc"

PACKAGES = [
    "VRKA-4.5.1-Build-019-Portable.exe",
    "VRKA-4.5.1-Build-019-Portable.zip",
    "VRKA-4.5.1-Build-019-Setup.exe",
    "VRKA-4.5.1-Build-019-Source.zip",
]


class TestReleaseLineEndingsAndSignatures(unittest.TestCase):
    """Enforces strict byte-exact line-ending and signature invariants for Build 019."""

    @classmethod
    def setUpClass(cls):
        if not RELEASE_DIR.is_dir():
            raise unittest.SkipTest(f"Release directory {RELEASE_DIR} does not exist.")

    def test_sha256sums_line_endings_lf_only(self):
        """SHA256SUMS.txt must contain LF line endings only (b'\r' strictly forbidden)."""
        self.assertTrue(SHA256_FILE.is_file(), f"Missing {SHA256_FILE}")
        raw_bytes = SHA256_FILE.read_bytes()
        self.assertNotIn(b"\r\n", raw_bytes, "SHA256SUMS.txt must not contain CRLF")
        self.assertNotIn(b"\r", raw_bytes, "SHA256SUMS.txt must not contain CR")
        self.assertTrue(raw_bytes.endswith(b"\n"), "SHA256SUMS.txt must end with LF")

    def test_release_manifest_line_endings_lf_only(self):
        """RELEASE-MANIFEST.json must contain LF line endings only (b'\r' strictly forbidden)."""
        self.assertTrue(MANIFEST_FILE.is_file(), f"Missing {MANIFEST_FILE}")
        raw_bytes = MANIFEST_FILE.read_bytes()
        self.assertNotIn(b"\r\n", raw_bytes, "RELEASE-MANIFEST.json must not contain CRLF")
        self.assertNotIn(b"\r", raw_bytes, "RELEASE-MANIFEST.json must not contain CR")
        self.assertTrue(raw_bytes.endswith(b"\n"), "RELEASE-MANIFEST.json must end with LF")

    def test_sha256sums_openpgp_exact_bytes_verification(self):
        """OpenPGP signature must verify directly on exact raw bytes without any normalization."""
        self.assertTrue(SHA256_FILE.is_file())
        self.assertTrue(SHA256_SIG_FILE.is_file())
        raw_bytes = SHA256_FILE.read_bytes()
        sig_text = SHA256_SIG_FILE.read_text(encoding="utf-8")

        res = verify_openpgp_signature(
            content=raw_bytes,
            signature=sig_text,
            trusted_pubkey_pem=TRUSTED_VRKA_RELEASE_KEY_PEM,
            expected_fingerprint=TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
        )
        self.assertTrue(res.is_valid, f"Verification failed on exact bytes: {res.error}")
        self.assertEqual(res.fingerprint, TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT)

    def test_release_manifest_openpgp_exact_bytes_verification(self):
        """OpenPGP signature must verify directly on exact raw bytes of RELEASE-MANIFEST.json."""
        self.assertTrue(MANIFEST_FILE.is_file())
        self.assertTrue(MANIFEST_SIG_FILE.is_file())
        raw_bytes = MANIFEST_FILE.read_bytes()
        sig_text = MANIFEST_SIG_FILE.read_text(encoding="utf-8")

        res = verify_openpgp_signature(
            content=raw_bytes,
            signature=sig_text,
            trusted_pubkey_pem=TRUSTED_VRKA_RELEASE_KEY_PEM,
            expected_fingerprint=TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
        )
        self.assertTrue(res.is_valid, f"Verification failed on exact bytes: {res.error}")
        self.assertEqual(res.fingerprint, TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT)

    def test_crlf_tampered_payload_fails_closed(self):
        """Verifier must reject payloads if CRLF is injected (proving fail-closed exact-byte behavior)."""
        raw_bytes = SHA256_FILE.read_bytes()
        sig_text = SHA256_SIG_FILE.read_text(encoding="utf-8")

        crlf_bytes = raw_bytes.replace(b"\n", b"\r\n")
        res = verify_openpgp_signature(
            content=crlf_bytes,
            signature=sig_text,
            trusted_pubkey_pem=TRUSTED_VRKA_RELEASE_KEY_PEM,
            expected_fingerprint=TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
        )
        self.assertFalse(res.is_valid, "Verifier must reject CRLF-tampered payload")
        self.assertIn("failed", res.error.lower())

    def test_all_four_packages_verified_against_exact_manifest(self):
        """All four release packages must pass integrity and authenticity checks via exact bytes."""
        manifest_bytes = MANIFEST_FILE.read_bytes()
        sig_text = MANIFEST_SIG_FILE.read_text(encoding="utf-8")

        for pkg_name in PACKAGES:
            pkg_path = RELEASE_DIR / pkg_name
            self.assertTrue(pkg_path.is_file(), f"Package missing: {pkg_name}")
            result = verify_release_artifact(
                artifact_path=pkg_path,
                manifest_content=manifest_bytes,
                signature_content=sig_text,
            )
            self.assertTrue(result.authenticated, f"Package {pkg_name} failed authenticity: {result.error}")
            self.assertTrue(result.integrity_ok, f"Package {pkg_name} failed integrity: {result.error}")
            self.assertEqual(result.signer_fingerprint, TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT)


if __name__ == "__main__":
    unittest.main()
