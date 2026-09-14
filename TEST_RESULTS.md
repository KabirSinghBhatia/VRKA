# VRKA 4.5.1 Build 019 Test Results

## Summary

| Result | Count |
| :--- | ---: |
| Tests | 163 |
| Passed | 163 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

---

## Test Suites

| Suite Module | Tests | Status | Scope |
| :--- | :---: | :---: | :--- |
| `tests.test_app_updater` | 14 | PASSED | SemanticVersion parsing, downgrade rejection, redirect allowlisting, hop limits, package SHA-256 verification, concurrency locking, fail-closed staging cleanup, and update state persistence without NameError. |
| `tests.test_build010_core` | 7 | PASSED | Core download state persistence, FIFO queue ordering, and task state transitions. |
| `tests.test_build010_scheduler` | 8 | PASSED | Single-worker FIFO task scheduling, process isolation, cancellation, and task recovery. |
| `tests.test_component_updater` | 8 | PASSED | Independent component updates (yt-dlp, uBlock Origin Lite MV3, Puemos MV3), 24h startup gate, batch updates, atomic staging, and rollback. |
| `tests.test_coverage_model` | 11 | PASSED | Media observation, candidate ranking models, and stream manifest detection coverage. |
| `tests.test_failure_classifier` | 40 | PASSED | yt-dlp failure classification (flashvars, KVS, client-side player, embedded player, generic parser, Cloudflare, cookies, HTTP blocks), non-recoverable filtering, anti-recursion guards, and end-to-end browser fallback routing. |
| `tests.test_header_security` | 7 | PASSED | RFC 7230 header validation, CRLF injection prevention, and sensitive header redaction. |
| `tests.test_quality_ranking` | 5 | PASSED | Multi-factor quality selection (resolution, frame rate, bitrate, codec efficiency), and no arbitrary HDR bonus. |
| `tests.test_release_authenticity` | 11 | PASSED | OpenPGP detached signature verification, pinned public key matching, and tamper detection. |
| `tests.test_settings_and_parity` | 7 | PASSED | Font preference, destination modes, component updates, session clearing, and sanitized diagnostics. |
| `tests.test_uplink_state` | 6 | PASSED | UPLINK status transitions (READY, ACTIVE, QUEUED, COMPLETED). |
| `tests.test_version_consistency` | 6 | PASSED | Version consistency across `pyproject.toml`, `vrka_downloader.py`, `vrka_qml/app.py`, `version_info.txt`, `SettingsPage.qml`, and About display string. |
| `tests.test_vrka_qml_bridge` | 21 | PASSED | QML bridge event queue draining, activity log ring buffer, and typed signal delivery. |
| `tests.test_vrka_qml_download` | 12 | PASSED | URL validation, download options normalization, and backend delegation. |
