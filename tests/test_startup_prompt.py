"""Tests for Startup Update Prompt, 24-hour rate limiting, dismissal suppression, and manual bypass."""

from __future__ import annotations

from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock

from vrka_core.updater_state import UpdateStateStore
from vrka_core.component_updater import BatchUpdater


class StartupPromptTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "update_state.json"
        self.store = UpdateStateStore(self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fresh_portable_state(self):
        # A fresh installation with no history should immediately allow auto-check and auto-popup
        self.assertTrue(self.store.can_run_auto_check())
        self.assertTrue(self.store.can_show_auto_popup())
        comp_state = self.store.get_component_state("yt-dlp")
        self.assertEqual(comp_state["state"], "idle")

    def test_startup_check_24h_rate_limit(self):
        now = 1700000000.0
        self.store.record_auto_check(timestamp=now)

        # Within 24 hours (86400 seconds) -> blocked
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 100))
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 3600))
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 86399))

        # After 24 hours -> allowed
        self.assertTrue(self.store.can_run_auto_check(current_time=now + 86400))
        self.assertTrue(self.store.can_run_auto_check(current_time=now + 100000))

    def test_dismissal_suppresses_auto_popup_for_24h(self):
        now = 1700000000.0
        # User clicks "Later" -> record_auto_popup
        self.store.record_auto_popup(timestamp=now)

        # Popup must not reappear for 24h
        self.assertFalse(self.store.can_show_auto_popup(current_time=now + 1800))
        self.assertFalse(self.store.can_show_auto_popup(current_time=now + 86399))

        # After 24h -> can reappear
        self.assertTrue(self.store.can_show_auto_popup(current_time=now + 86400))

    def test_manual_check_bypasses_auto_rate_limit(self):
        now = 1700000000.0
        self.store.record_auto_check(timestamp=now)
        # Even though can_run_auto_check is False:
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 60))

        # Manual check calls check_all() directly on BatchUpdater
        batch = BatchUpdater(store=self.store)
        batch.ytdlp.check_update = MagicMock(return_value={"update_available": False, "available_version": "1.0", "error": ""})
        batch.ubol.check_update = MagicMock(return_value={"update_available": False, "available_version": "1.0", "error": ""})
        batch.puemos.check_update = MagicMock(return_value={"update_available": False, "available_version": "1.0", "error": ""})

        res = batch.check_all()
        self.assertFalse(res["has_updates"])
        self.assertEqual(len(res["components"]), 3)


if __name__ == "__main__":
    unittest.main()
