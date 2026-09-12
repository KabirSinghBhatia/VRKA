# VRKA 4.5.0

Build 018

## Highlights
- Modern Qt 6 QML desktop interface with custom title bar, native window controls, and floating sidebar.
- Configurable download destination modes: remember folder or prompt every time.
- Font preference switcher between Monospace and System Default.
- In-app application updates with SHA-256 validation and automatic rollback.
- Supported component updates for yt-dlp, uBlock Origin Lite, and Puemos.
- One-click browser session and cache clearing for privacy.
- End-to-end cryptographic release verification using pinned OpenPGP signing keys.

## Downloading
- Multi-factor quality ranking prioritizing higher-bitrate and higher-fidelity streams without arbitrary codec bias.
- Audio extraction supporting MP3 (320, 256, 192, 128 kbps), Opus, and uncompressed WAV.
- Single-worker FIFO task queue with persistent task state and crash recovery.
- Advanced download options including playlist index ranges, subtitle language selection, precision media trimming, and custom HTTP headers.
- Optional custom yt-dlp command-line arguments protected by a safety confirmation prompt.

## Browser Fallback
- Automated passive fallback for sites requiring browser-assisted stream observation.
- Isolated WebView2 session equipped with uBlock Origin Lite ad and tracker protection.
- Passive detection of HLS master playlists, DASH manifests, and direct MP4 streams with automatic handoff to the download engine.
- Complete session data clearing available directly in Settings.

## Updates
- Application Updates: Check, stage, and install official VRKA updates directly within the application.
- Component Updates: Independent update checks and management for yt-dlp, uBlock Origin Lite rulesets, and the Puemos media observer.
- Cryptographic verification: Updates are verified using SHA-256 digests over secure HTTPS connections.

## Security
- RFC 7230 header validation: Custom HTTP headers are strictly validated against token grammar, rejecting CRLF and null-byte injection attacks.
- Sensitive data scrubbing: Authentication tokens, cookies, signed query parameters, and private file paths are automatically redacted from activity logs and diagnostic exports.
- Cryptographic release verification: Official releases are signed with the project's authoritative 4096-bit OpenPGP release signing key (fingerprint `71165A658B3A8612AC2568C6D519380BEBA1B9F7`).

## Known Limitations
- DRM-protected streams (Widevine, FairPlay, PlayReady) are not supported.
- Complex interactive web players may require brief manual user playback before streams become detectable.
- Downloads run in a sequential single-worker queue.
- Supported desktop platform is Windows 10 and 11 (x64).
- OpenPGP release signatures and current Windows SmartScreen/code-signing limitations: official packages are signed with OpenPGP rather than commercial Authenticode certificates. Verify SHA-256 digests against `SHA256SUMS.txt`.

---

## Historical Releases

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
