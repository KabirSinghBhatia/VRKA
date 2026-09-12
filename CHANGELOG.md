# Changelog

All notable changes to VRKA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.5.0] - 2026-09-12 (Build 018)

### Added
- **Modernized Qt Quick QML Desktop Interface**: Re-engineered desktop shell featuring a neutral floating sidebar island, custom Windows title bar with native DWM framing and 16x16 wolf identity, and responsive card layouts.
- **Dynamic Fonts Preference**: Dedicated user-facing Fonts preference supporting Monospace and System Default.
- **Independent Component Update State Machine**: Isolated operational status management for uBlock Origin Lite rulesets, Puemos media observer, and core yt-dlp engine.
- **Cryptographic Release Verification**: Comprehensive OpenPGP release signature verification enforcing the pinned trusted release key fingerprint (`71165A658B3A8612AC2568C6D519380BEBA1B9F7`).
- **Instant Browser Session Purge**: Direct Settings action to completely flush cookies, DOM storage, and network cache from the WebView2 fallback subsystem.

### Changed
- **Balanced Download Page Geometry**: Centered content block with responsive card column layouts (2-column on wider screens, single column on narrower viewports) and balanced vertical centering.
- **Settings Information Architecture**: Streamlined Settings hierarchy with Download Destination, Fonts, Component Updates, Authentication, Subtitles, Media, Network & File Output, Browser Privacy, Custom yt-dlp Command, Diagnostics, Application Updates, and About VRKA.
- **User Interface Copy Refinements**: Enforced exact, concise copy across all settings and cards (`Custom yt-dlp Command`, `Monospace`, `System Default`, `VRKA`).

### Fixed
- **Maximized Window Framing**: Resolved maximized window edge bleeding by enforcing square corners (`radius: 0`), zero border width, and solid background framing when maximized.
- **UPLINK Status Reactivity**: Ensured seamless real-time status transitions between Ready, Queued, and Active download states.
- **Asynchronous Subsystem Startup**: Decoupled background component checks from initial UI presentation, guaranteeing instant window display.

---

## [4.0.1] - 2026-09-01 (Build 017)

### Fixed
- **UPLINK Status Stuck on QUEUED**: Fixed an issue where the compact sidebar UPLINK status indicator and telemetry console remained stuck at `UPLINK QUEUED` (yellow) after a task finished. Connected `TaskListModel.dataChanged` and `layoutChanged` signals to bridge property notifications so transitions to `UPLINK LIVE` (green) propagate reactively.
- **Dynamic Version Labels**: Bound application and settings window version headers dynamically to `APP_DISPLAY_VERSION`.

### Added
- **UPLINK State Machine Regression Coverage**: Added comprehensive test suite (`tests/test_uplink_state.py`) verifying state transitions across task insertion, active downloading, completion, error, cancellation, and multi-task queue scenarios.
- **Dedicated Test Directory Layout**: Consolidated test suites into `tests/` supporting standard `python -m unittest discover -s tests`.

### Changed
- Refreshed real application interface screenshots across documentation to reflect version 4.0.1 and verified UPLINK LIVE idle state.

---

## [4.0.0] - 2026-09-01 (Build 016)

### Added
- **Qt 6 QML Desktop Interface**: Completely re-engineered frontend using PySide6 and Qt Quick for smooth rendering, responsive layout, and visual fidelity.
- **UPLINK Telemetry Console**: Sidebar console displaying real-time task queue statistics (Queued, Active, Archived, Done).
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
