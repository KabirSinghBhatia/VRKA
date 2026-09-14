"""Persistent state machine and durable state storage for VRKA 4.5.1 updaters.

Manages:
- Application self-update lifecycle states
- Independent component update states (yt-dlp, uBlock Origin Lite, Puemos)
- Authoritative batch update operation states
- 24-hour rate-limiting gates for startup checks and notifications
- Atomic persistence to %USERPROFILE%/.vrka/update_state.json
"""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
import threading
import time
from typing import Any


class AppUpdateState(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFYING = "verifying"
    READY_TO_INSTALL = "ready_to_install"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComponentUpdateState(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    UPDATING = "updating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchUpdateState(str, Enum):
    IDLE = "idle"
    CHECKING = "checking"
    UPDATING = "updating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _get_app_version() -> str:
    """Derive installed application version dynamically from authoritative source."""
    try:
        import vrka_downloader as app
        return str(getattr(app, "APP_DISPLAY_VERSION", getattr(app, "APP_VERSION", "4.5.2")))
    except Exception:
        return "4.5.2"


class UpdateStateStore:
    """Thread-safe durable state storage for app and component updaters."""

    DEFAULT_CHECK_INTERVAL_SECONDS = 86400.0  # 24 hours

    def __init__(self, state_file: Path | str | None = None):
        if state_file is None:
            self._state_file = Path.home() / ".vrka" / "update_state.json"
        else:
            self._state_file = Path(state_file)

        self._lock = threading.RLock()
        self._data: dict[str, Any] = {
            "last_auto_check_timestamp": 0.0,
            "last_auto_popup_timestamp": 0.0,
            "app_update": {
                "state": AppUpdateState.IDLE.value,
                "current_version": _get_app_version(),
                "available_version": "",
                "asset_name": "",
                "last_check": 0.0,
                "error": "",
            },
            "components": {
                "yt-dlp": {
                    "state": ComponentUpdateState.IDLE.value,
                    "installed_version": "",
                    "available_version": "",
                    "last_check": 0.0,
                    "last_update": 0.0,
                    "error": "",
                },
                "ubol": {
                    "state": ComponentUpdateState.IDLE.value,
                    "installed_version": "",
                    "available_version": "",
                    "last_check": 0.0,
                    "last_update": 0.0,
                    "error": "",
                },
                "puemos": {
                    "state": ComponentUpdateState.IDLE.value,
                    "installed_version": "",
                    "available_version": "",
                    "last_check": 0.0,
                    "last_update": 0.0,
                    "error": "",
                },
            },
            "batch": {
                "state": BatchUpdateState.IDLE.value,
                "last_check": 0.0,
                "error": "",
            },
        }
        self.load()

    @property
    def state_file(self) -> Path:
        return self._state_file

    def load(self) -> None:
        """Load persisted state from disk safely."""
        with self._lock:
            if not self._state_file.is_file():
                return
            try:
                content = self._state_file.read_text(encoding="utf-8")
                raw = json.loads(content)
                if isinstance(raw, dict):
                    if "last_auto_check_timestamp" in raw:
                        self._data["last_auto_check_timestamp"] = float(raw["last_auto_check_timestamp"])
                    if "last_auto_popup_timestamp" in raw:
                        self._data["last_auto_popup_timestamp"] = float(raw["last_auto_popup_timestamp"])
                    if isinstance(raw.get("app_update"), dict):
                        self._data["app_update"].update(raw["app_update"])
                    if isinstance(raw.get("components"), dict):
                        for k, v in raw["components"].items():
                            if k in self._data["components"] and isinstance(v, dict):
                                self._data["components"][k].update(v)
                    if isinstance(raw.get("batch"), dict):
                        self._data["batch"].update(raw["batch"])
            except Exception:
                # Corrupted state file must not crash startup; leave defaults
                pass

    def save(self) -> None:
        """Atomically persist state to disk."""
        with self._lock:
            try:
                self._state_file.parent.mkdir(parents=True, exist_ok=True)
                tmp_file = self._state_file.with_suffix(".json.tmp")
                text = json.dumps(self._data, indent=2) + "\n"
                tmp_file.write_text(text, encoding="utf-8")
                os.replace(tmp_file, self._state_file)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 24-Hour Rate Limiting
    # ------------------------------------------------------------------

    def can_run_auto_check(
        self,
        interval_seconds: float = DEFAULT_CHECK_INTERVAL_SECONDS,
        current_time: float | None = None,
    ) -> bool:
        """Return True if at least interval_seconds have passed since last automatic check."""
        with self._lock:
            now = time.time() if current_time is None else float(current_time)
            last = float(self._data.get("last_auto_check_timestamp", 0.0))
            if last <= 0.0:
                return True
            return (now - last) >= interval_seconds

    def record_auto_check(self, timestamp: float | None = None) -> None:
        """Record the timestamp of an automatic component check and persist."""
        with self._lock:
            self._data["last_auto_check_timestamp"] = time.time() if timestamp is None else float(timestamp)
            self.save()

    def can_show_auto_popup(
        self,
        interval_seconds: float = DEFAULT_CHECK_INTERVAL_SECONDS,
        current_time: float | None = None,
    ) -> bool:
        """Return True if at least interval_seconds have passed since last automatic popup."""
        with self._lock:
            now = time.time() if current_time is None else float(current_time)
            last = float(self._data.get("last_auto_popup_timestamp", 0.0))
            if last <= 0.0:
                return True
            return (now - last) >= interval_seconds

    def record_auto_popup(self, timestamp: float | None = None) -> None:
        """Record the timestamp of an automatic popup notification and persist."""
        with self._lock:
            self._data["last_auto_popup_timestamp"] = time.time() if timestamp is None else float(timestamp)
            self.save()

    def clear_auto_popup(self) -> None:
        """Clear the automatic popup timestamp so future checks can notify immediately."""
        with self._lock:
            self._data["last_auto_popup_timestamp"] = 0.0
            self.save()

    # ------------------------------------------------------------------
    # App Self-Update State
    # ------------------------------------------------------------------

    def get_app_state(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data["app_update"])

    def set_app_state(self, state: AppUpdateState | str, **kwargs: Any) -> None:
        with self._lock:
            st_val = state.value if isinstance(state, AppUpdateState) else str(state)
            self._data["app_update"]["state"] = st_val
            for k, v in kwargs.items():
                self._data["app_update"][k] = v
            self.save()

    # ------------------------------------------------------------------
    # Component State
    # ------------------------------------------------------------------

    def get_component_state(self, component_name: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._data["components"].get(component_name, {}))

    def set_component_state(
        self,
        component_name: str,
        state: ComponentUpdateState | str,
        **kwargs: Any,
    ) -> None:
        with self._lock:
            if component_name not in self._data["components"]:
                self._data["components"][component_name] = {}
            st_val = state.value if isinstance(state, ComponentUpdateState) else str(state)
            self._data["components"][component_name]["state"] = st_val
            for k, v in kwargs.items():
                self._data["components"][component_name][k] = v
            self.save()

    # ------------------------------------------------------------------
    # Batch State
    # ------------------------------------------------------------------

    def get_batch_state(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data["batch"])

    def set_batch_state(self, state: BatchUpdateState | str, **kwargs: Any) -> None:
        with self._lock:
            st_val = state.value if isinstance(state, BatchUpdateState) else str(state)
            self._data["batch"]["state"] = st_val
            for k, v in kwargs.items():
                self._data["batch"][k] = v
            self.save()
