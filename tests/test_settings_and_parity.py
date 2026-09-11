"""Unit tests for Settings preferences, Android 4.5.2 parity features, and session clearing."""

import unittest
from unittest.mock import MagicMock
from vrka_qml.settings_state import SettingsState
from vrka_qml.operational_controller import OperationalController


class SettingsAndParityTests(unittest.TestCase):
    def setUp(self):
        self.mock_host = MagicMock()
        self.mock_host.output_folder = "C:\\Downloads\\VRKA"
        self.mock_host.load_settings.return_value = {}
        self.mock_bridge = MagicMock()

    def test_font_mode_setting(self):
        settings = SettingsState(self.mock_host)
        self.assertEqual(settings.fontFamilyMode, "vrka")

        settings.fontFamilyMode = "system"
        self.assertEqual(settings.fontFamilyMode, "system")

        # Invalid mode is ignored
        settings.fontFamilyMode = "invalid_mode"
        self.assertEqual(settings.fontFamilyMode, "system")

    def test_destination_mode_setting(self):
        settings = SettingsState(self.mock_host)
        self.assertEqual(settings.destinationMode, "remember")

        settings.destinationMode = "ask_every_time"
        self.assertEqual(settings.destinationMode, "ask_every_time")

        # Invalid mode is ignored
        settings.destinationMode = "invalid_dest"
        self.assertEqual(settings.destinationMode, "ask_every_time")

    def test_browser_session_data_clearing(self):
        settings = SettingsState(self.mock_host)
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, settings)

        result_msg = op_ctrl.clearBrowserSessionData()
        self.assertIn("purged successfully", result_msg)
        self.assertEqual(op_ctrl.browserState, "idle")

    def test_sanitized_diagnostics_scrubs_secrets(self):
        settings = SettingsState(self.mock_host)
        self.mock_bridge.activity.rowCount.return_value = 1
        self.mock_bridge.activity.data.side_effect = lambda idx, role: "Request token=SECRET_VAL_123" if role == 257 else "INFO"
        self.mock_bridge.activeCount = 0
        self.mock_bridge.queuedCount = 0
        self.mock_bridge.historyCount = 0

        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, settings)
        diagnostics = op_ctrl.exportSanitizedDiagnostics()

        self.assertIn("VRKA 4.5 OPERATIONAL DIAGNOSTICS", diagnostics)
        self.assertNotIn("SECRET_VAL_123", diagnostics)
        self.assertIn("[REDACTED]", diagnostics)

    def test_operational_controller_helper_slots(self):
        settings = SettingsState(self.mock_host)
        op_ctrl = OperationalController(self.mock_host, self.mock_bridge, settings)

        # Test verification window and retry slots
        op_ctrl.openVerificationWindow()
        self.mock_host.ui_queue.put.assert_any_call(("log", "Browser verification window requested."))

        op_ctrl.retryAfterVerification()
        self.mock_host.ui_queue.put.assert_any_call(("log", "Retrying transfer after verification window confirmation."))

        # Test openOutputFolder slot
        op_ctrl.openOutputFolder()


if __name__ == "__main__":
    unittest.main()
