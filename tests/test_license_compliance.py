"""Automated unit tests for open-source license compliance and third-party notices."""

from pathlib import Path
import subprocess
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LICENSES_DIR = PROJECT_ROOT / "LICENSES"
NOTICES_FILE = PROJECT_ROOT / "THIRD_PARTY_NOTICES.md"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


class LicenseComplianceTests(unittest.TestCase):
    """Verify that all distributed dependencies and assets comply with open-source licensing."""

    def setUp(self):
        self.assertTrue(NOTICES_FILE.is_file(), "THIRD_PARTY_NOTICES.md must exist in the project root")
        self.assertTrue(LICENSES_DIR.is_dir(), "LICENSES/ directory must exist in the project root")
        self.notices_text = NOTICES_FILE.read_text(encoding="utf-8")

    def test_requirements_covered_in_notices(self):
        """Every core dependency in requirements.txt must be documented in THIRD_PARTY_NOTICES.md."""
        self.assertTrue(REQUIREMENTS_FILE.is_file(), "requirements.txt must exist")
        for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Extract package name (before ==, >=, [, etc.)
            pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip()
            # Normalize names
            norm_name = pkg_name.replace("_", "-").lower()
            self.assertIn(
                norm_name,
                self.notices_text.lower().replace("_", "-"),
                f"Required dependency '{pkg_name}' must be documented in THIRD_PARTY_NOTICES.md",
            )

    def test_spdx_canonical_templates_exist(self):
        """All canonical SPDX license text templates must exist in LICENSES/ with non-trivial size."""
        required_templates = [
            "GPL-3.0-or-later.txt",
            "GPL-2.0-or-later.txt",
            "LGPL-3.0-only.txt",
            "LGPL-2.1-or-later.txt",
            "MIT.txt",
            "Apache-2.0.txt",
            "BSD-3-Clause.txt",
            "OFL-1.1.txt",
            "MPL-2.0.txt",
            "PSF-2.0.txt",
            "Unlicense.txt",
        ]
        for t_name in required_templates:
            target = LICENSES_DIR / t_name
            self.assertTrue(target.is_file(), f"Canonical SPDX template '{t_name}' missing in LICENSES/")
            self.assertGreater(target.stat().st_size, 100, f"Template '{t_name}' is unexpectedly small")

    def test_embedded_assets_have_licenses(self):
        """Non-Python embedded components must have valid local license texts."""
        # Space Mono font OFL
        ofl_file = PROJECT_ROOT / "assets" / "fonts" / "OFL.txt"
        self.assertTrue(ofl_file.is_file(), "Space Mono OFL.txt license missing")
        self.assertIn("SIL OPEN FONT LICENSE", ofl_file.read_text(encoding="utf-8"))

        # puemos/hls-downloader MIT license
        puemos_license = PROJECT_ROOT / "third_party" / "media_observer" / "puemos-hls-downloader" / "LICENSE"
        self.assertTrue(puemos_license.is_file(), "puemos/hls-downloader LICENSE missing")
        self.assertIn("Shy Alter", puemos_license.read_text(encoding="utf-8"))

    def test_ffmpeg_attributed_as_unbundled_external_tool(self):
        """FFmpeg and FFprobe must be documented as unbundled external tools referencing FFMPEG_COMPLIANCE.md."""
        self.assertIn("FFmpeg & FFprobe", self.notices_text)
        self.assertIn("unbundled", self.notices_text.lower())
        self.assertIn("FFMPEG_COMPLIANCE.md", self.notices_text)

    def test_manifest_json_consistency(self):
        """LICENSES/manifest.json must exist and be valid JSON containing packages and external tools."""
        import json
        manifest_file = LICENSES_DIR / "manifest.json"
        self.assertTrue(manifest_file.is_file(), "LICENSES/manifest.json must exist")
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(data.get("application"), "VRKA")
        self.assertIn("packages", data)
        self.assertIn("embedded_assets", data)
        self.assertIn("external_tools", data)

    def test_collector_tool_check_passes(self):
        """Running tools/collect_licenses.py --check must return exit code 0."""
        collector_script = PROJECT_ROOT / "tools" / "collect_licenses.py"
        self.assertTrue(collector_script.is_file(), "tools/collect_licenses.py must exist")
        res = subprocess.run(
            [sys.executable, str(collector_script), "--check"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"License check failed:\n{res.stdout}\n{res.stderr}")


if __name__ == "__main__":
    unittest.main()
