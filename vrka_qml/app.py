"""Core Qt Quick bootstrap for VRKA 4.5.1 (Build 019).

Presentation layer: loads the QML shell and wires the presentation bridge
to the engine host.
"""

from __future__ import annotations

import os
import queue
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from .bridge import PresentationBridge
from .download_controller import DownloadController
from .engine_host import EngineHost
from .operational_controller import OperationalController
from .queue_controller import QueueController
from .settings_state import SettingsState

# Authoritative VRKA 4.5.1 application identity
APP_DISPLAY_VERSION = "4.5.1"
APP_BUILD = "019"

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = Path(sys._MEIPASS)
    QML_DIR = Path(sys._MEIPASS) / "vrka_qml" / "qml"
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    QML_DIR = Path(__file__).resolve().parent / "qml"


def _load_brand_fonts() -> None:
    fonts_dir = PROJECT_ROOT / "assets" / "fonts"
    for name in ("SpaceMono-Regular.ttf", "SpaceMono-Bold.ttf"):
        QFontDatabase.addApplicationFont(str(fonts_dir / name))


def _apply_windows_native_framing(window) -> None:
    """Apply Windows 11 DWM rounded corner preference and immersive dark framing."""
    if sys.platform != "win32" or not window:
        return
    try:
        import ctypes
        from ctypes import byref, c_int, sizeof
        from PySide6.QtGui import QWindow

        hwnd = int(window.winId())
        if not hwnd:
            return
        dwmapi = ctypes.windll.dwmapi

        def _update_framing(visibility=None):
            try:
                is_max = (window.visibility() == QWindow.Visibility.Maximized)
                # DWMWA_WINDOW_CORNER_PREFERENCE = 33 (1 = DWMWCP_DONOTROUND, 2 = DWMWCP_ROUND)
                corner_pref = c_int(1 if is_max else 2)
                dwmapi.DwmSetWindowAttribute(hwnd, 33, byref(corner_pref), sizeof(corner_pref))

                # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 1809+ / Windows 11)
                dark_mode = c_int(1)
                dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(dark_mode), sizeof(dark_mode))

                # DWMWA_BORDER_COLOR = 34 (Subdued border color)
                border_color = c_int(0x00000000 if is_max else 0x001A1A1A)
                dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(border_color), sizeof(border_color))

                # DWMWA_SYSTEMBACKDROP_TYPE = 38 (2 = DWMSBT_MAINWINDOW / Mica, Windows 11 22H2+)
                backdrop_type = c_int(2)
                dwmapi.DwmSetWindowAttribute(hwnd, 38, byref(backdrop_type), sizeof(backdrop_type))
            except Exception:
                pass

        window.visibilityChanged.connect(_update_framing)
        _update_framing()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    smoke = "--smoke" in argv

    log_path = Path.home() / ".vrka" / "runtime.log"
    os.makedirs(log_path.parent, exist_ok=True)
    if sys.stdout is None:
        try:
            sys.stdout = open(log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        try:
            sys.stderr = open(log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")

    if smoke:
        # Headless-safe default; an explicit QT_QPA_PLATFORM always wins.
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication([sys.argv[0]] + [a for a in argv if a != "--smoke"])
    app.setApplicationName("VRKA")
    app.setOrganizationName("MVRK")
    app.setApplicationDisplayName("VRKA")
    app.setApplicationVersion(APP_DISPLAY_VERSION)
    # Taskbar grouping: match 3.0's explicit AppUserModelID so Windows groups correctly
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VRKA.Downloader")
    except Exception:
        pass
    # Window / taskbar icon — same VRKA wolf used for packaged EXE (vrka.ico)
    try:
        app.setWindowIcon(QIcon(str(PROJECT_ROOT / "assets" / "branding" / "vrka.ico")))
    except Exception:
        pass
    _load_brand_fonts()

    engine = QQmlApplicationEngine()
    # QML exposure: identity strings, the presentation bridge, the download
    # controller, and the queue/history action controller. One shared queue
    # feeds the bridge; the engine host produces into it directly
    # application does.
    shared_queue = queue.Queue()
    engine_host = EngineHost(shared_queue)
    bridge = PresentationBridge(shared_queue)
    settings = SettingsState(engine_host)
    # Load persisted settings before any QML binding evaluates.
    settings.load()
    controller = DownloadController(engine_host, settings)
    queue_ctrl = QueueController(engine_host, bridge)
    engine_host._queue_controller = queue_ctrl
    operational = OperationalController(engine_host, bridge, settings)

    engine.rootContext().setContextProperty("APP_DISPLAY_VERSION", APP_DISPLAY_VERSION)
    engine.rootContext().setContextProperty("APP_BUILD", APP_BUILD)
    engine.rootContext().setContextProperty("Bridge", bridge)
    engine.rootContext().setContextProperty("Controller", controller)
    engine.rootContext().setContextProperty("QueueController", queue_ctrl)
    engine.rootContext().setContextProperty("Settings", settings)
    engine.rootContext().setContextProperty("Operational", operational)

    app.aboutToQuit.connect(bridge.shutdown)
    app.aboutToQuit.connect(lambda: engine_host.shutdown())

    def _serve_history():
        bridge.history.set_entries(engine_host.history)

    bridge.historyRefreshRequested.connect(_serve_history)
    # Stage 5: History "Again" must prefill the Download page via the
    # existing DownloadController seam without exposing history internals.
    queue_ctrl.redownloadRequested.connect(
        lambda url: controller.prefillRequested.emit(str(url))
    )

    # Load the presentation shell and ensure the root window is created and visible
    # before starting backend worker threads or subsystem checks.
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "MainShell.qml")))
    if not engine.rootObjects():
        # QML syntax errors, missing files or failed resource resolution all
        # surface here as "no root object".
        return 1

    root_window = engine.rootObjects()[0]
    _apply_windows_native_framing(root_window)

    if smoke:
        # Exercise one event-loop pass so bindings/delegates actually run,
        # then terminate cleanly with success.
        QTimer.singleShot(300, app.quit)
        return 0 if app.exec() == 0 else 1

    # Main window is created and visible. Start backend worker threads and models:
    engine_host.start()
    for snapshot in engine_host.restored_task_snapshots():
        bridge.seed_task(snapshot)
    _serve_history()
    bridge.start()

    # Defer runtime subsystem initialization to run asynchronously after UI is shown
    QTimer.singleShot(50, operational.initializeSubsystems)

    # Dedicated packaged execution and test harness modes
    verify_url = None
    capture_dir = None
    for i, arg in enumerate(argv):
        if arg in ("--verify-download", "--qa-verify-download") and i + 1 < len(argv):
            verify_url = argv[i + 1]
        elif arg in ("--capture-suite", "--qa-capture-suite") and i + 1 < len(argv):
            capture_dir = Path(argv[i + 1])

    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else PROJECT_ROOT

    if verify_url:
        from PySide6.QtQuick import QQuickItem
        from PySide6.QtCore import QEventLoop

        out_dir = exe_dir / "screenshots"
        os.makedirs(out_dir, exist_ok=True)

        verify_state = {
            "target_id": None,
            "ticks": [],
            "statuses": [],
            "speeds": [],
            "etas": [],
            "captured_active": False,
            "success": False,
        }

        def _on_sub_accepted(tid, url):
            verify_state["target_id"] = str(tid)
            print(f"[VERIFY] Tracked Task ID: {tid}")

        controller.submissionAccepted.connect(_on_sub_accepted)

        def _grab_screen(fname):
            item = root_window.findChild(QQuickItem)
            if item:
                img = item.grabToImage()
                loop = QEventLoop()
                img.ready.connect(loop.quit)
                QTimer.singleShot(1500, loop.quit)
                loop.exec()
                dest = out_dir / f"{fname}.png"
                img.saveToFile(str(dest))
                print(f"[VERIFY] Saved: {dest.name}")

        def _on_task_data_changed(top_left, bottom_right, roles):
            row = top_left.row()
            if row < 0 or row >= bridge.tasks.rowCount():
                return
            idx = bridge.tasks.index(row, 0)
            tid = str(bridge.tasks.data(idx, bridge.tasks.TaskIdRole) or "")
            if not verify_state["target_id"] or tid != verify_state["target_id"]:
                return

            prog = bridge.tasks.data(idx, bridge.tasks.ProgressRole)
            status = str(bridge.tasks.data(idx, bridge.tasks.StatusRole) or "")
            speed = str(bridge.tasks.data(idx, bridge.tasks.SpeedRole) or "")
            eta = str(bridge.tasks.data(idx, bridge.tasks.EtaRole) or "")

            if status and status not in verify_state["statuses"]:
                verify_state["statuses"].append(status)

            if prog is not None:
                p_val = float(prog)
                if not verify_state["ticks"] or abs(verify_state["ticks"][-1] - p_val) >= 0.005:
                    verify_state["ticks"].append(p_val)
                    if speed and speed not in verify_state["speeds"]:
                        verify_state["speeds"].append(speed)
                    if eta and eta not in verify_state["etas"]:
                        verify_state["etas"].append(eta)
                    print(f"[REAL DOWNLOAD] Progress: {p_val*100:.1f}% | Speed: {speed} | ETA: {eta} | Status: {status} | ActiveCount: {bridge.activeCount}")

            if status == "downloading" and 0.10 <= float(prog or 0) <= 0.85 and not verify_state["captured_active"]:
                verify_state["captured_active"] = True
                _grab_screen("08_queue_active_download_progress")

            if status == "completed":
                print(f"[REAL DOWNLOAD] Download Finished! Recorded {len(verify_state['ticks'])} progress updates.")
                _grab_screen("09_queue_download_completed")
                if len(verify_state["ticks"]) >= 2:
                    verify_state["success"] = True
                QTimer.singleShot(1000, lambda: app.exit(0 if verify_state["success"] else 1))

        bridge.tasks.dataChanged.connect(_on_task_data_changed)

        def _trigger_verify():
            root_window.setProperty("currentPageIndex", 1)  # Queue View
            download_dir = exe_dir / "test_downloads"
            os.makedirs(download_dir, exist_ok=True)
            opts = {
                "mode": "video",
                "quality": "360p",
                "output_folder": str(download_dir),
            }
            print(f"[VERIFY] Submitting download: {verify_url}")
            controller.submitDownload(verify_url, opts)

        QTimer.singleShot(600, _trigger_verify)
        # Timeout after 90 seconds
        QTimer.singleShot(90000, lambda: app.exit(0 if verify_state["success"] else 1))

    elif capture_dir:
        from PySide6.QtQuick import QQuickItem
        from PySide6.QtCore import QEventLoop
        from PySide6.QtGui import QWindow

        if not capture_dir.is_absolute():
            capture_dir = exe_dir / capture_dir
        os.makedirs(capture_dir, exist_ok=True)

        def _run_suite():
            # Enforce 100% sanitized synthetic paths and state for documentation captures (Zero personal information)
            settings.outputFolder = "C:\\Users\\Example\\Downloads"
            bridge.history.set_entries([
                {
                    "id": "synthetic-hist-1",
                    "title": "Quantum Physics - Complete Lecture Series [1080p 60fps]",
                    "url": "https://example.com/watch?v=quantum-physics",
                    "path": "C:\\Users\\Example\\Downloads\\Quantum_Physics.mp4",
                    "mode": "video",
                    "timestamp": "2026-09-12 10:30",
                },
                {
                    "id": "synthetic-hist-2",
                    "title": "Nature Documentary: Deep Ocean 4K [Best Available]",
                    "url": "https://example.com/watch?v=deep-ocean-4k",
                    "path": "C:\\Users\\Example\\Downloads\\Deep_Ocean_4K.mp4",
                    "mode": "video",
                    "timestamp": "2026-09-12 09:15",
                }
            ])
            bridge.tasks.upsert(
                "task-demo-1",
                title="Cosmos: A Spacetime Odyssey [1080p 60fps AV1]",
                url="https://example.com/watch?v=cosmos",
                status="downloading",
                progress=0.685,
                stage="Downloading 68.5%",
                speed="14.2 MB/s",
                eta="00:00:18",
                outputPath="C:\\Users\\Example\\Downloads\\Cosmos.mp4",
            )
            bridge.tasks.upsert(
                "task-demo-2",
                title="Synthwave Cyberpunk Ambient Mix [Opus 160kbps]",
                url="https://example.com/watch?v=synthwave",
                status="queued",
                progress=0.0,
                stage="Waiting",
                speed="",
                eta="",
                outputPath="C:\\Users\\Example\\Downloads\\Synthwave.opus",
            )
            bridge.log.clear()
            bridge.log.append_messages([
                "[Core] VRKA Media Engine 4.5 initialized successfully.",
                "[Network] TLS connection established with content CDN.",
                "[Engine] yt-dlp 2026.8.19 backend verified.",
                "[Queue] Task task-demo-1 started: Cosmos: A Spacetime Odyssey",
            ])

            steps = [
                # (primary_name, alt_names, width, height, page_idx, dark, scroll_pos, expand_adv)
                ("vrka45-download-dark", ["vrka-main"], 1240, 820, 0, True, 0, False),
                ("vrka45-download-light", [], 1240, 820, 0, False, 0, False),
                ("vrka45-queue-dark", ["vrka-queue"], 1240, 820, 1, True, 0, False),
                ("vrka45-queue-light", [], 1240, 820, 1, False, 0, False),
                ("vrka45-history-dark", ["vrka-history"], 1240, 820, 2, True, 0, False),
                ("vrka45-history-light", [], 1240, 820, 2, False, 0, False),
                ("vrka45-settings-dark", ["vrka-settings"], 1240, 820, 3, True, 0, False),
                ("vrka45-settings-light", [], 1240, 820, 3, False, 0, False),
            ]

            for name, aliases, w, h, page_idx, dark, scroll_pos, expand_adv in steps:
                root_window.setWidth(w)
                root_window.setHeight(h)
                if "maximized" in name:
                    root_window.setVisibility(QWindow.Visibility.Maximized)
                else:
                    root_window.setVisibility(QWindow.Visibility.Windowed)
                root_window.setDarkMode(dark)
                root_window.setProperty("currentPageIndex", page_idx)

                if page_idx == 0:
                    adv_card = root_window.findChild(QQuickItem, "advancedOptionsCard")
                    if adv_card:
                        adv_card.setProperty("isExpanded", expand_adv)

                if page_idx == 3:
                    settings_view = root_window.findChild(QQuickItem, "settingsScroll")
                    if settings_view:
                        ci = settings_view.property("contentItem")
                        if ci:
                            ci.setProperty("contentY", float(scroll_pos))
                        else:
                            settings_view.setProperty("contentY", float(scroll_pos))

                for _ in range(6):
                    app.processEvents()
                    time.sleep(0.03)

                item = root_window.findChild(QQuickItem)
                if item:
                    img = item.grabToImage()
                    loop = QEventLoop()
                    img.ready.connect(loop.quit)
                    QTimer.singleShot(1500, loop.quit)
                    loop.exec()
                    all_names = [name] + aliases
                    for n in all_names:
                        out_path = capture_dir / f"{n}.png"
                        img.saveToFile(str(out_path))
                        print(f"[CAPTURE SUITE] Saved: {out_path.name}")

            print("[CAPTURE SUITE] Representative suite screenshots captured successfully from packaged app!")
            app.exit(0)

        QTimer.singleShot(600, _run_suite)

    return app.exec()
