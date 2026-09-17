#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

APP_VERSION="4.5.3"
APP_BUILD="021"
ARCH="$(uname -m)"

echo "=== Building VRKA ${APP_VERSION} (Build ${APP_BUILD}) for macOS (${ARCH}) ==="

# 1. Virtual environment check
if [[ ! -f ".venv/bin/python" ]]; then
    echo "Creating virtual environment at .venv..."
    /opt/homebrew/bin/python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 2. Compile Retina icon if missing
if [[ ! -f "assets/branding/vrka.icns" ]]; then
    echo "Compiling macOS application icon..."
    ./assets/branding/generate_icns.sh
fi

# 3. Clean previous build artifacts
rm -rf build/VRKA dist/VRKA dist/VRKA.app "dist/VRKA-${APP_VERSION}-macOS-${ARCH}.dmg" "dist/VRKA-${APP_VERSION}-macOS-${ARCH}.zip"

# 4. Run PyInstaller
echo "Running PyInstaller with VRKA-Mac.spec (unbundled FFmpeg)..."
.venv/bin/pyinstaller --clean -y VRKA-Mac.spec

if [[ ! -d "dist/VRKA.app" ]]; then
    echo "Error: PyInstaller failed to produce dist/VRKA.app" >&2
    exit 1
fi

# 5. Apple Silicon Ad-Hoc Code Signing
echo "Applying ad-hoc code signing for Apple Silicon..."
codesign --force --deep -s - dist/VRKA.app
codesign --verify --deep --strict dist/VRKA.app
echo "Signature verification passed."

# 6. Create distributable DMG
echo "Packaging dist/VRKA-${APP_VERSION}-macOS-${ARCH}.dmg..."
hdiutil create -volname "VRKA" -srcfolder dist/VRKA.app -ov -format UDZO "dist/VRKA-${APP_VERSION}-macOS-${ARCH}.dmg"

# 7. Create standalone ZIP archive
echo "Packaging dist/VRKA-${APP_VERSION}-macOS-${ARCH}.zip..."
(cd dist && zip -q -r -y "VRKA-${APP_VERSION}-macOS-${ARCH}.zip" VRKA.app)

echo "=== Build Complete ==="
echo "Application Bundle : ${SCRIPT_DIR}/dist/VRKA.app"
echo "DMG Package        : ${SCRIPT_DIR}/dist/VRKA-${APP_VERSION}-macOS-${ARCH}.dmg"
echo "ZIP Archive        : ${SCRIPT_DIR}/dist/VRKA-${APP_VERSION}-macOS-${ARCH}.zip"
