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


if __name__ == "__main__":
    unittest.main()
