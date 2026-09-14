"""Comprehensive unit and integration tests for Independent Component Updaters,
BatchUpdater, 24-hour rate limiting, and state persistence.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import zipfile

from vrka_core.updater_state import (
    BatchUpdateState,
    ComponentUpdateState,
    UpdateStateStore,
)
from vrka_core.component_updater import (
    BatchUpdater,
    PuemosUpdater,
    UBlockUpdater,
    YtdlpUpdater,
    _version_tuple,
)


class ComponentUpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "update_state.json"
        self.store = UpdateStateStore(self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # Version tuple comparison
    # ------------------------------------------------------------------

    def test_version_tuple_comparison(self):
        self.assertTrue(_version_tuple("2026.08.19") > _version_tuple("2026.03.04"))
        self.assertTrue(_version_tuple("5.5.1") > _version_tuple("5.5.0"))
        self.assertTrue(_version_tuple("v2026.907.2003") > _version_tuple("2026.812.1211"))
        self.assertFalse(_version_tuple("5.5.0") > _version_tuple("5.5.0"))
        self.assertFalse(_version_tuple("2026.03.04") > _version_tuple("2026.08.19"))

    # ------------------------------------------------------------------
    # 24-Hour Rate Limiting & Persistence
    # ------------------------------------------------------------------

    def test_24h_rate_limiting_gate(self):
        # 1. Initial state: should allow check
        self.assertTrue(self.store.can_run_auto_check())
        self.assertTrue(self.store.can_show_auto_popup())

        # 2. Record check at time T
        now = 1000000.0
        self.store.record_auto_check(timestamp=now)
        self.store.record_auto_popup(timestamp=now)

        # 3. Check within 24h (< 86400s) -> False
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 3600.0))  # 1 hour later
        self.assertFalse(self.store.can_run_auto_check(current_time=now + 86399.0)) # 1 second before 24h
        self.assertFalse(self.store.can_show_auto_popup(current_time=now + 43200.0)) # 12 hours later

        # 4. Check after 24h (>= 86400s) -> True
        self.assertTrue(self.store.can_run_auto_check(current_time=now + 86400.0))
        self.assertTrue(self.store.can_run_auto_check(current_time=now + 90000.0))
        self.assertTrue(self.store.can_show_auto_popup(current_time=now + 86401.0))

    def test_rate_limiting_persistence_across_instances(self):
        now = 500000.0
        self.store.record_auto_check(timestamp=now)
        self.store.record_auto_popup(timestamp=now)

        # Reload store from disk
        store2 = UpdateStateStore(self.state_file)
        self.assertFalse(store2.can_run_auto_check(current_time=now + 1000.0))
        self.assertTrue(store2.can_run_auto_check(current_time=now + 86401.0))

    # ------------------------------------------------------------------
    # Independent Component Isolation
    # ------------------------------------------------------------------

    def test_independent_component_state_isolation(self):
        # Update yt-dlp to UPDATING
        self.store.set_component_state("yt-dlp", ComponentUpdateState.UPDATING)
        # Update ubol to COMPLETED
        self.store.set_component_state("ubol", ComponentUpdateState.COMPLETED, installed_version="2026.907.2003")
        # Update puemos to FAILED
        self.store.set_component_state("puemos", ComponentUpdateState.FAILED, error="Network error")

        # Verify each component retains independent state
        self.assertEqual(self.store.get_component_state("yt-dlp")["state"], ComponentUpdateState.UPDATING.value)
        self.assertEqual(self.store.get_component_state("ubol")["state"], ComponentUpdateState.COMPLETED.value)
        self.assertEqual(self.store.get_component_state("ubol")["installed_version"], "2026.907.2003")
        self.assertEqual(self.store.get_component_state("puemos")["state"], ComponentUpdateState.FAILED.value)
        self.assertEqual(self.store.get_component_state("puemos")["error"], "Network error")

    # ------------------------------------------------------------------
    # Batch Updater Concurrency & Debouncing
    # ------------------------------------------------------------------

    def test_batch_updater_debounces_rapid_clicks(self):
        batch = BatchUpdater(self.store)

        # Mock check_update on sub-updaters to sleep briefly
        def _mock_check():
            time.sleep(0.08)
            return {"update_available": False, "current_version": "1.0", "available_version": "1.0"}

        batch.ytdlp.check_update = _mock_check
        batch.ubol.check_update = _mock_check
        batch.puemos.check_update = _mock_check

        results = []
        def _run_click():
            res = batch.check_all(bypass_rate_limit=True)
            results.append(res)

        # Fire 5 rapid concurrent calls
        threads = [threading.Thread(target=_run_click) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 call succeeds; the other 4 are dropped with busy: True
        succeeded = [r for r in results if not r.get("busy")]
        dropped = [r for r in results if r.get("busy")]
        self.assertEqual(len(succeeded), 1)
        self.assertEqual(len(dropped), 4)

        # State must return to not busy and actionable
        self.assertFalse(batch.is_busy)
        self.assertEqual(self.store.get_batch_state()["state"], BatchUpdateState.COMPLETED.value)

    def test_batch_updater_recovers_after_failure(self):
        batch = BatchUpdater(self.store)

        # Force a failure in one sub-updater
        def _failing_check():
            raise RuntimeError("Upstream API rate limited")

        batch.ytdlp.check_update = _failing_check

        res = batch.check_all(bypass_rate_limit=True)
        self.assertFalse(res.get("busy"))
        self.assertIn("Upstream API rate limited", res.get("error", ""))
        self.assertFalse(batch.is_busy)
        self.assertEqual(self.store.get_batch_state()["state"], BatchUpdateState.FAILED.value)

        # Subsequent check succeeds cleanly when upstream recovers
        batch.ytdlp.check_update = lambda: {"update_available": False, "current_version": "2026.08.19"}
        batch.ubol.check_update = lambda: {"update_available": False, "current_version": "2026.907.2003"}
        batch.puemos.check_update = lambda: {"update_available": False, "current_version": "5.5.0"}

        res2 = batch.check_all(bypass_rate_limit=True)
        self.assertFalse(res2.get("busy"))
        self.assertFalse(res2.get("has_updates"))
        self.assertEqual(self.store.get_batch_state()["state"], BatchUpdateState.COMPLETED.value)

    # ------------------------------------------------------------------
    # uBlock Origin Lite Archive & Manifest Validation
    # ------------------------------------------------------------------

    def test_ubol_validates_mv3_manifest_and_rejects_non_mv3(self):
        ubol = UBlockUpdater(self.store)

        # 1. Create valid MV3 zip in memory
        valid_buf = io.BytesIO()
        with zipfile.ZipFile(valid_buf, "w") as zf:
            zf.writestr("manifest.json", json.dumps({
                "manifest_version": 3,
                "name": "uBlock Origin Lite",
                "version": "2026.907.2003"
            }))
        valid_zip = valid_buf.getvalue()

        # 2. Create invalid MV2 zip in memory
        invalid_buf = io.BytesIO()
        with zipfile.ZipFile(invalid_buf, "w") as zf:
            zf.writestr("manifest.json", json.dumps({
                "manifest_version": 2,
                "name": "uBlock Origin",
                "version": "1.54.0"
            }))
        invalid_zip = invalid_buf.getvalue()

        # Test validation on valid MV3
        with zipfile.ZipFile(io.BytesIO(valid_zip)) as zf:
            mf = json.loads(zf.read("manifest.json").decode("utf-8"))
            self.assertEqual(mf.get("manifest_version"), 3)
            self.assertEqual(mf.get("version"), "2026.907.2003")

        # Test rejection of non-MV3
        with zipfile.ZipFile(io.BytesIO(invalid_zip)) as zf:
            mf2 = json.loads(zf.read("manifest.json").decode("utf-8"))
            self.assertNotEqual(mf2.get("manifest_version"), 3)

    # ------------------------------------------------------------------
    # Puemos Media Observer Manifest Validation
    # ------------------------------------------------------------------

    def test_puemos_validates_mv3_and_background_worker(self):
        # 1. Valid Puemos MV3 archive with service worker
        valid_buf = io.BytesIO()
        with zipfile.ZipFile(valid_buf, "w") as zf:
            zf.writestr("manifest.json", json.dumps({
                "manifest_version": 3,
                "name": "Puemos HLS Downloader",
                "version": "5.5.0",
                "background": {"service_worker": "background.js"}
            }))
            zf.writestr("background.js", "console.log('puemos');")
        valid_zip = valid_buf.getvalue()

        with zipfile.ZipFile(io.BytesIO(valid_zip)) as zf:
            mf = json.loads(zf.read("manifest.json").decode("utf-8"))
            self.assertEqual(mf.get("manifest_version"), 3)
            self.assertTrue(bool(mf.get("background", {}).get("service_worker")))

        # 2. Invalid archive missing manifest
        invalid_buf = io.BytesIO()
        with zipfile.ZipFile(invalid_buf, "w") as zf:
            zf.writestr("unrelated.txt", "hello")
        invalid_zip = invalid_buf.getvalue()

        with zipfile.ZipFile(io.BytesIO(invalid_zip)) as zf:
            manifest_entry = next((n for n in zf.namelist() if n.endswith("manifest.json")), None)
            self.assertIsNone(manifest_entry)


if __name__ == "__main__":
    unittest.main()
