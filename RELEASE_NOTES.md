# VRKA 4.5.1

Build 019

## Highlights
- **Secure Application Self-Updater**: Automated in-app update checking, cryptographic OpenPGP release signature verification against the pinned authoritative release key, SHA-256 integrity validation, distribution type detection (Installer vs Portable), and safe staging.
- **Independent Component Updaters**: Dedicated, decoupled updaters for yt-dlp (with official upstream signature verification and rollback), uBlock Origin Lite (MV3), and Puemos Media Observer (MV3).
- **24-Hour Rate-Limited Startup Check**: Background check at most once per 24 hours with durable persistence in `~/.vrka/update_state.json`.
- **Unified Component Update Prompt**: Non-blocking modal overlay showing all available updates with one-click batch installation and non-nagging "Later" dismissal.
- **Concurrency & Debounce Protection**: Background worker locks preventing simultaneous update checks or race conditions.
- **Full Test Suite Coverage**: 163 automated tests with 100% pass rate.

## Updates & Maintenance
- **yt-dlp**: Independent checks against upstream GitHub releases with `SHA2-256SUMS` and `SHA2-256SUMS.sig` OpenPGP verification (signed by pinned key `57CF65933B5A7581`), binary execution test, and safe rollback via `.yt-dlp.previous.exe`.
- **uBlock Origin Lite**: Verified Manifest V3 distribution for Microsoft Edge WebView2 / Chromium runtime with SHA-256 integrity checks.
- **Puemos Media Observer**: Verified Manifest V3 media detection extension with SHA-256 integrity checks.
- **Application Self-Updater**: Strict semantic versioning, downgrade rejection, SHA-256 checksum matching, and detached OpenPGP signature verification with pinned project key `71165A658B3A8612AC2568C6D519380BEBA1B9F7`.

## Downloading & Fallback
- Intelligent yt-dlp failure classifier routing recoverable errors (flashvars, KVS, client-side/embedded players, bot challenges, and webpage HTTP blocks) to WebView2 Browser Fallback.
- Anti-recursion protection guaranteeing browser fallback runs at most once per logical task.
- Multi-factor quality selection evaluating bitrate, resolution, and frame rate without synthetic codec bias.

## Security
- Pinned OpenPGP release signatures and SHA-256 verification across application and component assets.
- Fail-closed download staging in temporary `.downloading` containers.
- Automated credential and local path scrubbing in logs and exported diagnostics.

---

## Historical Releases

### VRKA 4.5.0 (Build 018)

- **Version**: 4.5.0 (Build 018)
- **Release Date**: 2026-09-12
- **Target Platform**: Windows 10/11 x64
- **License**: GPL-3.0-or-later

#### Highlights in 4.5.0
- Modern Qt 6 QML desktop interface with custom title bar, native window controls, and floating sidebar.
- Configurable download destination modes: remember folder or prompt every time.
- Font preference switcher between Monospace and System Default.
- In-app application updates with SHA-256 validation and automatic rollback.
- Supported component updates for yt-dlp, uBlock Origin Lite, and Puemos.
- One-click browser session and cache clearing for privacy.
- End-to-end cryptographic release verification using pinned OpenPGP signing keys.

### VRKA 4.0.1 (Build 017)

- **Version**: 4.0.1 (Build 017)
- **Release Date**: 2026-09-01
- **Target Platform**: Windows 10/11 x64
- **License**: GPL-3.0-or-later

#### Highlights in 4.0.1
- **UPLINK Status Synchronization**: Resolved an issue where the compact sidebar UPLINK status indicator remained stuck on `UPLINK QUEUED` (yellow) after task completion.
- **Dynamic Version Headers**: Window title and Settings version badges dynamically reflect active build metadata (`4.0.1 Build 017`).
- **Regression Test Coverage**: Added dedicated UPLINK state machine tests in `tests/test_uplink_state.py` validating queue transitions.
- **Documentation & Screenshot Refresh**: Updated product screenshots with native captures demonstrating the verified `UPLINK LIVE` idle state.

---

### VRKA 4.0.0 (Build 016)

- **Version**: 4.0.0 (Build 016)
- **Release Date**: 2026-09-01
- **Target Platform**: Windows 10/11 x64
- **License**: GPL-3.0-or-later

#### Highlights in 4.0.0
- **Native Qt 6 QML Desktop Interface**: Hardware-accelerated interface built with PySide6 and Qt Quick supporting dynamic window resizing.
- **UPLINK Status Console**: Sidebar console displaying live task execution status and queue metrics.
- **Day / Night Mode**: Compact theme toggle with smooth transitions.
- **Selectable Activity Log**: Diagnostic console supporting full text selection and copying.
- **Passive Browser Fallback**: Content-filtered WebView2 session for observing media streams (HLS master manifests, DASH, direct MP4).
- **Strict-FIFO Task Scheduler**: Single-worker queue with durable persistence in `tasks.json`.
- **Managed Runtime Updater**: In-app yt-dlp runtime manager in `%LOCALAPPDATA%\VRKA\runtime` with SHA-256 validation.
- **Audio Extraction**: Audio extraction supporting MP3, WAV, and FLAC formats.
- **Privacy & Security**: Zero telemetry, redacted logs, and strict DRM non-circumvention.
