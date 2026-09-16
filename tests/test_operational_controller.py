"""Regression tests for OperationalController: AppUpdateInfo interface and thread-safe GUI dispatch."""

from __future__ import annotations

import platform
import time
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication

from vrka_qml.app_updater import AppUpdateInfo, check_for_application_update
from vrka_qml.operational_controller import OperationalController
from vrka_qml.settings_state import SettingsState


def _drain_events(op_ctrl: OperationalController, busy_attr: str = "batchBusy", timeout: float = 2.0) -> None:
    """Helper to process Qt events until the specified busy attribute becomes False."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        QCoreApplication.processEvents()
        if not getattr(op_ctrl, busy_attr):
            break
        time.sleep(0.01)
    QCoreApplication.processEvents()


class AppUpdateInfoInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication.instance() or QCoreApplication([])
        self.mock_host = MagicMock()
        self.mock_host.output_folder = "C:\\Downloads\\VRKA"
        self.mock_host.load_settings.return_value = {}
        self.mock_bridge = MagicMock()
        self.settings = SettingsState(self.mock_host)

    def test_app_update_info_semver_comparison(self):
        """AppUpdateInfo.is_newer must accurately reflect semantic comparison."""
        # 4.5.2 -> 4.5.3: update is available
        info_newer = AppUpdateInfo(
            current_version="4.5.2",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="",
            published_at="",
            asset_name="VRKA-4.5.3-Build-021-Setup.exe",
            asset_download_url="",
            sha256_manifest_url="",
            signature_url="",
            is_newer=True,
        )
        self.assertTrue(info_newer.is_newer)

        # 4.5.3 -> 4.5.3: up to date
        info_same = AppUpdateInfo(
            current_version="4.5.3",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="",
            published_at="",
            asset_name="VRKA-4.5.3-Build-021-Setup.exe",
            asset_download_url="",
            sha256_manifest_url="",
            signature_url="",
            is_newer=False,
        )
        self.assertFalse(info_same.is_newer)

        # 4.5.4 -> 4.5.3: downgrade rejection
        info_older = AppUpdateInfo(
            current_version="4.5.4",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="",
            published_at="",
            asset_name="VRKA-4.5.3-Build-021-Setup.exe",
            asset_download_url="",
            sha256_manifest_url="",
            signature_url="",
            is_newer=False,
        )
        self.assertFalse(info_older.is_newer)

    def test_app_update_info_has_no_update_available_attribute(self):
        """AppUpdateInfo dataclass defines is_newer; accessing update_available must fail."""
        info = AppUpdateInfo(
            current_version="4.5.3",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="",
            published_at="",
            asset_name="Setup.exe",
            asset_download_url="",
            sha256_manifest_url="",
            signature_url="",
            is_newer=False,
        )
        self.assertTrue(hasattr(info, "is_newer"))
        self.assertFalse(hasattr(info, "update_available"))
        with self.assertRaises(AttributeError):
            _ = info.update_available

    def test_operational_controller_check_app_update_up_to_date(self):
        """Controller uses info.is_newer and sets 'VRKA 4.5.3 is up to date (latest v4.5.3).' without exception."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        info_same = AppUpdateInfo(
            current_version="4.5.3",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="",
            published_at="",
            asset_name="Setup.exe",
            asset_download_url="",
            sha256_manifest_url="",
            signature_url="",
            is_newer=False,
        )

        with patch("vrka_qml.operational_controller.check_for_application_update", return_value=info_same):
            op_ctrl.checkAppUpdate()
            self.assertTrue(op_ctrl.appUpdateBusy)
            _drain_events(op_ctrl, busy_attr="appUpdateBusy")

            self.assertFalse(op_ctrl.appUpdateBusy)
            self.assertFalse(op_ctrl.appUpdateAvailable)
            self.assertEqual(op_ctrl.appUpdateLatestVersion, "4.5.3")
            self.assertEqual(op_ctrl.appUpdateStatusText, "VRKA 4.5.3 is up to date (latest v4.5.3).")

    def test_operational_controller_check_app_update_newer(self):
        """Controller uses info.is_newer to detect newer version v4.5.3 when running 4.5.2."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        info_newer = AppUpdateInfo(
            current_version="4.5.2",
            latest_version="4.5.3",
            tag_name="v4.5.3",
            release_notes="Maintenance release",
            published_at="2026-09-14",
            asset_name="Setup.exe",
            asset_download_url="https://example.com/Setup.exe",
            sha256_manifest_url="https://example.com/SHA256SUMS.txt",
            signature_url="https://example.com/SHA256SUMS.txt.asc",
            is_newer=True,
        )

        with patch("vrka_qml.operational_controller.check_for_application_update", return_value=info_newer):
            op_ctrl.checkAppUpdate()
            self.assertTrue(op_ctrl.appUpdateBusy)
            _drain_events(op_ctrl, busy_attr="appUpdateBusy")

            self.assertFalse(op_ctrl.appUpdateBusy)
            self.assertTrue(op_ctrl.appUpdateAvailable)
            self.assertEqual(op_ctrl.appUpdateLatestVersion, "4.5.3")
            self.assertEqual(op_ctrl.appUpdateReleaseNotes, "Maintenance release")
            self.assertEqual(op_ctrl.appUpdateStatusText, "New application update available: v4.5.3")

    def test_operational_controller_check_app_update_error(self):
        """Controller clears busy state and sets error status if check_for_application_update raises."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)

        with patch("vrka_qml.operational_controller.check_for_application_update", side_effect=RuntimeError("Network unreachable")):
            op_ctrl.checkAppUpdate()
            self.assertTrue(op_ctrl.appUpdateBusy)
            _drain_events(op_ctrl, busy_attr="appUpdateBusy")

            self.assertFalse(op_ctrl.appUpdateBusy)
            self.assertIn("Update check failed: Network unreachable", op_ctrl.appUpdateStatusText)


