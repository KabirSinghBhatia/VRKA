# Known Limitations

This document outlines the current technical boundaries and operational characteristics of VRKA.

---

## Dynamic Website Changes
VRKA uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) for direct media extraction. When streaming sites update their player scripts, APIs, or bot-detection mechanisms, extraction may fail until an updated yt-dlp release is installed. Use **Settings** > **Component Updates** to check for and install updated extractor definitions.

## Browser-Assisted Media Detection
When direct extraction encounters protected pages, VRKA opens an isolated WebView2 session with uBlock Origin Lite content filtering. While this automatically detects HLS master manifests, DASH streams, and direct media URLs on most sites, some complex interactive players may require the user to start playback manually before streams become detectable.

## Digital Rights Management (DRM)
VRKA does not circumvent or decrypt DRM-protected streams (such as Widevine, FairPlay, or PlayReady). If encrypted media segments or license challenge handshakes are detected, extraction stops immediately with an explanatory message.

## Queue Execution
Downloads currently execute sequentially using a single-worker FIFO queue. This design ensures predictable execution order, prevents host connection throttling or IP bans, and guarantees reliable state persistence across application restarts.

## Quality & Source Availability
- **Multi-Factor Selection**: VRKA selects streams by evaluating resolution, frame rate (up to 60 FPS), bitrate, container, and codec efficiency. Newer codecs (such as AV1 or VP9) are evaluated contextually and are never selected over a higher-bitrate source stream of superior fidelity.
- **No Artificial Upscaling**: VRKA only downloads video and audio streams made available by the hosting provider.
- **Frame Rates**: 60 FPS options are selected when provided by the server; otherwise, standard frame rates are used.
- **Audio Conversion**: Transcoding audio to formats such as MP3, Opus, or WAV preserves source fidelity within the limits of the source stream, but cannot reconstruct audio frequencies lost in lossy server compression.

## Platform Support
VRKA is built and packaged for **Windows 10 and Windows 11 (x64)**. Embedded browser-assisted capture requires the Microsoft Edge WebView2 Runtime, which is pre-installed on Windows 11 and Windows 10 (version 2004+).

## Windows SmartScreen & OpenPGP Signatures
- **SmartScreen / Authenticode**: Official release binaries do not currently use a commercial Microsoft Authenticode certificate. Windows SmartScreen may display an unrecognized app warning upon first launch.
- **OpenPGP Release Verification**: VRKA uses detached OpenPGP signatures and SHA-256 checksums (`SHA256SUMS.txt.asc`) as an independent authenticity and integrity mechanism. Users can verify release authenticity against the pinned project key regardless of Windows SmartScreen reputation.
