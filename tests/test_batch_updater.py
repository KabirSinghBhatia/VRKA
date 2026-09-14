"""Tests for BatchUpdater: concurrency, partial failure handling, and false-success prevention."""

from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock

from vrka_core.component_updater import BatchUpdater
from vrka_core.updater_state import UpdateStateStore


class BatchUpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "update_state.json"
        self.store = UpdateStateStore(self.state_file)
        self.batch = BatchUpdater(store=self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_batch_update_all_success(self):
        # yt-dlp mocks:
        self.batch.ytdlp.get_installed_version = MagicMock(side_effect=[("2026.03.04", True), ("2026.09.14", True)])
        self.batch.ytdlp.install_update = MagicMock(return_value={"updated": True, "installed_version": "2026.09.14", "error": ""})
        self.batch.ytdlp.check_update = MagicMock(return_value={"update_available": False, "available_version": "2026.09.14", "error": ""})

        # ubol mocks:
        self.batch.ubol.get_installed_version = MagicMock(side_effect=["2026.907.2003", "2026.914.1325", "2026.914.1325"])
        self.batch.ubol.install_update = MagicMock(return_value={"updated": True, "installed_version": "2026.914.1325", "error": ""})
        self.batch.ubol.check_update = MagicMock(return_value={"update_available": False, "available_version": "2026.914.1325", "error": ""})

        # puemos mocks:
        self.batch.puemos.get_installed_version = MagicMock(side_effect=["5.5.0", "5.5.1", "5.5.1"])
        self.batch.puemos.install_update = MagicMock(return_value={"updated": True, "installed_version": "5.5.1", "error": ""})
        self.batch.puemos.check_update = MagicMock(return_value={"update_available": False, "available_version": "5.5.1", "error": ""})

        res = self.batch.update_all()
        self.assertTrue(res["success"], f"Expected batch success, got {res}")
        self.assertEqual(res["updated_count"], 3)
        self.assertEqual(res["failed_count"], 0)
        self.assertEqual(len(res["errors"]), 0)

    def test_batch_update_partial_failure_prevents_false_success(self):
        # yt-dlp succeeds
        self.batch.ytdlp.get_installed_version = MagicMock(side_effect=[("2026.03.04", True), ("2026.09.14", True)])
        self.batch.ytdlp.install_update = MagicMock(return_value={"updated": True, "installed_version": "2026.09.14", "error": ""})
        self.batch.ytdlp.check_update = MagicMock(return_value={"update_available": False, "available_version": "2026.09.14", "error": ""})

        # ubol fails
        self.batch.ubol.get_installed_version = MagicMock(return_value="2026.907.2003")
        self.batch.ubol.install_update = MagicMock(return_value={"updated": False, "installed_version": "2026.907.2003", "error": "Checksum mismatch"})
        self.batch.ubol.check_update = MagicMock(return_value={"update_available": True, "available_version": "2026.914.1325", "error": ""})

        # puemos succeeds
        self.batch.puemos.get_installed_version = MagicMock(side_effect=["5.5.0", "5.5.1", "5.5.1"])
        self.batch.puemos.install_update = MagicMock(return_value={"updated": True, "installed_version": "5.5.1", "error": ""})
        self.batch.puemos.check_update = MagicMock(return_value={"update_available": False, "available_version": "5.5.1", "error": ""})

        res = self.batch.update_all()
        # Must NOT report global success
        self.assertFalse(res["success"], "Partial failure must not report success=True")
        self.assertEqual(res["updated_count"], 2)
        self.assertEqual(res["failed_count"], 1)
        self.assertIn("ubol", res["errors"])
        self.assertIn("Checksum mismatch", res["errors"]["ubol"])

    def test_batch_update_concurrency_lock(self):
        # Ensure only one batch update can run at a time
        block_event = threading.Event()
        started_event = threading.Event()

        def _blocking_install(*args, **kwargs):
            started_event.set()
            block_event.wait(timeout=5.0)
            return {"updated": True, "installed_version": "2026.09.14", "error": ""}

        self.batch.ytdlp.get_installed_version = MagicMock(return_value=("2026.03.04", True))
        self.batch.ytdlp.install_update = _blocking_install
        self.batch.ytdlp.check_update = MagicMock(return_value={"update_available": False, "available_version": "2026.09.14", "error": ""})

        self.batch.ubol.get_installed_version = MagicMock(return_value="2026.907.2003")
        self.batch.ubol.install_update = MagicMock(return_value={"updated": True, "installed_version": "2026.907.2003", "error": ""})
        self.batch.ubol.check_update = MagicMock(return_value={"update_available": False, "available_version": "2026.907.2003", "error": ""})

        self.batch.puemos.get_installed_version = MagicMock(return_value="5.5.0")
        self.batch.puemos.install_update = MagicMock(return_value={"updated": True, "installed_version": "5.5.0", "error": ""})
        self.batch.puemos.check_update = MagicMock(return_value={"update_available": False, "available_version": "5.5.0", "error": ""})

        t = threading.Thread(target=self.batch.update_all, daemon=True)
        t.start()
        started_event.wait(timeout=2.0)

        # Second concurrent attempt must report busy / error
        second_res = self.batch.update_all()
        self.assertFalse(second_res["success"])
        self.assertIn("already in progress", second_res.get("error", ""))

        block_event.set()
        t.join(timeout=3.0)


if __name__ == "__main__":
    unittest.main()
