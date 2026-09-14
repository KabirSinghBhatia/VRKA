# Changelog

All notable changes to VRKA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.5.2] - 2026-09-14 (Build 020)

### Fixed
- **Settings UI Small-Window Layout & Responsiveness**:
  - Eliminated horizontal layout clipping and overflow at window widths below 640px.
  - Standardized consistent 9-part component cards across all subsystems (yt-dlp, uBlock Origin Lite, and Puemos Media Observer).
  - Replaced rigid button rows with responsive `Flow` layouts, preventing button overlap, truncation, or boundary clipping on narrow viewports.
  - Added dedicated, wrapping status text areas to prevent long updater messages from displacing UI controls.
  - Made uBOL and Puemos component cards stack vertically into a single column on viewports under 680px.
  - Corrected vertical scrolling by establishing an explicit `contentHeight` binding (`mainCol.implicitHeight + 40`) on `ScrollView`.
- **uBlock Origin Lite Update Loop Elimination**:
  - Resolved regression where checking for updates immediately after an installation incorrectly reported "Update available".
  - Made installed version inspection strictly read-only, scanning all candidate extension directories and picking the highest validated version via numeric version tuple sorting.
  - Implemented atomic directory replacement and automatic pruning of superseded older extension directories only after post-install validation succeeds.
  - Ensured fresh app restarts correctly read the active updated extension manifest.
- **Batch Update Reliability & False Success Elimination**:
  - Replaced partial result checks with strict per-component tracking in `BatchUpdater.update_all()`.
  - Prohibited global success when any component fails; now accurately reports `updated_count`, `failed_count`, and granular error descriptions.
  - Added post-update consistency re-checks to verify all updated components show zero remaining updates.
  - Enforced thread-safe concurrency locks on batch update operations.
- **Startup Component Update Prompt & Rate Limiting**:
  - Integrated 24-hour rate-limiting gate for startup update checks and modal prompts (`CombinedUpdateDialog`).
  - Corrected dialog suppression logic: clicking "Later" suppresses the startup dialog for 24 hours without preventing manual checks from Settings.
  - Added responsive size bounds on the startup update modal to prevent clipping on small displays.
- **Fresh Portable EXE Component Update Detection**:
  - Enabled immediate component update detection on fresh portable installations without prior state history.
- **Diagnostics & Version Consistency**:
  - Made sanitized operational diagnostics dynamically bind to authoritative application identity constants (`APP_DISPLAY_VERSION` and `APP_BUILD`).
- **Release Packaging Line Ending Invariants**:
  - Enforced byte-exact LF-only line endings on `SHA256SUMS.txt` and `RELEASE-MANIFEST.json` and verified detached OpenPGP signatures without normalization.

---

## [4.5.1] - 2026-09-14 (Build 019)

### Added
- **Secure In-App Application Self-Updater**: Full semantic versioning, downgrade rejection, installation type detection (`Setup.exe` vs `Portable.zip`/`Portable.exe`), OpenPGP release signature verification with pinned authoritative key (`71165A658B3A8612AC2568C6D519380BEBA1B9F7`), SHA-256 package integrity validation, and fail-closed atomic staging in `.downloading` temporary containers.
- **Independent Component Updaters**:
  - **yt-dlp**: Official upstream release tracking, `SHA2-256SUMS` and `SHA2-256SUMS.sig` OpenPGP verification (signed by pinned key `57CF65933B5A7581`), binary execution validation via `validate_ytdlp_binary()`, and atomic activation with `.yt-dlp.previous.exe` rollback.
  - **uBlock Origin Lite**: Official upstream checks, Manifest V3 structure and SHA-256 validation for Microsoft WebView2/Chromium runtime.
  - **Puemos Media Observer**: Official upstream checks, Manifest V3 background service worker and SHA-256 validation.
- **Automated 24-Hour Rate-Limited Startup Check**: Durable persistence in `~/.vrka/update_state.json` ensuring background checks run at most once per 24 hours.
- **Combined Update Prompt (`CombinedUpdateDialog.qml`)**: Single non-blocking modal overlay presenting all available component updates with "Update Now" and "Later" options, preventing recurring popup loops.
- **Concurrency Protection & Debouncing**: Thread-safe locks preventing duplicate checks or simultaneous downloads on rapid user interactions.

### Changed
- Refactored update architecture into GUI-independent `vrka_core/updater_state.py` and `vrka_core/component_updater.py`.
- Modernized Settings page with batch update trigger ("Check All Updates") and per-component installation controls.
- Expanded automated regression test suite to 163 tests with 100% pass rate.

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
- Fixed yt-dlp failure classification to route recoverable extraction failures (flashvars, KVS, client-side/embedded players, generic stream parsing, bot challenges, webpage HTTP blocks) to Browser Fallback while keeping network, cancellation, local system, FFmpeg, DRM, and post-transfer failures terminal.
- Added anti-recursion protection to guarantee browser fallback executes at most once per task.

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
