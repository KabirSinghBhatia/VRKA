# Project Roadmap

This document outlines current capabilities and planned future directions for VRKA.

---

## Current Release (v4.5.2 Build 020)
- Modern Qt 6 QML desktop interface with custom Windows title bar, floating sidebar, and dark/light themes.
- Typography preference supporting Monospace and System Default.
- Configurable download destination behavior (Remember Location vs Ask Every Time).
- Single-worker FIFO task queue with persistent `tasks.json` storage and crash recovery.
- Automated passive Browser Fallback powered by content-filtered WebView2 observation (uBlock Origin Lite and Puemos stream detection).
- In-app application updates and component management (yt-dlp, uBlock Origin Lite, Puemos) with SHA-256 verification and rollback support.
- Multi-factor quality selection and audio extraction supporting MP3, Opus, and WAV formats.
- Browser privacy controls with one-click session and cache clearing.
- Advanced options: playlist index ranges, subtitle selection, precision trimming, and RFC 7230 validated custom HTTP headers.

---

## Planned Enhancements

The following areas represent current planned improvements:

- **Custom Output Filename Templates**: Template-based naming syntax for customized file naming patterns.
- **Multi-Track Audio Selection**: Selecting and extracting alternate language and descriptive audio tracks.
- **Expanded Subtitle Controls**: Additional styling, formatting, and language preference defaults.
- **Download Connection Controls**: Configurable concurrent connection limits per task.
- **Improved Retry Tuning**: Exponential backoff and adaptive retry logic for unstable networks.
- **Localization**: Multi-language translations for the user interface.
