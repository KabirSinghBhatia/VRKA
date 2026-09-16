# Architecture Overview

VRKA is a modular desktop media downloader built with a native **Qt 6 QML** interface and a Python backend.

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Qt 6 QML Shell                        │
│   (MainShell.qml, Theme.qml, Pages, Components, Models)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ PySide6 Bridge & Signals
┌──────────────────────────────▼──────────────────────────────┐
│                    QML Application Layer                    │
│   (vrka_qml_app.py, app.py, bridge.py, controllers)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Thread-Safe Task Protocol
┌──────────────────────────────▼──────────────────────────────┐
│                     Domain & Core Engine                    │
│  (TaskScheduler, DownloadStateMachine, BrowserFallback)     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     yt-dlp Engine Core      ││  Platform Abstraction Layer  │
│ (Extraction, Muxing, Probing)││      (vrka_platform/)        │
└─────────────────────────────┘└──────────────┬───────────────┘
                                              │
               ┌──────────────────────────────┼──────────────────────────────┐
               │                              │                              │
┌──────────────▼──────────────┐┌──────────────▼──────────────┐┌──────────────▼──────────────┐
│        WindowsDriver        ││         MacOSDriver          ││         LinuxDriver          │
│(WebView2, GDI, Win32 Jobs)  ││ (Cocoa WKWebView, CoreText) ││   (WebKitGTK, POSIX, xdg)    │
└─────────────────────────────┘└─────────────────────────────┘└─────────────────────────────┘
```

---

## Component Breakdown

### 1. Presentation Layer (`vrka_qml/`)
- **Qt Quick / QML**: Renders a fluid, hardware-accelerated user interface supporting dynamic window scaling, high-DPI displays, and theme switching.
- **Bridge (`bridge.py`)**: Connects QML UI signals to backend controllers through thread-safe Qt slots and properties.
- **Adaptive Frame**: Responsive frameless geometry with native traffic lights on macOS and native window controls on Windows.
- **Activity Log Model (`activity_log_model.py`)**: Ring buffer model providing smooth real-time log rendering with low memory overhead.

### 2. Task Orchestration (`vrka_core/scheduler.py`, `vrka_core/tasks.py`)
- **Strict FIFO Queue**: Executes downloads sequentially to maximize throughput, prevent connection contention, and ensure predictable execution.
- **Durable Persistence**: Maintains task records and states atomically in `~/.vrka/tasks.json` (or `%LOCALAPPDATA%\VRKA`).

### 3. Media Extraction Engine (`vrka_downloader.py`, `vrka_core/failure_classifier.py`)
- **Direct Extraction & Failure Classification**: Manages yt-dlp subprocess execution with structured argument arrays. When direct extraction encounters player or site protection barriers, a dedicated failure classifier routes recoverable failures (such as flashvars, KVS players, client-side/embedded players, or webpage access blocks) to Browser Fallback. Network, cancellation, local system, FFmpeg, DRM, and post-transfer failures remain strictly terminal.
- **Single-Attempt Fallback**: Fallback executes at most once per task, preventing recursive retry loops.
- **Post-Processing**: Coordinates FFmpeg/FFprobe operations for muxing, audio transcoding, and precision video trimming.

### 4. Passive Browser Fallback (`vrka_core/browser_fallback.py`, `vrka_platform/browser/`)
- **Protected Environment**: Launches an on-demand browser instance (WebView2 on Windows, native Cocoa WKWebView on macOS) with popup suppression and uBlock Origin Lite content filtering.
- **Stream Observation**: Passively observes network requests to identify HLS master playlists, DASH manifests, and direct MP4 streams.
- **Automated Handoff**: Passes captured media candidate URLs directly to the downloader backend without manual user intervention.

### 5. Platform Abstraction Layer (`vrka_platform/`)
- **Strategy Pattern**: Decouples operating system specifics from business logic via `PlatformDriver` (`WindowsDriver`, `MacOSDriver`, `LinuxDriver`).
- **Subprocess & Ownership**: Standardizes hidden process invocation flags (`CREATE_NO_WINDOW` vs POSIX session leaders) and clean process tree termination (`taskkill` vs `killpg`).
- **Shell & Desktop**: Bridges native file reveal (`explorer /select,` vs `open -R` vs `xdg-open`), system URL handling, and application identity configuration.
- **Font & Tool Resolution**: Manages dynamic font registration (GDI vs CoreText) and binary executable discovery (`.exe` suffix, Homebrew `/opt/homebrew/bin`, PyInstaller bundles).

---

## Security Principles
- **No Inbound Network Ports**: VRKA runs purely as a client application.
- **No Background Telemetry**: Zero analytics, tracking beacons, or remote telemetry.
- **Redacted Diagnostics**: Sensitive session tokens, cookies, and URLs are stripped before display in logs.
- **Process Cleanup**: Helper processes are registered in an ownership registry and terminated cleanly on task cancellation or app exit.
