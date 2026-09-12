# Changelog

All notable changes to VRKA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.5.0] - 2026-09-12 (Build 018)

### Added
- Added the new Qt 6 QML Windows interface with custom title bar and floating sidebar.
- Added configurable download location behavior (Remember Location vs Ask Every Time).
- Added in-app application updates with SHA-256 validation and rollback support.
- Added supported component updates for yt-dlp, uBlock Origin Lite, and Puemos.
- Added custom HTTP header support with strict validation.
- Added custom yt-dlp command options with a safety confirmation prompt.
- Added browser session and cache clearing in Settings.
- Added light and dark interface themes.
- Added Monospace and System Default font choices.

### Changed
- Reworked the Download, Queue, History, and Settings pages for improved clarity and responsive scaling.
- Improved media quality selection based on resolution, frame rate, bitrate, and codec efficiency.
- Improved diagnostics and privacy handling with automated credential scrubbing.
- Documented MP3, Opus, and WAV as standard audio extraction options.

### Fixed
- Fixed maximized window framing and border alignment on Windows.
- Fixed UPLINK status transitions between ready, active, and queued states.
- Fixed asynchronous subsystem startup to ensure instant window display.
- Fixed version consistency across project configuration, code, and documentation.

### Security
- Enforced strict RFC 7230 token validation and CRLF injection prevention for HTTP headers.
- Implemented cryptographic release verification using pinned OpenPGP signing keys.
- Enhanced updater security with HTTPS requirements and redirect allowlisting.

---

## [4.0.1] - 2026-09-01 (Build 017)

### Fixed
- **UPLINK Status Stuck on QUEUED**: Fixed an issue where the compact sidebar UPLINK status indicator remained stuck at `UPLINK QUEUED` (yellow) after a task finished. Connected `TaskListModel.dataChanged` and `layoutChanged` signals to bridge property notifications so transitions to `UPLINK LIVE` (green) propagate reactively.
- **Dynamic Version Labels**: Bound application and settings window version headers dynamically to `APP_DISPLAY_VERSION`.

### Added
- **UPLINK State Machine Regression Coverage**: Added test suite (`tests/test_uplink_state.py`) verifying state transitions across task insertion, active downloading, completion, error, cancellation, and multi-task queue scenarios.
- **Dedicated Test Directory Layout**: Consolidated test suites into `tests/` supporting standard `python -m unittest discover -s tests`.

### Changed
- Refreshed real application interface screenshots across documentation to reflect version 4.0.1 and verified UPLINK LIVE idle state.

---

## [4.0.0] - 2026-09-01 (Build 016)

### Added
- **Qt 6 QML Desktop Interface**: Completely re-engineered frontend using PySide6 and Qt Quick for smooth rendering and responsive layout.
- **UPLINK Status Console**: Sidebar console displaying real-time task queue statistics (Queued, Active, Archived, Done).
- **Theme System**: Dedicated Day / Night theme toggle with compact capsule design and animated sliding indicator.
- **Selectable Activity Log**: High-performance multi-line activity log supporting text selection, `Ctrl+A` select-all, and `Ctrl+C` copying.
- **Passive Browser Fallback Subsystem**: Isolated WebView2 execution with uBlock Origin Lite content protection, ranking HLS master manifests, DASH, and direct MP4 streams.
- **Strict-FIFO Scheduler**: Durable single-worker execution model with persistent `tasks.json` storage and state recovery.
- **Managed Runtime Updater**: In-app yt-dlp update manager with SHA-256 validation, atomic rollout, and instant rollback.

### Changed
- Migrated primary desktop interface from legacy widgets to native Qt Quick / QML.
- Polished top-left sidebar branding with 72px VRKA Wolf logo and refined typography.
- Deduplicated retry arguments in yt-dlp command construction (`--impersonate` and extractor arguments).

### Fixed
- Fixed child helper process standard stream restoration in frozen PyInstaller windowed builds (`noconsole=True`).
- Fixed responsive width propagation on high-DPI displays across all window sizes.

---

## [3.0.0] - 2026-08-20

### Added
- Passive media observation engine integration with uBlock Origin Lite.
- End-to-end browser-context transfer protocol for protected streaming sites.
- Deterministic candidate ranking algorithm (`CandidateRanker`).

---

## [2.0.0] - 2026-08-03

### Added
- Initial modular non-Flutter architecture with Python backend.
- Standalone Windows installer and single-file portable builds.
- Contextual Cloudflare challenge handling and cookie import options.
