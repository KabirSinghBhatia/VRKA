"""Operational integration for VRKA 4.5.2: Browser fallback, MediaObserver, yt-dlp updater,
uBlock Origin Lite updater, Puemos updater, 24-hour startup check, Application self-updater,
browser session clearing, and sanitized diagnostics.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


from PySide6.QtCore import Property, QCoreApplication, QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

import vrka_downloader as app
from vrka_core.header_security import redact_secrets_from_text
from vrka_core.updater_state import (
    AppUpdateState,
    BatchUpdateState,
    ComponentUpdateState,
    UpdateStateStore,
)
from vrka_core.component_updater import (
    BatchUpdater,
    PuemosUpdater,
    UBlockUpdater,
    YtdlpUpdater,
)
from .app_updater import (
    AppUpdateInfo,
    check_for_application_update,
    download_and_verify_update,
)


class OperationalController(QObject):
    # Browser session state machine
    browserStateChanged = Signal()
    browserErrorChanged = Signal()
    browserNeededUrlChanged = Signal()
    browserNeededCategoryChanged = Signal()
    browserReadySummaryChanged = Signal()

    # Media observer
    observerStatusChanged = Signal()
    observerHealthChanged = Signal()
    observerStatusTextChanged = Signal()

    # yt-dlp Component Updater
    updaterBusyChanged = Signal()
    updaterStatusTextChanged = Signal()
    updaterOperationalStatusChanged = Signal()
    updaterCurrentVersionChanged = Signal()
    updaterAvailableVersionChanged = Signal()
    updaterUpdateAvailableChanged = Signal()

    # uBlock Origin Lite Component Updater (Independent State)
    ubolBusyChanged = Signal()
    ubolStatusTextChanged = Signal()
    ubolOperationalStatusChanged = Signal()
    ubolCurrentVersionChanged = Signal()
    ubolAvailableVersionChanged = Signal()
    ubolUpdateAvailableChanged = Signal()

    # Puemos Media Observer Component Updater (Independent State)
    puemosBusyChanged = Signal()
    puemosStatusTextChanged = Signal()
    puemosOperationalStatusChanged = Signal()
    puemosCurrentVersionChanged = Signal()
    puemosAvailableVersionChanged = Signal()
    puemosUpdateAvailableChanged = Signal()

    # Authoritative Batch Updater
    batchBusyChanged = Signal()
    batchStatusTextChanged = Signal()

    # 24-Hour Startup Check & Dialog
    startupDialogVisibleChanged = Signal()
    startupUpdatesChanged = Signal()
    startupUpdateDialogRequested = Signal(list)

    # Application Self-Updater
    appUpdateBusyChanged = Signal()
    appUpdateStatusTextChanged = Signal()
    appUpdateAvailableChanged = Signal()
    appUpdateLatestVersionChanged = Signal()
    appUpdateReleaseNotesChanged = Signal()

    # Diagnostics
    diagnosticsTextChanged = Signal()

    # Thread-safe GUI Dispatch
    _guiDispatch = Signal(object)

    def __init__(self, engine_host, bridge, settings_state, parent=None):
        super().__init__(parent)
        self._host = engine_host
        self._bridge = bridge
        self._settings = settings_state

        # Queued dispatcher connection ensuring worker -> GUI delivery
        self._guiDispatch.connect(self._run_on_gui, Qt.ConnectionType.QueuedConnection)

        # Persistent Update Store & Batch Updater
        self._store = UpdateStateStore()
        self._batch_updater = BatchUpdater(self._store)

        self._browser_state: str = "idle"
        self._browser_error: str = ""
        self._browser_needed_url: str = ""
        self._browser_needed_category: str = ""
        self._browser_ready_summary: str = ""

        self._observer_status_text: str = ""
        self._observer_health_ok: bool = False

        # yt-dlp state
        self._updater_busy: bool = False
        self._updater_status_text: str = ""
        self._updater_operational_status: str = "Ready"
        self._updater_current_version: str = "Detecting..."
        self._updater_available_version: str = ""
        self._updater_update_available: bool = False

        # Independent uBOL state
        self._ubol_busy: bool = False
        self._ubol_status_text: str = "Ready"
        self._ubol_operational_status: str = "Ready"
        self._ubol_current_version: str = "1.0.4 (MV3)"
        self._ubol_available_version: str = ""
        self._ubol_update_available: bool = False

        # Independent Puemos state
        self._puemos_busy: bool = False
        self._puemos_status_text: str = "Ready"
        self._puemos_operational_status: str = "Ready"
        self._puemos_current_version: str = "5.5.0 (MV3)"
        self._puemos_available_version: str = ""
        self._puemos_update_available: bool = False

        # Batch Updater state
        self._batch_busy: bool = False
        self._batch_status_text: str = "Ready"

        # Startup update dialog state
        self._startup_dialog_visible: bool = False
        self._startup_updates: list[dict[str, Any]] = []

        # App Self-Updater state
        self._app_update_busy: bool = False
        self._app_update_status_text: str = "Ready to check for application updates."
        self._app_update_available: bool = False
        self._app_update_latest_version: str = ""
        self._app_update_release_notes: str = ""
        self._cached_update_info: AppUpdateInfo | None = None

        self._diagnostics_text: str = ""

        # Wire existing bridge signals
        bridge.browserNeeded.connect(self._on_browser_needed)
        bridge.browserSessionReady.connect(self._on_browser_ready)
        bridge.browserSessionError.connect(self._on_browser_error)

    @Slot(object)
    def _run_on_gui(self, fn: Any) -> None:
        try:
            fn()
        except Exception:
            _logger.exception("Error executing GUI dispatch callback")

    def _dispatch_to_gui(self, fn: Any) -> None:
        if QCoreApplication.instance() is None:
            fn()
        else:
            self._guiDispatch.emit(fn)

    @Slot()
    def initializeSubsystems(self) -> None:
        """Initialize runtime subsystem status asynchronously after UI creation."""
        self._refresh_updater_snapshot()
        self._refresh_observer_snapshot()
        self._refresh_ubol_snapshot()
        self._check_startup_updates_async()

    def _check_startup_updates_async(self) -> None:
        """Non-blocking 24-hour rate-limited component check at application startup."""
        if not getattr(self._settings, "ytdlpCheckOnStartup", True):
            return
        if not self._store.can_run_auto_check():
            return

        def _worker():
            try:
                res = self._batch_updater.check_all(bypass_rate_limit=False)
                self._dispatch_to_gui(lambda r=res: self._on_startup_check_finished(r))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_startup_check_finished(self, res: dict) -> None:
        has_updates = bool(res.get("has_updates"))
        can_popup = self._store.can_show_auto_popup()
        updates = res.get("updates_list", []) if has_updates else []
        if has_updates and can_popup:
            self._startup_updates = updates
            self._startup_dialog_visible = True
            self._store.record_auto_popup()
            self.startupUpdatesChanged.emit()
            self.startupDialogVisibleChanged.emit()
            self.startupUpdateDialogRequested.emit(updates)
        self._refresh_updater_snapshot()
        self._refresh_observer_snapshot()
        self._refresh_ubol_snapshot()

    # ------------------------------------------------------------------
    # Browser session & Fallback
    # ------------------------------------------------------------------

    @Property(str, notify=browserStateChanged)
    def browserState(self) -> str:
        return self._browser_state

    @Property(str, notify=browserErrorChanged)
    def browserError(self) -> str:
        return self._browser_error

    @Property(str, notify=browserNeededUrlChanged)
    def browserNeededUrl(self) -> str:
        return self._browser_needed_url

    @Property(str, notify=browserNeededCategoryChanged)
    def browserNeededCategory(self) -> str:
        return self._browser_needed_category

    @Property(str, notify=browserReadySummaryChanged)
    def browserReadySummary(self) -> str:
        return self._browser_ready_summary

    def _on_browser_needed(self, url: str, category: str) -> None:
        self._browser_state = "needed"
        self._browser_needed_url = url
        self._browser_needed_category = category
        self.browserStateChanged.emit()
        self.browserNeededUrlChanged.emit()
        self.browserNeededCategoryChanged.emit()

    def _on_browser_ready(self, summary: str) -> None:
        self._browser_state = "ready"
        self._browser_ready_summary = summary
        self.browserStateChanged.emit()
        self.browserReadySummaryChanged.emit()

    def _on_browser_error(self, err: str) -> None:
        self._browser_state = "error"
        self._browser_error = err
        self.browserStateChanged.emit()
        self.browserErrorChanged.emit()

    @Slot()
    def launchBrowserSession(self) -> None:
        """User clicked to launch the protected fallback browser manually."""
        if self._browser_needed_url:
            self._host.launch_browser_for_url(self._browser_needed_url)

    @Slot()
    def clearBrowserSession(self) -> None:
        """Clear all stored cookies, cache, and WebStorage in fallback profile."""
        try:
            self._host.clear_browser_profile()
            self._browser_state = "idle"
            self._browser_error = ""
            self._browser_ready_summary = "Browser session data successfully purged."
            self.browserStateChanged.emit()
            self.browserErrorChanged.emit()
            self.browserReadySummaryChanged.emit()
        except Exception as exc:
            self._browser_error = f"Failed to clear profile: {exc}"
            self.browserErrorChanged.emit()

    @Slot(result=str)
    def clearBrowserSessionData(self) -> str:
        """Purge WebView2 session storage (cookies, cache, local storage) without touching settings or queue."""
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        cleared_paths = []
        possible_dirs = [
            local_app_data / "VRKA" / "EBWebView",
            local_app_data / "VRKA" / "browser_profile",
            local_app_data / "VRKA" / "webview2_data",
        ]
        for p in possible_dirs:
            if p.exists() and p.is_dir():
                try:
                    shutil.rmtree(p, ignore_errors=True)
                    cleared_paths.append(p.name)
                except Exception:
                    pass
        self.clearBrowserSession()
        return "Browser session data, cache, and cookies purged successfully."

    @Slot()
    def openVerificationWindow(self) -> None:
        try:
            self._host.ui_queue.put(("log", "Browser verification window requested."))
        except Exception:
            pass
        self.browserStateChanged.emit()

    @Slot()
    def retryAfterVerification(self) -> None:
        try:
            self._host.ui_queue.put(("log", "Retrying transfer after verification window confirmation."))
        except Exception:
            pass
        self.browserStateChanged.emit()

    # ------------------------------------------------------------------
    # Media observer properties
    # ------------------------------------------------------------------

    @Property(str, notify=observerStatusTextChanged)
    def observerStatusText(self) -> str:
        return self._observer_status_text

    @Property(bool, notify=observerHealthChanged)
    def observerHealthOk(self) -> bool:
        return self._observer_health_ok

    # ------------------------------------------------------------------
    # uBlock Origin Lite Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=ubolBusyChanged)
    def ubolBusy(self) -> bool:
        return self._ubol_busy

    @Property(str, notify=ubolStatusTextChanged)
    def ubolStatusText(self) -> str:
        return self._ubol_status_text

    @Property(str, notify=ubolOperationalStatusChanged)
    def ubolOperationalStatus(self) -> str:
        return self._ubol_operational_status

    @Property(str, notify=ubolCurrentVersionChanged)
    def ubolCurrentVersion(self) -> str:
        return self._ubol_current_version

    @Property(str, notify=ubolAvailableVersionChanged)
    def ubolAvailableVersion(self) -> str:
        return self._ubol_available_version

    @Property(bool, notify=ubolUpdateAvailableChanged)
    def ubolUpdateAvailable(self) -> bool:
        return self._ubol_update_available

    # ------------------------------------------------------------------
    # Puemos Media Observer Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=puemosBusyChanged)
    def puemosBusy(self) -> bool:
        return self._puemos_busy

    @Property(str, notify=puemosStatusTextChanged)
    def puemosStatusText(self) -> str:
        return self._puemos_status_text

    @Property(str, notify=puemosOperationalStatusChanged)
    def puemosOperationalStatus(self) -> str:
        return self._puemos_operational_status

    @Property(str, notify=puemosCurrentVersionChanged)
    def puemosCurrentVersion(self) -> str:
        return self._puemos_current_version

    @Property(str, notify=puemosAvailableVersionChanged)
    def puemosAvailableVersion(self) -> str:
        return self._puemos_available_version

    @Property(bool, notify=puemosUpdateAvailableChanged)
    def puemosUpdateAvailable(self) -> bool:
        return self._puemos_update_available

    # ------------------------------------------------------------------
    # Batch Updater Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=batchBusyChanged)
    def batchBusy(self) -> bool:
        return self._batch_busy

    @Property(str, notify=batchStatusTextChanged)
    def batchStatusText(self) -> str:
        return self._batch_status_text

    # ------------------------------------------------------------------
    # Startup Update Dialog Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=startupDialogVisibleChanged)
    def startupDialogVisible(self) -> bool:
        return self._startup_dialog_visible

    @Property("QVariantList", notify=startupUpdatesChanged)
    def startupUpdates(self) -> list:
        return self._startup_updates

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def _refresh_observer_snapshot(self) -> None:
        try:
            text = self._host._media_observer_status_text()
        except Exception as exc:
            text = f"Media observer status unavailable: {exc}"
            self._observer_health_ok = False
            self._observer_status_text = text
            self._puemos_operational_status = "Degraded"
            self.observerStatusTextChanged.emit()
            self.observerHealthChanged.emit()
            self.puemosOperationalStatusChanged.emit()
            return
        health_ok = False
        try:
            adapter = self._host._media_observer_adapter()
            health = adapter.health()
            health_ok = bool(health.get("ok"))
        except Exception:
            pass
        self._observer_status_text = str(text)
        self._observer_health_ok = bool(health_ok)
        self._puemos_operational_status = "Active" if health_ok else "Degraded"
        self._puemos_current_version = self._batch_updater.puemos.get_installed_version()
        self.observerStatusTextChanged.emit()
        self.observerHealthChanged.emit()
        self.puemosOperationalStatusChanged.emit()
        self.puemosCurrentVersionChanged.emit()

    def _refresh_ubol_snapshot(self) -> None:
        ver = self._batch_updater.ubol.get_installed_version()
        self._ubol_current_version = ver
        self._ubol_operational_status = "Active"
        self.ubolCurrentVersionChanged.emit()
        self.ubolOperationalStatusChanged.emit()

    @Slot()
    def refreshObserverStatus(self) -> None:
        self._refresh_observer_snapshot()

    @Slot()
    def refreshAllSubsystems(self) -> None:
        self._refresh_updater_snapshot()
        self._refresh_observer_snapshot()
        self._refresh_ubol_snapshot()

    # ------------------------------------------------------------------
    # uBlock Origin Lite Actions
    # ------------------------------------------------------------------

    @Slot()
    def checkUbolUpdate(self) -> None:
        if self._ubol_busy:
            return
        self._ubol_busy = True
        self._ubol_operational_status = "Checking..."
        self._ubol_status_text = "Checking uBlock Origin Lite releases..."
        self.ubolBusyChanged.emit()
        self.ubolOperationalStatusChanged.emit()
        self.ubolStatusTextChanged.emit()

        def _worker():
            try:
                info = self._batch_updater.ubol.check_update()
                self._dispatch_to_gui(lambda inf=info: self._on_ubol_check_finished(inf))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_ubol_check_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ubol_check_finished(self, info: dict) -> None:
        try:
            if info.get("error"):
                self._ubol_operational_status = "Failed"
                self._ubol_status_text = f"Check failed: {info.get('error')}"
            elif info.get("update_available"):
                self._ubol_operational_status = "Update available"
                self._ubol_available_version = str(info.get("available_version"))
                self._ubol_update_available = True
                self._ubol_status_text = f"Update available: {self._ubol_available_version}"
            else:
                self._ubol_operational_status = "Up to date"
                self._ubol_status_text = f"uBOL is current ({info.get('current_version')})"
            self.ubolOperationalStatusChanged.emit()
            self.ubolStatusTextChanged.emit()
            self.ubolAvailableVersionChanged.emit()
            self.ubolUpdateAvailableChanged.emit()
            self._refresh_ubol_snapshot()
        finally:
            self._ubol_busy = False
            self.ubolBusyChanged.emit()

    def _on_ubol_check_failed(self, error: str) -> None:
        self._ubol_operational_status = "Failed"
        self._ubol_status_text = f"Check error: {error}"
        self.ubolOperationalStatusChanged.emit()
        self.ubolStatusTextChanged.emit()
        self._ubol_busy = False
        self.ubolBusyChanged.emit()

    @Slot()
    def installUbolUpdate(self) -> None:
        if self._ubol_busy:
            return
        self._ubol_busy = True
        self._ubol_operational_status = "Updating..."
        self._ubol_status_text = "Downloading verified uBOL MV3 extension..."
        self.ubolBusyChanged.emit()
        self.ubolOperationalStatusChanged.emit()
        self.ubolStatusTextChanged.emit()

        def _worker():
            try:
                res = self._batch_updater.ubol.install_update()
                self._dispatch_to_gui(lambda r=res: self._on_ubol_install_finished(r))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_ubol_install_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ubol_install_finished(self, res: dict) -> None:
        try:
            if res.get("updated"):
                self._ubol_operational_status = "Active"
                self._ubol_update_available = False
                self._ubol_status_text = f"Updated to {res.get('installed_version')}"
            else:
                self._ubol_operational_status = "Failed"
                self._ubol_status_text = f"Update failed: {res.get('error')}"
            self.ubolOperationalStatusChanged.emit()
            self.ubolStatusTextChanged.emit()
            self.ubolUpdateAvailableChanged.emit()
            self._refresh_ubol_snapshot()
        finally:
            self._ubol_busy = False
            self.ubolBusyChanged.emit()

    def _on_ubol_install_failed(self, error: str) -> None:
        self._ubol_operational_status = "Failed"
        self._ubol_status_text = f"Update error: {error}"
        self.ubolOperationalStatusChanged.emit()
        self.ubolStatusTextChanged.emit()
        self._ubol_busy = False
        self.ubolBusyChanged.emit()

    # ------------------------------------------------------------------
    # Puemos Actions
    # ------------------------------------------------------------------

    @Slot()
    def checkPuemosUpdate(self) -> None:
        if self._puemos_busy:
            return
        self._puemos_busy = True
        self._puemos_operational_status = "Checking..."
        self._puemos_status_text = "Checking Puemos media observer..."
        self.puemosBusyChanged.emit()
        self.puemosOperationalStatusChanged.emit()
        self.puemosStatusTextChanged.emit()

        def _worker():
            try:
                info = self._batch_updater.puemos.check_update()
                self._dispatch_to_gui(lambda inf=info: self._on_puemos_check_finished(inf))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_puemos_check_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_puemos_check_finished(self, info: dict) -> None:
        try:
            if info.get("error"):
                self._puemos_operational_status = "Failed"
                self._puemos_status_text = f"Check failed: {info.get('error')}"
            elif info.get("update_available"):
                self._puemos_operational_status = "Update available"
                self._puemos_status_text = f"Update available: {info.get('available_version')}"
                self._puemos_available_version = str(info.get("available_version"))
                self._puemos_update_available = True
            else:
                self._puemos_operational_status = "Up to date"
                self._puemos_status_text = f"Observer up to date ({info.get('available_version') or '5.5.0'})"
            self.puemosOperationalStatusChanged.emit()
            self.puemosStatusTextChanged.emit()
            self.puemosAvailableVersionChanged.emit()
            self.puemosUpdateAvailableChanged.emit()
            self._refresh_observer_snapshot()
        finally:
            self._puemos_busy = False
            self.puemosBusyChanged.emit()

    def _on_puemos_check_failed(self, error: str) -> None:
        self._puemos_operational_status = "Failed"
        self._puemos_status_text = f"Observer check error: {error}"
        self.puemosOperationalStatusChanged.emit()
        self.puemosStatusTextChanged.emit()
        self._puemos_busy = False
        self.puemosBusyChanged.emit()

    @Slot()
    def checkObserverUpdate(self) -> None:
        self.checkPuemosUpdate()

    @Slot()
    def applyObserverUpdate(self) -> None:
        if self._puemos_busy:
            return
        self._puemos_busy = True
        self._puemos_operational_status = "Updating..."
        self._puemos_status_text = "Updating media observer..."
        self.puemosBusyChanged.emit()
        self.puemosOperationalStatusChanged.emit()
        self.puemosStatusTextChanged.emit()

        def _worker():
            try:
                result = self._batch_updater.puemos.install_update()
                self._dispatch_to_gui(lambda res=result: self._on_puemos_install_finished(res))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_puemos_install_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_puemos_install_finished(self, result: dict) -> None:
        try:
            if result.get("updated"):
                self._puemos_operational_status = "Up to date"
                self._puemos_update_available = False
                self._puemos_status_text = f"Updated to {result.get('installed_version')}"
            else:
                self._puemos_operational_status = "Failed"
                self._puemos_status_text = f"Observer update failed: {result.get('error')}"
            self.puemosOperationalStatusChanged.emit()
            self.puemosStatusTextChanged.emit()
            self.puemosUpdateAvailableChanged.emit()
            self._refresh_observer_snapshot()
        finally:
            self._puemos_busy = False
            self.puemosBusyChanged.emit()

    def _on_puemos_install_failed(self, error: str) -> None:
        self._puemos_operational_status = "Failed"
        self._puemos_status_text = f"Observer update error: {error}"
        self.puemosOperationalStatusChanged.emit()
        self.puemosStatusTextChanged.emit()
        self._puemos_busy = False
        self.puemosBusyChanged.emit()

    # ------------------------------------------------------------------
    # yt-dlp Component Updater
    # ------------------------------------------------------------------

    @Property(bool, notify=updaterBusyChanged)
    def updaterBusy(self) -> bool:
        return self._updater_busy

    @Property(str, notify=updaterStatusTextChanged)
    def updaterStatusText(self) -> str:
        return self._updater_status_text

    @Property(str, notify=updaterOperationalStatusChanged)
    def updaterOperationalStatus(self) -> str:
        return self._updater_operational_status

    @Property(str, notify=updaterCurrentVersionChanged)
    def updaterCurrentVersion(self) -> str:
        return self._updater_current_version

    @Property(str, notify=updaterAvailableVersionChanged)
    def updaterAvailableVersion(self) -> str:
        return self._updater_available_version

    @Property(bool, notify=updaterUpdateAvailableChanged)
    def updaterUpdateAvailable(self) -> bool:
        return self._updater_update_available

    def _refresh_updater_snapshot(self) -> None:
        try:
            ver, src = self._batch_updater.ytdlp.get_installed_version()
            if ver and ver != "Unavailable":
                self._updater_current_version = f"{ver} ({src})"
                self._updater_operational_status = "Active"
                self._updater_status_text = f"Active: {self._updater_current_version}"
            else:
                self._updater_current_version = "Unavailable"
                self._updater_operational_status = "Unavailable"
                self._updater_status_text = "yt-dlp engine unavailable"
        except Exception as exc:
            self._updater_current_version = "?"
            self._updater_operational_status = "Unavailable"
            self._updater_status_text = f"yt-dlp status unavailable: {exc}"
        self.updaterCurrentVersionChanged.emit()
        self.updaterOperationalStatusChanged.emit()
        self.updaterStatusTextChanged.emit()

    @Slot()
    def checkUpdater(self) -> None:
        if self._updater_busy:
            return
        self._updater_busy = True
        self._updater_status_text = "Checking for yt-dlp engine updates..."
        self.updaterBusyChanged.emit()
        self.updaterStatusTextChanged.emit()
        channel = str(self._settings.ytdlpChannel) if self._settings else app.DEFAULT_YTDLP_CHANNEL

        def _worker():
            try:
                info = self._batch_updater.ytdlp.check_update(channel)
                self._dispatch_to_gui(lambda inf=info: self._on_updater_check_finished(inf))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_updater_check_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_updater_check_finished(self, info: dict) -> None:
        try:
            available = str(info.get("available_version") or "")
            self._updater_available_version = available
            self._updater_update_available = bool(info.get("update_available"))
            if info.get("error"):
                self._updater_status_text = f"Check failed: {info.get('error')}"
            elif info.get("update_available"):
                self._updater_status_text = f"Update available: {available} (current {self._updater_current_version})"
            else:
                self._updater_status_text = f"yt-dlp is current ({self._updater_current_version})"
            self.updaterAvailableVersionChanged.emit()
            self.updaterUpdateAvailableChanged.emit()
            self.updaterStatusTextChanged.emit()
        finally:
            self._updater_busy = False
            self.updaterBusyChanged.emit()

    def _on_updater_check_failed(self, error: str) -> None:
        self._updater_status_text = f"Check failed: {error}"
        self.updaterStatusTextChanged.emit()
        self._updater_busy = False
        self.updaterBusyChanged.emit()

    @Slot()
    def installUpdate(self) -> None:
        if self._updater_busy:
            return
        self._updater_busy = True
        self._updater_status_text = "Installing yt-dlp update..."
        self.updaterBusyChanged.emit()
        self.updaterStatusTextChanged.emit()
        channel = str(self._settings.ytdlpChannel) if self._settings else app.DEFAULT_YTDLP_CHANNEL

        def _worker():
            try:
                installed = self._batch_updater.ytdlp.install_update(channel=channel)
                self._dispatch_to_gui(lambda inst=installed: self._on_updater_install_finished(inst))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_updater_install_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_updater_install_finished(self, installed: dict) -> None:
        try:
            if installed.get("updated"):
                self._updater_update_available = False
                self._refresh_updater_snapshot()
                self._updater_status_text = f"Updated to {installed.get('version')}"
            else:
                self._updater_status_text = f"Update failed: {installed.get('error')}"
            self.updaterUpdateAvailableChanged.emit()
            self.updaterStatusTextChanged.emit()
        finally:
            self._updater_busy = False
            self.updaterBusyChanged.emit()

    def _on_updater_install_failed(self, error: str) -> None:
        self._updater_status_text = f"Update failed: {error}"
        self.updaterStatusTextChanged.emit()
        self._updater_busy = False
        self.updaterBusyChanged.emit()

    @Slot()
    def rollbackUpdate(self) -> None:
        if self._updater_busy:
            return
        self._updater_busy = True
        self._updater_status_text = "Rolling back yt-dlp..."
        self.updaterBusyChanged.emit()
        self.updaterStatusTextChanged.emit()

        def _worker():
            try:
                info = self._batch_updater.ytdlp.rollback()
                self._dispatch_to_gui(lambda inf=info: self._on_updater_rollback_finished(inf))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_updater_rollback_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_updater_rollback_finished(self, info: dict) -> None:
        try:
            if info.get("rolled_back"):
                self._updater_status_text = f"Rolled back to {info.get('version')}"
                self._refresh_updater_snapshot()
            else:
                self._updater_status_text = f"Rollback failed: {info.get('error')}"
            self.updaterStatusTextChanged.emit()
        finally:
            self._updater_busy = False
            self.updaterBusyChanged.emit()

    def _on_updater_rollback_failed(self, error: str) -> None:
        self._updater_status_text = f"Rollback failed: {error}"
        self.updaterStatusTextChanged.emit()
        self._updater_busy = False
        self.updaterBusyChanged.emit()

    # ------------------------------------------------------------------
    # Batch Update Actions (Check All Updates)
    # ------------------------------------------------------------------

    @Slot()
    def checkAllUpdates(self) -> None:
        """Debounced manual Check All Updates (bypasses 24h gate)."""
        if self._batch_busy or self._batch_updater.is_busy:
            return
        self._batch_busy = True
        self._batch_status_text = "Checking all components for updates..."
        self.batchBusyChanged.emit()
        self.batchStatusTextChanged.emit()

        def _worker():
            try:
                res = self._batch_updater.check_all(bypass_rate_limit=True)
                self._dispatch_to_gui(lambda r=res: self._on_batch_check_finished(r))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_batch_check_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_batch_check_finished(self, res: dict) -> None:
        try:
            has_up = res.get("has_updates", False)
            up_list = res.get("updates_list", [])

            # 1. Update component snapshots
            self._refresh_updater_snapshot()
            self._refresh_observer_snapshot()
            self._refresh_ubol_snapshot()

            # 2. Set final batch status
            if res.get("error"):
                self._batch_status_text = f"Batch check failed: {res.get('error')}"
            elif has_up:
                self._batch_status_text = f"Updates available for {len(up_list)} component(s)."
            else:
                self._batch_status_text = "All components are up to date."

            # 3. Emit batchStatusTextChanged
            self.batchStatusTextChanged.emit()
        finally:
            # 4. Set _batch_busy = False and emit batchBusyChanged
            self._batch_busy = False
            self.batchBusyChanged.emit()

    def _on_batch_check_error(self, err: str) -> None:
        try:
            self._batch_status_text = f"Batch check error: {err}"
            self.batchStatusTextChanged.emit()
        finally:
            self._batch_busy = False
            self.batchBusyChanged.emit()

    @Slot()
    def updateAllAvailable(self) -> None:
        """Update all components with available updates."""
        if self._batch_busy or self._batch_updater.is_busy:
            return
        self._batch_busy = True
        self._batch_status_text = "Updating available components..."
        self.batchBusyChanged.emit()
        self.batchStatusTextChanged.emit()

        def _worker():
            try:
                res = self._batch_updater.update_all()
                self._dispatch_to_gui(lambda r=res: self._on_batch_update_finished(r))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_batch_update_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_batch_update_finished(self, res: dict) -> None:
        try:
            summary = res.get("summary", "")
            success = bool(res.get("success"))
            if success:
                self._batch_status_text = summary or "All components successfully updated."
            else:
                self._batch_status_text = summary or f"One or more updates failed: {res.get('error', 'Check logs')}"
            self._refresh_updater_snapshot()
            self._refresh_observer_snapshot()
            self._refresh_ubol_snapshot()
            self.batchStatusTextChanged.emit()
        finally:
            self._batch_busy = False
            self.batchBusyChanged.emit()

    def _on_batch_update_error(self, err: str) -> None:
        try:
            self._batch_status_text = f"Batch update error: {err}"
            self.batchStatusTextChanged.emit()
        finally:
            self._batch_busy = False
            self.batchBusyChanged.emit()

    @Slot()
    def dismissStartupDialog(self) -> None:
        """Dismiss the combined startup update prompt (prevents popup loop for 24h)."""
        self._startup_dialog_visible = False
        self._store.record_auto_popup()
        self.startupDialogVisibleChanged.emit()

    @Slot()
    def acceptStartupDialog(self) -> None:
        """Accept the startup update prompt and launch updateAllAvailable."""
        self._startup_dialog_visible = False
        self.startupDialogVisibleChanged.emit()
        self.updateAllAvailable()

    # ------------------------------------------------------------------
    # In-App Application Self-Updater
    # ------------------------------------------------------------------

    @Property(bool, notify=appUpdateBusyChanged)
    def appUpdateBusy(self) -> bool:
        return self._app_update_busy

    @Property(str, notify=appUpdateStatusTextChanged)
    def appUpdateStatusText(self) -> str:
        return self._app_update_status_text

    @Property(bool, notify=appUpdateAvailableChanged)
    def appUpdateAvailable(self) -> bool:
        return self._app_update_available

    @Property(str, notify=appUpdateLatestVersionChanged)
    def appUpdateLatestVersion(self) -> str:
        return self._app_update_latest_version

    @Property(str, notify=appUpdateReleaseNotesChanged)
    def appUpdateReleaseNotes(self) -> str:
        return self._app_update_release_notes

    @Slot()
    def checkAppUpdate(self) -> None:
        """Check GitHub for new VRKA application releases."""
        if self._app_update_busy:
            return
        self._app_update_busy = True
        self._app_update_status_text = "Checking GitHub for VRKA application updates..."
        self.appUpdateBusyChanged.emit()
        self.appUpdateStatusTextChanged.emit()

        def _worker():
            try:
                curr_ver = str(getattr(app, "APP_DISPLAY_VERSION", getattr(app, "APP_VERSION", "4.5.2")))
                info = check_for_application_update(curr_ver, store=self._store)
                self._dispatch_to_gui(lambda inf=info, cv=curr_ver: self._on_app_update_finished(inf, cv))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_app_update_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_app_update_finished(self, info: AppUpdateInfo, curr_ver: str) -> None:
        try:
            self._cached_update_info = info
            if info.is_newer:
                self._app_update_available = True
                self._app_update_latest_version = info.latest_version
                self._app_update_release_notes = info.release_notes
                self._app_update_status_text = f"New application update available: v{info.latest_version}"
                self.appUpdateAvailableChanged.emit()
                self.appUpdateLatestVersionChanged.emit()
                self.appUpdateReleaseNotesChanged.emit()
            else:
                self._app_update_available = False
                self._app_update_latest_version = info.latest_version
                self._app_update_status_text = f"VRKA {curr_ver} is up to date (latest v{info.latest_version})."
                self.appUpdateAvailableChanged.emit()
                self.appUpdateLatestVersionChanged.emit()
            self.appUpdateReleaseNotesChanged.emit()
            self.appUpdateStatusTextChanged.emit()
        finally:
            self._app_update_busy = False
            self.appUpdateBusyChanged.emit()

    def _on_app_update_failed(self, error: str) -> None:
        try:
            self._app_update_status_text = f"Update check failed: {error}"
            self.appUpdateStatusTextChanged.emit()
        finally:
            self._app_update_busy = False
            self.appUpdateBusyChanged.emit()

    @Slot()
    def downloadAndInstallAppUpdate(self) -> None:
        if self._app_update_busy or not self._cached_update_info:
            return
        self._app_update_busy = True
        self._app_update_status_text = "Downloading verified installer package..."
        self.appUpdateBusyChanged.emit()
        self.appUpdateStatusTextChanged.emit()

        def _prog(cur, total):
            if total > 0:
                pct = int((cur / total) * 100)
                msg = f"Downloading update: {pct}% ({cur // 1024} KB / {total // 1024} KB)"
                self._dispatch_to_gui(lambda m=msg: self._on_app_download_progress(m))

        def _worker():
            try:
                target_exe = download_and_verify_update(
                    self._cached_update_info,
                    progress_cb=_prog,
                    store=self._store,
                )
                exe_str = str(target_exe)
                exe_name = target_exe.name
                self._dispatch_to_gui(lambda ep=exe_str, en=exe_name: self._on_app_download_finished(ep, en))
            except Exception as exc:
                err_msg = str(exc)
                self._dispatch_to_gui(lambda err=err_msg: self._on_app_download_failed(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_app_download_progress(self, msg: str) -> None:
        self._app_update_status_text = msg
        self.appUpdateStatusTextChanged.emit()

    def _on_app_download_finished(self, exe_path: str, exe_name: str) -> None:
        try:
            self._app_update_status_text = f"Verified package ready: {exe_name}. Launching setup..."
            self.appUpdateStatusTextChanged.emit()
            os.startfile(exe_path)
        finally:
            self._app_update_busy = False
            self.appUpdateBusyChanged.emit()

    def _on_app_download_failed(self, error: str) -> None:
        try:
            self._app_update_status_text = f"Update download failed: {error}"
            self.appUpdateStatusTextChanged.emit()
        finally:
            self._app_update_busy = False
            self.appUpdateBusyChanged.emit()

    # ------------------------------------------------------------------
    # Sanitized Diagnostics
    # ------------------------------------------------------------------

    @Slot(result=str)
    def exportSanitizedDiagnostics(self) -> str:
        """Collect and sanitize full operational diagnostics, copying to system clipboard."""
        lines = [
            f"=== VRKA {app.APP_DISPLAY_VERSION} OPERATIONAL DIAGNOSTICS ===",
            f"OS: {platform.system()} {platform.release()} (x64) - Python {sys.version.split()[0]}",
            f"PySide6: {app.PySide6.__version__ if hasattr(app, 'PySide6') else 'Loaded'}",
            f"Application Version: {app.APP_DISPLAY_VERSION} (Build {app.APP_BUILD})",
            f"Active Output Folder: {self._host.output_folder}",
            f"Active yt-dlp: {self._updater_current_version}",
            f"uBlock Origin Lite: {self._ubol_current_version}",
            f"Media Observer: {self._puemos_current_version} (Health: {'OK' if self._observer_health_ok else 'Inactive/Degraded'})",
            f"Browser Session State: {self._browser_state}",
            f"Batch Updater State: {self._batch_status_text}",
            f"24h Gate Can Check: {self._store.can_run_auto_check()}",
            f"Active Queue Tasks: {self._bridge.activeCount} | Queued: {self._bridge.queuedCount} | Archived: {self._bridge.historyCount}",
            "",
            "=== RECENT RELEVANT EVENTS ===",
        ]
        # Append sanitized recent log entries
        for row in range(min(40, self._bridge.activity.rowCount())):
            idx = self._bridge.activity.index(row, 0)
            msg = self._bridge.activity.data(idx, 0x0100 + 1)  # MessageRole
            lvl = self._bridge.activity.data(idx, 0x0100 + 2)  # LevelRole
            lines.append(f"[{lvl}] {msg}")

        full_text = "\n".join(lines)
        sanitized = redact_secrets_from_text(full_text)

        # Copy to clipboard if running in a GUI application
        app_inst = QCoreApplication.instance()
        if isinstance(app_inst, QGuiApplication):
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                try:
                    clipboard.setText(sanitized)
                except Exception:
                    pass

        return sanitized

    @Slot()
    def openNotices(self) -> None:
        try:
            notices = app.resource_path(app.Path("THIRD_PARTY_NOTICES.md"))
            if app.Path(notices).exists():
                app.open_path(str(notices))
        except Exception:
            pass

    @Slot()
    def openOutputFolder(self) -> None:
        try:
            folder = getattr(self._host, "output_folder", None) or os.getcwd()
            app.open_path(str(folder))
        except Exception:
            pass

    @Slot(str)
    def openUrl(self, url: str) -> None:
        try:
            import webbrowser
            webbrowser.open(str(url))
        except Exception:
            pass
