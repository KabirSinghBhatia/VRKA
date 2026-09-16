#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_PNG="${SCRIPT_DIR}/vrka-wolf-1024.png"
OUTPUT_ICNS="${SCRIPT_DIR}/vrka.icns"
ICONSET_DIR="${SCRIPT_DIR}/vrka.iconset"

if [[ ! -f "${MASTER_PNG}" ]]; then
    echo "Error: Master image not found at ${MASTER_PNG}" >&2
    exit 1
fi

echo "Generating Apple Silicon Retina iconset from ${MASTER_PNG}..."
rm -rf "${ICONSET_DIR}"
mkdir -p "${ICONSET_DIR}"

sips -z 16 16     "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_16x16.png" >/dev/null
sips -z 32 32     "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_16x16@2x.png" >/dev/null
sips -z 32 32     "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_32x32.png" >/dev/null
sips -z 64 64     "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_32x32@2x.png" >/dev/null
sips -z 128 128   "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_128x128.png" >/dev/null
sips -z 256 256   "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_256x256.png" >/dev/null
sips -z 512 512   "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_512x512.png" >/dev/null
sips -z 1024 1024 "${MASTER_PNG}" --out "${ICONSET_DIR}/icon_512x512@2x.png" >/dev/null

echo "Compiling ${OUTPUT_ICNS}..."
iconutil -c icns "${ICONSET_DIR}" -o "${OUTPUT_ICNS}"
rm -rf "${ICONSET_DIR}"

echo "Successfully generated ${OUTPUT_ICNS}"