class CheckAllUpdatesTests(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication.instance() or QCoreApplication([])
        self.mock_host = MagicMock()
        self.mock_host.output_folder = "C:\\Downloads\\VRKA"
        self.mock_host.load_settings.return_value = {}
        self.mock_bridge = MagicMock()
        self.settings = SettingsState(self.mock_host)

    def test_check_all_success_all_up_to_date(self):
        """All components are up to date: busy clears, status reports all up to date."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.check_all = MagicMock(return_value={
            "has_updates": False,
            "updates_list": [],
            "error": "",
        })

        op_ctrl.checkAllUpdates()
        self.assertTrue(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Checking all components for updates...")

        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "All components are up to date.")

    def test_check_all_success_with_updates_available(self):
        """Updates available for components: busy clears, status reports count."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.check_all = MagicMock(return_value={
            "has_updates": True,
            "updates_list": [{"name": "yt-dlp", "available_version": "2026.09.14"}],
            "error": "",
        })

        op_ctrl.checkAllUpdates()
        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Updates available for 1 component(s).")

    def test_check_all_failure_reported(self):
        """One component check failure: busy clears, status reports batch check failed."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.check_all = MagicMock(return_value={
            "has_updates": False,
            "updates_list": [],
            "error": "Connection timed out",
        })

        op_ctrl.checkAllUpdates()
        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Batch check failed: Connection timed out")

    def test_check_all_exception_handling(self):
        """Batch updater raises exception: busy clears, status reports error."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.check_all = MagicMock(side_effect=RuntimeError("Subsystem crashed"))

        op_ctrl.checkAllUpdates()
        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Batch check error: Subsystem crashed")

    def test_check_all_rapid_repeated_clicks(self):
        """Rapid clicks while busy are rejected; only one operation runs and busy clears."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        call_count = 0

        def slow_check_all(**kwargs):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)
            return {"has_updates": False, "updates_list": [], "error": ""}

        op_ctrl._batch_updater.check_all = slow_check_all

        op_ctrl.checkAllUpdates()
        # Immediate second and third clicks while busy
        op_ctrl.checkAllUpdates()
        op_ctrl.checkAllUpdates()

        _drain_events(op_ctrl, busy_attr="batchBusy", timeout=3.0)

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(call_count, 1)

    def test_check_all_recheck_after_completion(self):
        """After completion, checkAllUpdates() can be invoked again normally."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.check_all = MagicMock(return_value={
            "has_updates": False,
            "updates_list": [],
            "error": "",
        })

        # Run 1
        op_ctrl.checkAllUpdates()
        _drain_events(op_ctrl, busy_attr="batchBusy")
        self.assertFalse(op_ctrl.batchBusy)

        # Run 2
        op_ctrl.checkAllUpdates()
        self.assertTrue(op_ctrl.batchBusy)
        _drain_events(op_ctrl, busy_attr="batchBusy")
        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "All components are up to date.")


