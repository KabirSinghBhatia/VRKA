# -*- mode: python ; coding: utf-8 -*-
"""Native Apple Silicon (arm64) PyInstaller recipe for VRKA macOS application bundle."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_dir = Path(SPECPATH)
datas = []

branding_dir = project_dir / "assets" / "branding"
datas.append((str(branding_dir / "vrka.icns"), "assets/branding"))
datas.append((str(branding_dir / "vrka-wolf-256.png"), "assets/branding"))
datas.append((str(branding_dir / "vrka-wolf-16.png"), "assets/branding"))
datas.append((str(branding_dir / "nav"), "assets/branding/nav"))
datas.append((str(branding_dir / "v2icons"), "assets/branding/v2icons"))
datas.append((str(project_dir / "assets" / "fonts"), "assets/fonts"))
datas.append((str(project_dir / "assets" / "browser_protection"), "assets/browser_protection"))
datas.append((str(project_dir / "third_party" / "media_observer" / "puemos-hls-downloader" / "extension-mv3-chrome-v5.5.0.zip"), "third_party/media_observer/puemos-hls-downloader"))
datas.append((str(project_dir / "THIRD_PARTY_NOTICES.md"), "."))
datas.append((str(project_dir / "vrka_qml" / "qml"), "vrka_qml/qml"))

binaries = []
hiddenimports = []

deno_executable = project_dir / "deno_bin" / "deno"
if deno_executable.is_file():
    binaries.append((str(deno_executable), "deno_bin"))

# Collect required native/networking/crypto dependencies
# Note: FFmpeg and FFprobe binaries are strictly NOT bundled with VRKA to maintain
# a lightweight distribution and isolate external GPL tools across a subprocess boundary.
# FFmpeg is managed at runtime in ~/.vrka/runtime or discovered via Homebrew/PATH.
for package_name in (
    "curl_cffi", "yt_dlp_ejs", "webview", "pgpy", "cryptography",
    "objc", "WebKit", "AppKit", "Foundation"
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

hiddenimports += [
    "yt_dlp", "yt_dlp.extractor", "yt_dlp.version",
    "objc", "WebKit", "AppKit", "Foundation",
    "vrka_platform", "vrka_platform.macos", "vrka_platform.browser.cocoa_wkwebview",
]


a = Analysis(
    [str(project_dir / "vrka_qml_app.py")],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
        "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
        "PySide6.QtDesigner", "PySide6.QtGraphs", "PySide6.QtLocation",
        "PySide6.QtMultimedia", "PySide6.QtMultimediaQuick", "PySide6.QtMultimediaWidgets",
        "PySide6.QtPdf", "PySide6.QtPositioning", "PySide6.QtSensors",
        "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio",
        "PySide6.QtTextToSpeech", "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets", "PySide6.QtWebSockets",
        "PySide6.QtWebView", "PySide6.QtNfc", "PySide6.QtHelp",
        "PySide6.QtSql",
        "tkinter", "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageTk",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VRKA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "branding" / "vrka.icns"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VRKA",
)

app = BUNDLE(
    coll,
    name="VRKA.app",
    icon=str(project_dir / "assets" / "branding" / "vrka.icns"),
    bundle_identifier="com.maverickrox.vrka",
    info_plist={
        "CFBundleName": "VRKA",
        "CFBundleDisplayName": "VRKA",
        "CFBundleGetInfoString": "VRKA Media Downloader",
        "CFBundleIdentifier": "com.maverickrox.vrka",
        "CFBundleVersion": "4.5.3",
        "CFBundleShortVersionString": "4.5.3",
        "NSHighResolutionCapable": "True",
        "LSMinimumSystemVersion": "11.0",
        "NSRequiresAquaSystemAppearance": "False",
    },
)
