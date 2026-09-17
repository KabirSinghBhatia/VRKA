# FFmpeg Compliance & Managed Runtime Architecture

VRKA interfaces with FFmpeg and FFprobe as external subprocess tools for stream remuxing, format merging, audio conversion, and precision trimming.

---

## 1. Unbundled Architecture & Subprocess Isolation

To maintain a lightweight application distribution and strictly respect open-source licensing boundaries, **FFmpeg and FFprobe binaries are never bundled with VRKA release packages** (macOS `.app` bundles, `.dmg` images, standalone `.zip` archives, Windows `.exe` files, or Inno Setup installers).

- **Zero Bundled Binaries**: No FFmpeg executable code is distributed within the application package or source archive.
- **Subprocess Boundary**: VRKA interacts with FFmpeg strictly across standard process pipes and command-line parameters (`--ffmpeg-location`).
- **No Linkage**: No FFmpeg C libraries (`libavcodec`, `libavformat`, `libavutil`, etc.) are statically or dynamically linked into the core VRKA application executable.

---

## 2. Managed Runtime Architecture

FFmpeg and FFprobe binaries are managed separately in the user's isolated local runtime directory:

- **Windows**: `%LOCALAPPDATA%\VRKA\runtime\`
- **macOS & Linux**: `~/.vrka/runtime/`

### Resolution Hierarchy
When media operations require FFmpeg, VRKA searches in the following prioritized order:
1. **Managed Runtime Directory**: Verified binaries previously provisioned in `%LOCALAPPDATA%\VRKA\runtime\` or `~/.vrka/runtime/`.
2. **System Package Managers**: Native platform locations, including macOS Homebrew (`/opt/homebrew/bin` on Apple Silicon, `/usr/local/bin` on Intel) and Linux standard directories (`/usr/bin`, `/usr/local/bin`).
3. **System `PATH`**: Any validated `ffmpeg` and `ffprobe` binaries reachable via the system's `PATH` environment variable.
4. **Local Overrides**: Users may place compatible `ffmpeg` and `ffprobe` binaries into an `ffmpeg_bin/` folder next to the executable to manually override automated resolution.

### Automatic On-Demand Provisioning
If FFmpeg is absent on the system, VRKA provisions a verified static build on first required media operation:
- **Windows (x64)**: Pinned static build from [GyanD/codexffmpeg](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.1) (release `9.0.1-essentials_build`).
- **macOS (Apple Silicon arm64 & Intel x86_64)**: Version-pinned native static build.
- **Cryptographic Integrity Verification**: Every downloaded runtime archive is verified against an immutable, hardcoded SHA-256 checksum before extraction and activation.
- **Offline Operation**: Once provisioned, the local runtime is stored and reused for all subsequent operations without requiring further network access.

---

## 3. Licensing & Open-Source Compliance

- **FFmpeg Licensing**: FFmpeg is licensed under the GNU Lesser General Public License (LGPL) version 2.1 or later, or GNU General Public License (GPL) version 2 or later depending on enabled codecs (e.g., `libx264`, `libx265`).
- **Distribution Independence**: Because VRKA distributions do **not** convey, package, or distribute FFmpeg binaries, VRKA releases do not trigger GPL binary conveyance obligations under GPLv2 §3 or GPLv3 §6.
- **Upstream Source Availability**: Upstream FFmpeg source code and build recipes are available directly from the official upstream project:
  - FFmpeg Official Website: [https://ffmpeg.org/](https://ffmpeg.org/)
  - FFmpeg Source Repository: [https://git.ffmpeg.org/ffmpeg.git](https://git.ffmpeg.org/ffmpeg.git)
  - GyanD Windows Build Recipes: [https://github.com/GyanD/codexffmpeg](https://github.com/GyanD/codexffmpeg)