class UpdateAllAvailableTests(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication.instance() or QCoreApplication([])
        self.mock_host = MagicMock()
        self.mock_host.output_folder = "C:\\Downloads\\VRKA"
        self.mock_host.load_settings.return_value = {}
        self.mock_bridge = MagicMock()
        self.settings = SettingsState(self.mock_host)

    def test_update_all_success(self):
        """Successful update all clears busy and displays success summary."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.update_all = MagicMock(return_value={
            "success": True,
            "summary": "All 3 components successfully updated.",
            "error": "",
        })

        op_ctrl.updateAllAvailable()
        self.assertTrue(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Updating available components...")

        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "All 3 components successfully updated.")

    def test_update_all_failure(self):
        """Partial update failure clears busy and displays failure message."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.update_all = MagicMock(return_value={
            "success": False,
            "summary": "1/3 updated (uBlock Origin Lite failed: validation error)",
            "error": "uBlock Origin Lite failed",
        })

        op_ctrl.updateAllAvailable()
        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "1/3 updated (uBlock Origin Lite failed: validation error)")

    def test_update_all_exception(self):
        """Update all exception clears busy and displays error message."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.update_all = MagicMock(side_effect=RuntimeError("Disk write error"))

        op_ctrl.updateAllAvailable()
        _drain_events(op_ctrl, busy_attr="batchBusy")

        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "Batch update error: Disk write error")

    def test_update_all_recheck_after_failure(self):
        """After failure, updateAllAvailable() can be rerun cleanly."""
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        op_ctrl._batch_updater.update_all = MagicMock(return_value={"success": False, "summary": "Failed", "error": "Err"})

        op_ctrl.updateAllAvailable()
        _drain_events(op_ctrl, busy_attr="batchBusy")
        self.assertFalse(op_ctrl.batchBusy)

        # Run again with success
        op_ctrl._batch_updater.update_all = MagicMock(return_value={"success": True, "summary": "All updated", "error": ""})
        op_ctrl.updateAllAvailable()
        self.assertTrue(op_ctrl.batchBusy)
        _drain_events(op_ctrl, busy_attr="batchBusy")
        self.assertFalse(op_ctrl.batchBusy)
        self.assertEqual(op_ctrl.batchStatusText, "All updated")

    def test_export_sanitized_diagnostics_architecture(self):
        """Diagnostics correctly includes dynamic platform.machine() architecture."""
        self.mock_bridge.activity.rowCount.return_value = 0
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, self.settings)
        with patch("PySide6.QtGui.QGuiApplication.clipboard") as mock_clip:
            mock_clipboard_instance = MagicMock()
            mock_clip.return_value = mock_clipboard_instance
            diag = op_ctrl.exportSanitizedDiagnostics()
            self.assertIn(f"({platform.machine()})", diag)
            self.assertIn(f"OS: {platform.system()}", diag)

    def test_resolve_ffmpeg_location_validates(self):
        """resolve_ffmpeg_location() must discover valid ffmpeg and ffprobe binaries."""
        import os
        import vrka_downloader as vd
        ffmpeg_dir = vd.resolve_ffmpeg_location()
        self.assertIsNotNone(ffmpeg_dir, "FFmpeg directory must be resolvable via static-ffmpeg or runtime")
        exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        probe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
        ffmpeg_path = os.path.join(ffmpeg_dir, exe_name)
        probe_path = os.path.join(ffmpeg_dir, probe_name)
        self.assertTrue(os.path.isfile(ffmpeg_path), f"ffmpeg must exist at {ffmpeg_path}")
        self.assertTrue(os.path.isfile(probe_path), f"ffprobe must exist at {probe_path}")
        valid_f, _, err_f = vd.validate_ffmpeg_binary(ffmpeg_path)
        self.assertTrue(valid_f, f"ffmpeg validation failed: {err_f}")
        valid_p, _, err_p = vd.validate_ffprobe_binary(probe_path)
        self.assertTrue(valid_p, f"ffprobe validation failed: {err_p}")


if __name__ == "__main__":
    unittest.main()

