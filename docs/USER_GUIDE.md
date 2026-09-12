# VRKA User Guide

---

## Main Interface & Navigation

VRKA provides four primary sections accessible from the sidebar:

### 1. Download
- **URL Input**: Paste a supported video, audio, playlist, or webpage link.
- **Format Options**:
  - **Video**: Downloads the best matching video and audio streams based on your selected resolution and frame rate preferences.
  - **Audio Only**: Extracts and converts audio to MP3 (320, 256, 192, or 128 kbps), Opus, or uncompressed WAV.
- **Advanced Options**:
  - **Playlist Range**: Specify start and end indices to download selected items from a playlist.
  - **Subtitles**: Download embedded or separate subtitle tracks matching your preferred language.
  - **Precision Trim**: Trim media during download by providing start and end timestamps.
  - **Custom Headers**: Provide custom HTTP headers (such as Referer or Origin) for sites that require them.

### 2. Queue
- Displays active and queued downloads in a single-worker FIFO queue.
- Shows real-time progress, download speed, ETA, and current processing stage.
- Includes actions to pause, resume, cancel, or retry downloads.
- Features a selectable activity log and compact UPLINK status information.

### 3. History
- Searchable list of completed downloads.
- Quick actions to open downloaded files directly in your media player or locate them in Windows File Explorer.
- Clear individual items or entire history.

### 4. Settings
- **Download Location**: Choose between **Remember Location** (persists your chosen folder) and **Ask Every Time** (prompts for a folder when starting a download).
- **Fonts**: Switch the interface font between **Monospace** and **System Default**.
- **Theme**: Toggle between Dark and Light interface modes.
- **Component Updates**: Check and update supported yt-dlp, uBlock Origin Lite, and Puemos components with checksum verification.
- **Application Updates**: Check for new VRKA releases, stage updates, and install them with rollback protection.
- **Custom yt-dlp Command**: Enter custom command-line options for yt-dlp with an integrated safety confirmation prompt.
- **Network & Proxy**: Configure custom HTTP or SOCKS5 proxies for downloads.
- **Cookie Import**: Import cookies from supported web browsers or a `cookies.txt` file for authenticated content.
- **Browser Privacy**: Clear stored cookies, DOM storage, and network cache from the browser fallback subsystem.
- **Diagnostics**: Export sanitized diagnostic reports for troubleshooting without exposing private tokens, cookies, or personal paths.
- **About VRKA**: Shows the current version and build, project information, GitHub repository, author information, and third-party notices.

---

## Browser Fallback

When downloading from streaming sites where direct extractors are blocked by bot-detection or dynamic scripts:

1. VRKA automatically opens an isolated **Browser Fallback** session using Microsoft Edge WebView2.
2. The page loads with ad and tracker filtering enabled via uBlock Origin Lite.
3. When video playback begins, VRKA passively detects the stream manifest (HLS, DASH, or direct MP4) and hands it off to the download engine.
4. The browser window closes automatically and the download proceeds in the queue.

---

## Managed Media Runtime

VRKA automatically provisions and manages its media processing tools (yt-dlp and FFmpeg) in `%LOCALAPPDATA%\VRKA\runtime\`.

- **No Manual Setup**: You do not need to install FFmpeg or add it to your system PATH.
- **First-Run Provisioning**: When a download requires stream merging or audio conversion for the first time, VRKA downloads and verifies the official FFmpeg static binaries.
- **Offline Operation**: Once downloaded, all tools run locally and offline.
