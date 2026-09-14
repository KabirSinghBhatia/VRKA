"""Version consistency tests for VRKA 4.5."""

from pathlib import Path
import unittest
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None
import re


class VersionConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_pyproject_version_is_4_5(self):
        pyproject_path = self.repo_root / "pyproject.toml"
        self.assertTrue(pyproject_path.exists(), "pyproject.toml missing")
        if tomllib is not None:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            version = data.get("project", {}).get("version", "")
        else:
            content = pyproject_path.read_text(encoding="utf-8")
            match = re.search(r'(?m)^version\s*=\s*["\']([^"\']+)["\']', content)
            version = match.group(1) if match else ""
        self.assertTrue(version.startswith("4.5"), f"Expected 4.5.x in pyproject.toml, got {version}")

    def test_app_py_version_constants(self):
        from vrka_qml.app import APP_DISPLAY_VERSION, APP_BUILD
        self.assertEqual(APP_DISPLAY_VERSION, "4.5.1")
        self.assertEqual(APP_BUILD, "019")

    def test_vrka_downloader_version_constants(self):
        import vrka_downloader as vd
        self.assertEqual(vd.APP_DISPLAY_VERSION, "4.5.1")
        self.assertEqual(vd.APP_BUILD, "019")
        self.assertEqual(vd.APP_VERSION, "4.5.1")

    def test_about_version_display_string(self):
        from vrka_qml.app import APP_DISPLAY_VERSION
        about_str = "VRKA v" + APP_DISPLAY_VERSION
        self.assertEqual(about_str, "VRKA v4.5.1")

    def test_qml_settings_page_no_stale_version_literals(self):
        settings_qml = self.repo_root / "vrka_qml" / "qml" / "pages" / "SettingsPage.qml"
        self.assertTrue(settings_qml.exists(), "SettingsPage.qml missing")
        content = settings_qml.read_text(encoding="utf-8")

        # Stale literals must NOT exist
        self.assertNotIn("4.5.0 (Build 018)", content)
        self.assertNotIn("Build 018", content)
        self.assertNotIn("v4.5.0", content)
        self.assertNotIn('APP_DISPLAY_VERSION + ".0"', content)

        # Authoritative bindings MUST exist
        self.assertIn('APP_DISPLAY_VERSION + " (Build " + APP_BUILD + ")"', content)
        self.assertIn('"VRKA v" + APP_DISPLAY_VERSION', content)
        self.assertIn(': "Unknown"', content)

    def test_version_info_txt_constants(self):
        version_info = self.repo_root / "version_info.txt"
        self.assertTrue(version_info.exists(), "version_info.txt missing")
        content = version_info.read_text(encoding="utf-8")
        self.assertIn("filevers=(4, 5, 1, 19)", content)
        self.assertIn("prodvers=(4, 5, 1, 19)", content)
        self.assertIn("'FileVersion', '4.5.1.19'", content)
        self.assertIn("'ProductVersion', '4.5.1'", content)


if __name__ == "__main__":
    unittest.main()
