# Building VRKA from Source

This guide provides instructions for building and running VRKA on macOS (Apple Silicon / Intel) and Windows 10/11 (x64).

---

## Prerequisites

### macOS (Apple Silicon / Intel)
- **Operating System**: macOS 11.0 (Big Sur) or newer
- **Python**: Version 3.10+ (via Homebrew recommended: `/opt/homebrew/bin/python3`)
- **Git**: For source version control
- **FFmpeg & Deno** *(Optional)*: `brew install ffmpeg deno` (VRKA also provisions FFmpeg automatically if absent)

### Windows
- **Operating System**: Windows 10 or 11 (x64)
- **Python**: Version 3.10+ (64-bit)
- **Git**: For source version control
- **Inno Setup 6** *(Optional)*: Required only if compiling the Windows setup installer

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/MaverickRox/VRKA.git
cd VRKA
```

---

## Step 2: Set Up Virtual Environment

### macOS (Apple Silicon / Intel)
```bash
# Create an isolated Python virtual environment with Homebrew Python
/opt/homebrew/bin/python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows
```powershell
# Create an isolated Python virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Step 3: Run the Application

```bash
# macOS:
.venv/bin/python vrka_qml_app.py

# Windows:
python vrka_qml_app.py
```

---

## Step 4: Run Tests

```bash
# macOS:
.venv/bin/python -m unittest discover -s tests -v

# Windows:
python -m unittest discover -s tests -v
```

---

## Step 5: Compiling Executable Packages

### macOS (Apple Silicon Application Bundle & DMG)
Run the automated build script:
```bash
./build_mac.sh
```
This produces:
- `dist/VRKA.app` (Ad-hoc signed Mach-O arm64 bundle)
- `dist/VRKA-4.5.3-macOS-arm64.dmg` (Distributable disk image)
- `dist/VRKA-4.5.3-macOS-arm64.zip` (Portable ZIP archive)

### Windows (Standalone Executable & Setup Installer)
```powershell
# Standalone EXE
pyinstaller --clean --noconfirm VRKA-Windows.spec

# Full Setup Wizard (requires Inno Setup 6)
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```
