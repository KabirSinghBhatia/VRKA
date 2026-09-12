# Troubleshooting Guide

---

## Common Issues & Solutions

### A Specific Website Fails to Download
1. Open **Settings** > **Component Updates**.
2. Check for an update to yt-dlp and apply it if available.
3. Retry the download.
4. If direct extraction still fails, allow VRKA to attempt Browser Fallback.

### Audio Extraction or Merging Fails
- VRKA provisions FFmpeg automatically in `%LOCALAPPDATA%\VRKA\runtime\`. If first-run provisioning was interrupted by a network drop, retry the download while connected to the internet.
- Alternatively, you can place compatible `ffmpeg.exe` and `ffprobe.exe` binaries into an `ffmpeg_bin/` folder next to `VRKA.exe`.
- Verify that your output drive has sufficient free storage space for temporary conversion files.

### Windows Defender SmartScreen Warning
- Official VRKA release packages include detached OpenPGP signatures. Windows SmartScreen may display an unrecognized app notice because release binaries do not use a commercial Authenticode certificate.
- Click **More info** and select **Run anyway** to launch.
- You can verify package integrity and authenticity by checking the SHA-256 hash against `SHA256SUMS.txt` and verifying the detached signature (`SHA256SUMS.txt.asc`) using the project's public key.

### WebView2 / Browser Fallback Does Not Open
- Ensure the Microsoft Edge WebView2 Runtime is installed. It is pre-installed on Windows 11 and Windows 10 (version 2004 and newer).

---

## Submitting an Issue

If a problem persists, submit an issue on [GitHub Issues](https://github.com/MaverickRox/VRKA/issues/new/choose):
- Include your VRKA version (`4.5.0 Build 018`) and Windows version.
- Provide steps to reproduce the issue.
- Export and attach a sanitized report from **Settings** > **Diagnostics**, or paste relevant log output with any personal paths, tokens, or cookies removed.
