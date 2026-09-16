"""Tests for QueueController history management and action slots."""

import os
import queue
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication

from vrka_qml.queue_controller import QueueController

_app = None


def setUpModule():
    global _app
    _app = QCoreApplication.instance() or QCoreApplication([])


class FakeHost:
    def __init__(self):
        self.history = [
            {"id": "h1", "url": "https://example.com/1", "title": "Item 1"},
            {"id": "h2", "url": "https://example.com/2", "title": "Item 2"},
        ]
        self.ui_queue = queue.Queue()
        self._core_adapter = object()
        self.saved = False

    def save_history(self):
        self.saved = True

    def remove_history_entry(self, entry_id):
        self.history = [h for h in self.history if h.get("id") != entry_id]
        self.save_history()
        self.ui_queue.put(("history_refresh", None))


class QueueControllerHistoryTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeHost()
        self.bridge = object()
        self.controller = QueueController(self.host, self.bridge)


    def test_clear_all_history(self):
        self.assertEqual(len(self.host.history), 2)
        self.controller.clearAllHistory()
        self.assertEqual(self.host.history, [])
        self.assertTrue(self.host.saved)

        event = self.host.ui_queue.get_nowait()
        self.assertEqual(event, ("history_refresh", None))

    def test_clear_history_alias(self):
        self.assertEqual(len(self.host.history), 2)
        self.controller.clearHistory()
        self.assertEqual(self.host.history, [])
        self.assertTrue(self.host.saved)

        event = self.host.ui_queue.get_nowait()
        self.assertEqual(event, ("history_refresh", None))

    def test_remove_history_entry(self):
        self.controller.removeHistoryEntry("h1")
        self.assertEqual(len(self.host.history), 1)
        self.assertEqual(self.host.history[0]["id"], "h2")
        self.assertTrue(self.host.saved)

        event = self.host.ui_queue.get_nowait()
        self.assertEqual(event, ("history_refresh", None))

    def test_redownload_from_history_signal(self):
        received = []
        self.controller.redownloadRequested.connect(lambda u: received.append(u))
        self.controller.redownloadFromHistory("https://example.com/item")
        self.assertEqual(received, ["https://example.com/item"])


class DownloadControllerHistoryTests(unittest.TestCase):
    def setUp(self):
        from vrka_qml.download_controller import DownloadController
        self.host = FakeHost()
        self.controller = DownloadController(self.host)

    def test_download_controller_clear_all_history(self):
        self.assertEqual(len(self.host.history), 2)
        self.controller.clearAllHistory()
        self.assertEqual(self.host.history, [])
        self.assertTrue(self.host.saved)
        event = self.host.ui_queue.get_nowait()
        self.assertEqual(event, ("history_refresh", None))

    def test_download_controller_clear_history_alias(self):
        self.assertEqual(len(self.host.history), 2)
        self.controller.clearHistory()
        self.assertEqual(self.host.history, [])
        self.assertTrue(self.host.saved)
        event = self.host.ui_queue.get_nowait()
        self.assertEqual(event, ("history_refresh", None))

