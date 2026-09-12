# Project Roadmap

This document outlines planned improvements and future directions for VRKA.

---

## Current Release (v4.5.0 Build 018)
- Modernized Qt 6 QML desktop interface with floating sidebar island, custom Windows title bar, and Day/Night theme toggle.
- Single-worker FIFO task queue with persistent `tasks.json` storage and crash recovery.
- Automated passive Browser Fallback powered by content-filtered WebView2 observation (uBlock Origin Lite and Puemos stream detection).
- In-app yt-dlp runtime and component manager with SHA-256 validation and instant rollback.
- Multi-factor quality selection and high-fidelity audio extraction supporting MP3 and WAV formats.
- Complete browser privacy controls with one-click session and cache purging.

---

## Planned Enhancements

### User Interface & Experience
- Custom output template builder for flexible naming patterns.
- Expanded localization and multi-language interface translations.
- Enhanced speed graphing and visual bandwidth throttling controls.

### Downloader & Engine
- Fine-grained segment connection limits for high-bandwidth connections.
- Extended subtitle styling options and multi-track audio stream extraction.
- Automatic retry tuning with exponential backoff on intermittent network drops.

### Packaging & Infrastructure
- Automated reproducible build verification.
- Code signing integration as project funding permits.
