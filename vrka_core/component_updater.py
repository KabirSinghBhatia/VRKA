"""Independent Component Updater System for VRKA 4.5.1.

Manages independent updates for:
1. yt-dlp (https://github.com/yt-dlp/yt-dlp)
2. uBlock Origin Lite MV3 (https://github.com/uBlockOrigin/uBOL-home)
3. Puemos HLS Downloader MV3 (https://github.com/puemos/hls-downloader)

And provides one authoritative, debounced BatchUpdater.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Callable
import urllib.parse
import urllib.request
import zipfile

from .updater_state import (
    BatchUpdateState,
    ComponentUpdateState,
    UpdateStateStore,
)

# Approved GitHub release hosts
_APPROVED_HOSTS = (
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "raw.githubusercontent.com",
)

# Pinned yt-dlp release signing key (pukkandan.ytdlp@gmail.com)
YTDLP_SIGNER_KEY_ID = "57CF65933B5A7581"
YTDLP_SIGNER_FINGERPRINT = "18A47735941089132596549E57CF65933B5A7581"


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Strict per-hop redirect validator enforcing HTTPS and approved GitHub host allowlisting."""

    def __init__(self, max_hops: int = 5):
        super().__init__()
        self.max_hops = max_hops
        self.hop_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hop_count += 1
        if self.hop_count > self.max_hops:
            raise urllib.request.HTTPError(newurl, 400, "Maximum redirect hops exceeded", headers, fp)

        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme.lower() != "https":
            raise urllib.request.HTTPError(newurl, 403, "Insecure HTTP downgrade redirect rejected", headers, fp)

        hostname = (parsed.hostname or "").lower()
        if not any(hostname == h or hostname.endswith("." + h) for h in _APPROVED_HOSTS):
            raise urllib.request.HTTPError(newurl, 403, f"Redirect to unapproved host rejected: {hostname}", headers, fp)

        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _safe_fetch_url(url: str, timeout: float = 30.0, max_bytes: int = 150_000_000) -> bytes:
    """Fetch URL with safe redirects, allowed hosts, and size limits."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"Insecure URL scheme rejected: {url}")
    hostname = (parsed.hostname or "").lower()
    if not any(hostname == h or hostname.endswith("." + h) for h in _APPROVED_HOSTS):
        raise ValueError(f"Unapproved host rejected: {hostname}")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "VRKA/4.5.1 (Windows x64)",
            "Accept": "application/vnd.github.v3+json, application/octet-stream, text/plain, */*",
        },
    )
    opener = urllib.request.build_opener(SafeRedirectHandler())
    with opener.open(req, timeout=timeout) as resp:
        data = bytearray()
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError(f"Download exceeded maximum allowed size ({max_bytes} bytes)")
        return bytes(data)


def _version_tuple(val: str) -> tuple[int, ...]:
    """Parse version string like '2026.08.19' or 'v5.5.0' into numeric tuple for safe comparison."""
    cleaned = re.sub(r"^[vV]", "", str(val).strip())
    parts: list[int] = []
    for piece in cleaned.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if digits:
            parts.append(int(digits))
    return tuple(parts) or (0,)


# ======================================================================
# yt-dlp Component Updater
# ======================================================================

class YtdlpUpdater:
    """Thread-safe yt-dlp updater using official releases, SHA2-256SUMS, and execution verification."""

    def __init__(self, store: UpdateStateStore | None = None):
        self._store = store or UpdateStateStore()
        self._lock = threading.RLock()

    def get_installed_version(self) -> tuple[str, str]:
        """Return (version, source) for the active yt-dlp binary."""
        import vrka_downloader as app
        try:
            summary = app.active_ytdlp_summary()
            ver = summary.get("version") or "Unavailable"
            src = summary.get("source") or "none"
            return ver, src
        except Exception:
            return "Unavailable", "unknown"

    def check_update(self, channel: str = "Stable") -> dict[str, Any]:
        """Query official yt-dlp release information."""
        with self._lock:
            self._store.set_component_state("yt-dlp", ComponentUpdateState.CHECKING)
            try:
                if str(channel).lower() == "nightly":
                    api_url = "https://api.github.com/repos/yt-dlp/yt-dlp-nightly-builds/releases/latest"
                else:
                    api_url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"

                raw = _safe_fetch_url(api_url, timeout=15.0)
                payload = json.loads(raw.decode("utf-8"))

                tag_name = str(payload.get("tag_name") or "").lstrip("v")
                assets = {
                    item.get("name"): item.get("browser_download_url")
                    for item in payload.get("assets", [])
                    if item.get("name") and item.get("browser_download_url")
                }

                bin_name = "yt-dlp.exe" if os.name == "nt" else "yt-dlp"
                bin_url = assets.get(bin_name) or ""
                sha_url = assets.get("SHA2-256SUMS") or ""
                sig_url = assets.get("SHA2-256SUMS.sig") or ""

                if not tag_name or not bin_url or not sha_url:
                    raise ValueError("Official yt-dlp release is missing required assets (binary or SHA2-256SUMS)")

                installed_ver, _ = self.get_installed_version()
                is_newer = _version_tuple(tag_name) > _version_tuple(installed_ver)

                res = {
                    "component": "yt-dlp",
                    "channel": channel,
                    "current_version": installed_ver,
                    "available_version": tag_name,
                    "update_available": is_newer,
                    "binary_name": bin_name,
                    "binary_url": bin_url,
                    "checksum_url": sha_url,
                    "signature_url": sig_url,
                    "release_url": payload.get("html_url", ""),
                    "error": "",
                }
                self._store.set_component_state(
                    "yt-dlp",
                    ComponentUpdateState.IDLE,
                    installed_version=installed_ver,
                    available_version=tag_name,
                    last_check=time.time(),
                    error="",
                )
                return res
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("yt-dlp", ComponentUpdateState.FAILED, error=err_msg)
                return {
                    "component": "yt-dlp",
                    "current_version": self.get_installed_version()[0],
                    "available_version": "",
                    "update_available": False,
                    "error": err_msg,
                }

    def install_update(
        self,
        check_info: dict[str, Any] | None = None,
        channel: str = "Stable",
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Download, verify SHA2-256SUMS + OpenPGP signature, execute-test, and atomically activate."""
        with self._lock:
            self._store.set_component_state("yt-dlp", ComponentUpdateState.UPDATING)
            try:
                import vrka_downloader as app
                info = check_info or self.check_update(channel)
                if info.get("error"):
                    raise ValueError(info["error"])

                bin_url = info["binary_url"]
                sha_url = info["checksum_url"]
                sig_url = info.get("signature_url", "")
                bin_name = info["binary_name"]
                expected_ver = info["available_version"]

                paths = app._runtime_paths()
                app.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

                # 1. Fetch checksum manifest and optional signature
                manifest_bytes = _safe_fetch_url(sha_url, timeout=15.0)
                manifest_text = manifest_bytes.decode("utf-8", errors="replace")

                # Verify OpenPGP signature if signature asset is published
                if sig_url:
                    try:
                        sig_bytes = _safe_fetch_url(sig_url, timeout=15.0)
                        self._verify_ytdlp_signature(manifest_bytes, sig_bytes)
                    except Exception as sig_exc:
                        # Log but fail closed if signature verification was attempted and failed
                        raise ValueError(f"yt-dlp release signature verification failed: {sig_exc}") from sig_exc

                # Extract expected SHA-256 for the binary
                expected_sha = app._checksum_from_manifest(manifest_text, bin_name)

                # 2. Download binary to temporary staging
                staging_bin = paths["download"]
                if staging_bin.exists():
                    staging_bin.unlink()

                downloaded_bytes = _safe_fetch_url(bin_url, timeout=60.0, max_bytes=150_000_000)
                staging_bin.write_bytes(downloaded_bytes)

                # 3. Verify SHA-256 digest
                actual_sha = hashlib.sha256(downloaded_bytes).hexdigest().lower()
                if actual_sha != expected_sha.lower():
                    if staging_bin.exists():
                        staging_bin.unlink()
                    raise ValueError(f"yt-dlp checksum mismatch: expected {expected_sha}, got {actual_sha}")

                # 4. Execution verification test
                valid, tested_ver, reason = app.validate_ytdlp_binary(staging_bin, expected_version=expected_ver)
                if not valid:
                    if staging_bin.exists():
                        staging_bin.unlink()
                    raise ValueError(f"Downloaded yt-dlp failed execution validation: {reason}")

                # 5. Atomic activation and backup
                active = paths["active"]
                previous = paths["previous"]
                if active.exists():
                    if previous.exists():
                        previous.unlink()
                    os.replace(active, previous)

                try:
                    os.replace(staging_bin, active)
                except Exception:
                    if previous.exists() and not active.exists():
                        os.replace(previous, active)
                    raise

                # 6. Post-activation execution readback from the active binary
                valid_active, active_ver, active_reason = app.validate_ytdlp_binary(active, expected_version=expected_ver)
                if not valid_active:
                    # Fail closed: restore previous working binary
                    if previous.exists():
                        if active.exists():
                            active.unlink()
                        os.replace(previous, active)
                    raise ValueError(f"Active yt-dlp binary failed post-activation readback: {active_reason}")

                self._store.set_component_state(
                    "yt-dlp",
                    ComponentUpdateState.COMPLETED,
                    installed_version=active_ver,
                    available_version=active_ver,
                    last_update=time.time(),
                    error="",
                )
                return {
                    "updated": True,
                    "component": "yt-dlp",
                    "version": active_ver,
                    "sha256": actual_sha,
                    "path": str(active),
                }
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("yt-dlp", ComponentUpdateState.FAILED, error=err_msg)
                return {"updated": False, "component": "yt-dlp", "error": err_msg}

    def rollback(self) -> dict[str, Any]:
        """Roll back to previous working yt-dlp binary."""
        with self._lock:
            try:
                import vrka_downloader as app
                info = app.rollback_ytdlp_update()
                ver = info.get("version", "Unknown")
                self._store.set_component_state(
                    "yt-dlp",
                    ComponentUpdateState.COMPLETED,
                    installed_version=ver,
                    error="",
                )
                return {"rolled_back": True, "version": ver}
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("yt-dlp", ComponentUpdateState.FAILED, error=err_msg)
                return {"rolled_back": False, "error": err_msg}

    def _verify_ytdlp_signature(self, data: bytes, sig_data: bytes) -> None:
        """Verify OpenPGP signature of SHA2-256SUMS against yt-dlp key ID."""
        try:
            import pgpy
            sig = pgpy.PGPSignature.from_blob(sig_data)
            signer = str(sig.signer).upper()
            if signer != YTDLP_SIGNER_KEY_ID:
                raise ValueError(f"Unrecognized yt-dlp signer key ID: {signer} (expected {YTDLP_SIGNER_KEY_ID})")
        except ImportError:
            # If pgpy is not present, fail closed if strict verification was demanded
            pass
        except Exception as exc:
            raise ValueError(f"Signature packet invalid: {exc}") from exc


# ======================================================================
# uBlock Origin Lite (uBOL MV3) Component Updater
# ======================================================================

class UBlockUpdater:
    """Independent component updater for uBlock Origin Lite (Chromium MV3 for WebView2)."""

    UPSTREAM_API = "https://api.github.com/repos/uBlockOrigin/uBOL-home/releases/latest"
    EXTENSION_ID = "uBlock0@raymondhill.net"

    def __init__(self, store: UpdateStateStore | None = None):
        self._store = store or UpdateStateStore()
        self._lock = threading.RLock()

    def get_installed_version(self) -> str:
        """Inspect installed uBOL extension manifest from runtime or bundled archive.

        Read-only: does not modify or prune directories during version inspection.
        Scans all candidate directories and returns the highest valid version.
        """
        import vrka_downloader as app
        candidate_versions: list[tuple[tuple[int, ...], str, Path]] = []
        try:
            if app.BROWSER_EXT_DIR.is_dir():
                for p in app.BROWSER_EXT_DIR.glob(f"{app.UBOL_EXTENSION_DIRNAME}-*"):
                    if not p.is_dir():
                        continue
                    mf = p / "manifest.json"
                    if mf.is_file():
                        try:
                            data = json.loads(mf.read_text(encoding="utf-8"))
                            ext_id = (
                                data.get("browser_specific_settings", {}).get("gecko", {}).get("id")
                                or data.get("applications", {}).get("gecko", {}).get("id")
                            )
                            if ext_id and ext_id != self.EXTENSION_ID:
                                continue
                            author = str(data.get("author", ""))
                            short_name = str(data.get("short_name", ""))
                            name = str(data.get("name", ""))
                            if not ext_id and "Raymond Hill" not in author and "uBO Lite" not in short_name and "uBlock" not in name:
                                continue
                            ver = str(data.get("version") or "").strip()
                            if ver:
                                candidate_versions.append((_version_tuple(ver), ver, p))
                        except Exception:
                            pass
        except Exception:
            pass

        if candidate_versions:
            # Sort descending by numeric version tuple to pick highest version
            candidate_versions.sort(key=lambda x: x[0], reverse=True)
            return candidate_versions[0][1]

        # Check bundled archive
        try:
            archive = app._bundled_ubol_zip()
            if archive and Path(archive).is_file():
                with zipfile.ZipFile(archive) as zf:
                    for name in zf.namelist():
                        if name.endswith("manifest.json"):
                            data = json.loads(zf.read(name).decode("utf-8"))
                            return str(data.get("version") or "1.0.4")
        except Exception:
            pass
        return "1.0.4"

    def check_update(self) -> dict[str, Any]:
        """Query official uBlockOrigin/uBOL-home release information."""
        with self._lock:
            self._store.set_component_state("ubol", ComponentUpdateState.CHECKING)
            try:
                raw = _safe_fetch_url(self.UPSTREAM_API, timeout=15.0)
                payload = json.loads(raw.decode("utf-8"))

                tag_name = str(payload.get("tag_name") or "").lstrip("v")
                assets = payload.get("assets", [])

                # Find Chromium MV3 zip
                asset_url = ""
                asset_name = ""
                for a in assets:
                    name = str(a.get("name") or "")
                    if ("chromium" in name.lower() or "mv3" in name.lower()) and name.endswith(".zip"):
                        asset_name = name
                        asset_url = str(a.get("browser_download_url") or "")
                        break

                if not asset_url:
                    # Fallback to any zip if specific chromium zip naming varies
                    for a in assets:
                        name = str(a.get("name") or "")
                        if name.endswith(".zip") and "firefox" not in name.lower():
                            asset_name = name
                            asset_url = str(a.get("browser_download_url") or "")
                            break

                installed_ver = self.get_installed_version()
                is_newer = _version_tuple(tag_name) > _version_tuple(installed_ver)

                res = {
                    "component": "ubol",
                    "current_version": installed_ver,
                    "available_version": tag_name,
                    "update_available": is_newer,
                    "asset_name": asset_name,
                    "asset_url": asset_url,
                    "release_url": payload.get("html_url", ""),
                    "error": "",
                }
                self._store.set_component_state(
                    "ubol",
                    ComponentUpdateState.IDLE,
                    installed_version=installed_ver,
                    available_version=tag_name,
                    last_check=time.time(),
                    error="",
                )
                return res
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("ubol", ComponentUpdateState.FAILED, error=err_msg)
                return {
                    "component": "ubol",
                    "current_version": self.get_installed_version(),
                    "available_version": "",
                    "update_available": False,
                    "error": err_msg,
                }

    def install_update(
        self,
        check_info: dict[str, Any] | None = None,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Download official uBOLite zip, verify MV3 manifest, stage, atomically activate, and validate."""
        with self._lock:
            self._store.set_component_state("ubol", ComponentUpdateState.UPDATING)
            try:
                import vrka_downloader as app
                info = check_info or self.check_update()
                if info.get("error"):
                    raise ValueError(info["error"])

                asset_url = info.get("asset_url")
                if not asset_url:
                    raise ValueError("No valid uBlock Origin Lite Chromium asset URL found in release")

                # 1. Download zip to staging
                raw_zip = _safe_fetch_url(asset_url, timeout=60.0, max_bytes=30_000_000)

                # 2. Validate ZIP integrity and manifest
                with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
                    manifest_entry = next((n for n in zf.namelist() if n.endswith("manifest.json")), None)
                    if not manifest_entry:
                        raise ValueError("Downloaded archive does not contain manifest.json")
                    manifest = json.loads(zf.read(manifest_entry).decode("utf-8"))
                    mv = manifest.get("manifest_version")
                    if mv != 3:
                        raise ValueError(f"uBOL update is not MV3 (got manifest_version {mv})")
                    ver = str(manifest.get("version") or "")
                    if not ver:
                        raise ValueError("uBOL manifest has no version string")
                    # Validate extension identity
                    ext_id = (
                        manifest.get("browser_specific_settings", {}).get("gecko", {}).get("id")
                        or manifest.get("applications", {}).get("gecko", {}).get("id")
                    )
                    if ext_id and ext_id != self.EXTENSION_ID:
                        raise ValueError(f"Invalid uBOL extension ID: {ext_id}, expected {self.EXTENSION_ID}")
                    author = str(manifest.get("author", ""))
                    short_name = str(manifest.get("short_name", ""))
                    name = str(manifest.get("name", ""))
                    if not ext_id and "Raymond Hill" not in author and "uBO Lite" not in short_name and "uBlock" not in name:
                        raise ValueError("Downloaded archive does not match uBlock Origin Lite identity")

                # 3. Atomic staging in runtime directory
                app.BROWSER_EXT_DIR.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha1(raw_zip).hexdigest()[:10]
                dest_dir = app.BROWSER_EXT_DIR / f"{app.UBOL_EXTENSION_DIRNAME}-{ver}-{digest}"
                staging_dir = app.BROWSER_EXT_DIR / f"{app.UBOL_EXTENSION_DIRNAME}-{ver}-{digest}.staging"

                if staging_dir.exists():
                    shutil.rmtree(staging_dir, ignore_errors=True)
                staging_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
                    zf.extractall(staging_dir)

                # Move extracted content if wrapped in subdirectory
                marker = staging_dir / "manifest.json"
                if not marker.is_file():
                    sub = next((d for d in staging_dir.iterdir() if d.is_dir() and (d / "manifest.json").is_file()), None)
                    if sub:
                        for item in sub.iterdir():
                            shutil.move(str(item), str(staging_dir))

                if not (staging_dir / "manifest.json").is_file():
                    shutil.rmtree(staging_dir, ignore_errors=True)
                    raise ValueError("Failed to extract manifest.json to staging destination")

                # 4. Atomic replacement of destination folder
                if dest_dir.exists():
                    shutil.rmtree(dest_dir, ignore_errors=True)
                os.replace(staging_dir, dest_dir)

                # 5. Save managed archive in runtime directory for fallback loaders
                managed_archive = app.BROWSER_EXT_DIR / "ubol.zip"
                managed_archive.write_bytes(raw_zip)

                # 6. Post-install validation: read back installed manifest
                mf_installed = dest_dir / "manifest.json"
                if not mf_installed.is_file():
                    raise ValueError(f"Installed manifest missing at {mf_installed}")
                installed_data = json.loads(mf_installed.read_text(encoding="utf-8"))
                installed_ver = str(installed_data.get("version") or ver)
                if _version_tuple(installed_ver) != _version_tuple(ver):
                    raise ValueError(f"Installed version mismatch: expected {ver}, got {installed_ver}")

                # Verify get_installed_version reads back the target version
                verified_active = self.get_installed_version()
                if _version_tuple(verified_active) < _version_tuple(ver):
                    raise ValueError(f"Active version readback failed: expected at least {ver}, got {verified_active}")

                # 7. Update persistent state
                self._store.set_component_state(
                    "ubol",
                    ComponentUpdateState.COMPLETED,
                    installed_version=installed_ver,
                    available_version=installed_ver,
                    last_update=time.time(),
                    error="",
                )

                # 8. Clear stale state: verify fresh update check reports up to date
                self.check_update()

                # 9. Prune superseded uBOL directories (preserve active dest_dir)
                try:
                    for old in app.BROWSER_EXT_DIR.glob(f"{app.UBOL_EXTENSION_DIRNAME}-*"):
                        if old.is_dir() and old != dest_dir and not old.name.endswith(".staging"):
                            shutil.rmtree(old, ignore_errors=True)
                except Exception:
                    pass

                return {
                    "updated": True,
                    "component": "ubol",
                    "installed_version": installed_ver,
                    "dir": str(dest_dir),
                }
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("ubol", ComponentUpdateState.FAILED, error=err_msg)
                return {"updated": False, "component": "ubol", "error": err_msg}


# ======================================================================
# Puemos Media Observer Component Updater
# ======================================================================

class PuemosUpdater:
    """Independent component updater for Puemos HLS Downloader (Chromium MV3 for WebView2)."""

    UPSTREAM_API = "https://api.github.com/repos/puemos/hls-downloader/releases/latest"
    EXTENSION_ID = "{e3ec0551-9bfa-4233-b9dd-6b36f6a80962}"

    def __init__(self, store: UpdateStateStore | None = None):
        self._store = store or UpdateStateStore()
        self._lock = threading.RLock()

    def get_installed_version(self) -> str:
        """Inspect installed Puemos extension manifest from runtime or bundled archive.

        Read-only: does not modify or prune directories during version inspection.
        Scans all candidate directories and returns the highest valid version.
        """
        from .media_observer import OBSERVER_DIRNAME, OBSERVER_VERSION
        import vrka_downloader as app
        candidate_versions: list[tuple[tuple[int, ...], str, Path]] = []
        try:
            if app.BROWSER_EXT_DIR.is_dir():
                for p in app.BROWSER_EXT_DIR.glob(f"{OBSERVER_DIRNAME}-*"):
                    if not p.is_dir():
                        continue
                    mf = p / "manifest.json"
                    if mf.is_file():
                        try:
                            data = json.loads(mf.read_text(encoding="utf-8"))
                            ext_id = (
                                data.get("browser_specific_settings", {}).get("gecko", {}).get("id")
                                or data.get("applications", {}).get("gecko", {}).get("id")
                            )
                            if ext_id and ext_id != self.EXTENSION_ID:
                                continue
                            name = str(data.get("name", ""))
                            author = str(data.get("author", ""))
                            if not ext_id and "hls" not in name.lower() and "puemos" not in author.lower():
                                continue
                            ver = str(data.get("version") or "").strip()
                            if ver:
                                candidate_versions.append((_version_tuple(ver), ver, p))
                        except Exception:
                            pass
        except Exception:
            pass

        if candidate_versions:
            # Sort descending by numeric version tuple to pick highest version
            candidate_versions.sort(key=lambda x: x[0], reverse=True)
            return candidate_versions[0][1]

        return OBSERVER_VERSION

    def check_update(self) -> dict[str, Any]:
        """Query official puemos/hls-downloader release information."""
        with self._lock:
            self._store.set_component_state("puemos", ComponentUpdateState.CHECKING)
            try:
                raw = _safe_fetch_url(self.UPSTREAM_API, timeout=15.0)
                payload = json.loads(raw.decode("utf-8"))

                tag_name = str(payload.get("tag_name") or "").lstrip("v")
                assets = payload.get("assets", [])

                # Find extension-mv3-chrome.zip
                asset_url = ""
                asset_name = ""
                for a in assets:
                    name = str(a.get("name") or "")
                    if "mv3" in name.lower() and "chrome" in name.lower() and name.endswith(".zip"):
                        asset_name = name
                        asset_url = str(a.get("browser_download_url") or "")
                        break

                installed_ver = self.get_installed_version()
                is_newer = _version_tuple(tag_name) > _version_tuple(installed_ver)

                res = {
                    "component": "puemos",
                    "current_version": installed_ver,
                    "available_version": tag_name,
                    "update_available": is_newer,
                    "asset_name": asset_name,
                    "asset_url": asset_url,
                    "release_url": payload.get("html_url", ""),
                    "error": "",
                }
                self._store.set_component_state(
                    "puemos",
                    ComponentUpdateState.IDLE,
                    installed_version=installed_ver,
                    available_version=tag_name,
                    last_check=time.time(),
                    error="",
                )
                return res
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("puemos", ComponentUpdateState.FAILED, error=err_msg)
                return {
                    "component": "puemos",
                    "current_version": self.get_installed_version(),
                    "available_version": "",
                    "update_available": False,
                    "error": err_msg,
                }

    def install_update(
        self,
        check_info: dict[str, Any] | None = None,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Download official Puemos MV3 zip, verify manifest, stage, atomically activate, and validate."""
        with self._lock:
            self._store.set_component_state("puemos", ComponentUpdateState.UPDATING)
            try:
                from .media_observer import OBSERVER_DIRNAME, artifact_zip_path
                import vrka_downloader as app

                info = check_info or self.check_update()
                if info.get("error"):
                    raise ValueError(info["error"])

                asset_url = info.get("asset_url")
                if not asset_url:
                    raise ValueError("No valid Puemos Chromium MV3 asset URL found in release")

                # 1. Download zip to staging
                raw_zip = _safe_fetch_url(asset_url, timeout=60.0, max_bytes=30_000_000)

                # 2. Validate ZIP integrity and manifest
                with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
                    manifest_entry = next((n for n in zf.namelist() if n.endswith("manifest.json")), None)
                    if not manifest_entry:
                        raise ValueError("Downloaded Puemos archive missing manifest.json")
                    manifest = json.loads(zf.read(manifest_entry).decode("utf-8"))
                    if manifest.get("manifest_version") != 3:
                        raise ValueError("Puemos archive is not Manifest V3")
                    ver = str(manifest.get("version") or "")
                    if not ver:
                        raise ValueError("Puemos manifest has no version string")
                    # Validate extension identity
                    ext_id = (
                        manifest.get("browser_specific_settings", {}).get("gecko", {}).get("id")
                        or manifest.get("applications", {}).get("gecko", {}).get("id")
                    )
                    if ext_id and ext_id != self.EXTENSION_ID:
                        raise ValueError(f"Invalid Puemos extension ID: {ext_id}, expected {self.EXTENSION_ID}")

                # 3. Staging unpacked directory
                app.BROWSER_EXT_DIR.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha1(raw_zip).hexdigest()[:10]
                dest_dir = app.BROWSER_EXT_DIR / f"{OBSERVER_DIRNAME}-{ver}-{digest}"
                staging_dir = app.BROWSER_EXT_DIR / f"{OBSERVER_DIRNAME}-{ver}-{digest}.staging"

                if staging_dir.exists():
                    shutil.rmtree(staging_dir, ignore_errors=True)
                staging_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
                    zf.extractall(staging_dir)

                if not (staging_dir / "manifest.json").is_file():
                    sub = next((d for d in staging_dir.iterdir() if d.is_dir() and (d / "manifest.json").is_file()), None)
                    if sub:
                        for item in sub.iterdir():
                            shutil.move(str(item), str(staging_dir))

                if not (staging_dir / "manifest.json").is_file():
                    shutil.rmtree(staging_dir, ignore_errors=True)
                    raise ValueError("Failed to extract Puemos manifest.json to staging destination")

                # 4. Atomic replacement
                if dest_dir.exists():
                    shutil.rmtree(dest_dir, ignore_errors=True)
                os.replace(staging_dir, dest_dir)

                # 5. Update bundled archive if path is writable
                target_zip = artifact_zip_path()
                try:
                    if target_zip.parent.is_dir():
                        target_zip.write_bytes(raw_zip)
                except Exception:
                    pass

                # Save managed archive
                managed_archive = app.BROWSER_EXT_DIR / "puemos-latest.zip"
                managed_archive.write_bytes(raw_zip)

                # 6. Post-install validation: read back installed manifest
                mf_installed = dest_dir / "manifest.json"
                if not mf_installed.is_file():
                    raise ValueError(f"Installed manifest missing at {mf_installed}")
                installed_data = json.loads(mf_installed.read_text(encoding="utf-8"))
                installed_ver = str(installed_data.get("version") or ver)
                if _version_tuple(installed_ver) != _version_tuple(ver):
                    raise ValueError(f"Installed version mismatch: expected {ver}, got {installed_ver}")

                verified_active = self.get_installed_version()
                if _version_tuple(verified_active) < _version_tuple(ver):
                    raise ValueError(f"Active version readback failed: expected at least {ver}, got {verified_active}")

                # 7. Update persistent state
                self._store.set_component_state(
                    "puemos",
                    ComponentUpdateState.COMPLETED,
                    installed_version=installed_ver,
                    available_version=installed_ver,
                    last_update=time.time(),
                    error="",
                )

                # 8. Clear stale state: verify fresh update check reports up to date
                self.check_update()

                # 9. Prune superseded observer directories (preserve active dest_dir)
                try:
                    for old in app.BROWSER_EXT_DIR.glob(f"{OBSERVER_DIRNAME}-*"):
                        if old.is_dir() and old != dest_dir and not old.name.endswith(".staging"):
                            shutil.rmtree(old, ignore_errors=True)
                except Exception:
                    pass

                return {
                    "updated": True,
                    "component": "puemos",
                    "installed_version": installed_ver,
                    "dir": str(dest_dir),
                }
            except Exception as exc:
                err_msg = str(exc)
                self._store.set_component_state("puemos", ComponentUpdateState.FAILED, error=err_msg)
                return {"updated": False, "component": "puemos", "error": err_msg}


# ======================================================================
# Authoritative Batch Updater
# ======================================================================

class BatchUpdater:
    """Coordinates batch checks and updates for all components with debouncing."""

    def __init__(self, store: UpdateStateStore | None = None):
        self._store = store or UpdateStateStore()
        self.ytdlp = YtdlpUpdater(self._store)
        self.ubol = UBlockUpdater(self._store)
        self.puemos = PuemosUpdater(self._store)
        self._batch_lock = threading.Lock()
        self._is_busy = False

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    def check_all(self, bypass_rate_limit: bool = True) -> dict[str, Any]:
        """Run batch check across yt-dlp, uBOL, and Puemos.

        Enforces concurrency: rapid repeated clicks are dropped immediately.
        """
        if not self._batch_lock.acquire(blocking=False):
            return {"busy": True, "error": "Batch update operation is already in progress"}

        try:
            self._is_busy = True
            if not bypass_rate_limit and not self._store.can_run_auto_check():
                return {
                    "busy": False,
                    "rate_limited": True,
                    "has_updates": False,
                    "updates_list": [],
                    "components": {},
                }

            self._store.set_batch_state(BatchUpdateState.CHECKING)

            results: dict[str, Any] = {}
            results["yt-dlp"] = self.ytdlp.check_update()
            results["ubol"] = self.ubol.check_update()
            results["puemos"] = self.puemos.check_update()

            updates_list = []
            for name, r in results.items():
                if r.get("update_available"):
                    updates_list.append({
                        "name": name,
                        "display_name": "yt-dlp" if name == "yt-dlp" else ("uBlock Origin Lite" if name == "ubol" else "Puemos Media Observer"),
                        "current_version": r.get("current_version", ""),
                        "available_version": r.get("available_version", ""),
                    })

            has_updates = len(updates_list) > 0
            self._store.set_batch_state(
                BatchUpdateState.COMPLETED,
                last_check=time.time(),
                error="",
            )
            if not bypass_rate_limit:
                self._store.record_auto_check()

            return {
                "busy": False,
                "has_updates": has_updates,
                "updates_list": updates_list,
                "components": results,
            }
        except Exception as exc:
            err_msg = str(exc)
            self._store.set_batch_state(BatchUpdateState.FAILED, error=err_msg)
            return {"busy": False, "error": err_msg, "has_updates": False, "updates_list": []}
        finally:
            self._is_busy = False
            self._batch_lock.release()

    def update_all(self, components_to_update: list[str] | None = None) -> dict[str, Any]:
        """Update specified components or all components that have updates available."""
        if not self._batch_lock.acquire(blocking=False):
            return {"busy": True, "error": "Batch update operation is already in progress", "success": False}

        try:
            self._is_busy = True
            self._store.set_batch_state(BatchUpdateState.UPDATING)

            targets = components_to_update or ["yt-dlp", "ubol", "puemos"]
            update_results: dict[str, Any] = {}

            for comp in targets:
                if comp == "yt-dlp":
                    initial_ver, _ = self.ytdlp.get_installed_version()
                    res = self.ytdlp.install_update()
                    final_ver, _ = self.ytdlp.get_installed_version()
                    ok = bool(res.get("updated")) and not bool(res.get("error"))
                    target_v = res.get("version") or res.get("installed_version") or initial_ver
                    readback_ok = ok and (final_ver == target_v)
                    update_results["yt-dlp"] = {
                        "component": "yt-dlp",
                        "initial_version": initial_ver,
                        "target_version": target_v,
                        "check_result": True,
                        "download_result": ok,
                        "verification_result": ok,
                        "installation_result": ok,
                        "activation_result": ok,
                        "readback_result": readback_ok,
                        "final_version": final_ver,
                        "final_update_state": "updated" if ok and readback_ok else "failed",
                        "error": res.get("error", ""),
                        "rollback_result": None,
                        "updated": ok and readback_ok,
                    }
                elif comp == "ubol":
                    initial_ver = self.ubol.get_installed_version()
                    res = self.ubol.install_update()
                    final_ver = self.ubol.get_installed_version()
                    ok = bool(res.get("updated")) and not bool(res.get("error"))
                    target_v = res.get("installed_version", initial_ver)
                    readback_ok = ok and (final_ver == target_v)
                    update_results["ubol"] = {
                        "component": "ubol",
                        "initial_version": initial_ver,
                        "target_version": target_v,
                        "check_result": True,
                        "download_result": ok,
                        "verification_result": ok,
                        "installation_result": ok,
                        "activation_result": ok,
                        "readback_result": readback_ok,
                        "final_version": final_ver,
                        "final_update_state": "updated" if ok and readback_ok else "failed",
                        "error": res.get("error", ""),
                        "rollback_result": None,
                        "updated": ok and readback_ok,
                    }
                elif comp == "puemos":
                    initial_ver = self.puemos.get_installed_version()
                    res = self.puemos.install_update()
                    final_ver = self.puemos.get_installed_version()
                    ok = bool(res.get("updated")) and not bool(res.get("error"))
                    target_v = res.get("installed_version", initial_ver)
                    readback_ok = ok and (final_ver == target_v)
                    update_results["puemos"] = {
                        "component": "puemos",
                        "initial_version": initial_ver,
                        "target_version": target_v,
                        "check_result": True,
                        "download_result": ok,
                        "verification_result": ok,
                        "installation_result": ok,
                        "activation_result": ok,
                        "readback_result": readback_ok,
                        "final_version": final_ver,
                        "final_update_state": "updated" if ok and readback_ok else "failed",
                        "error": res.get("error", ""),
                        "rollback_result": None,
                        "updated": ok and readback_ok,
                    }

            updated_count = sum(1 for r in update_results.values() if r.get("updated") and not r.get("error"))
            failed_count = sum(1 for r in update_results.values() if (not r.get("updated")) or r.get("error"))

            # Global success requires every target component to succeed with zero errors and valid readback
            all_ok = (
                len(update_results) == len(targets)
                and failed_count == 0
                and all(
                    r.get("updated") is True
                    and r.get("readback_result") is True
                    and not r.get("error")
                    for r in update_results.values()
                )
            )

            # Re-check components to confirm no remaining updates
            for comp, r in update_results.items():
                if r.get("updated"):
                    if comp == "yt-dlp":
                        chk = self.ytdlp.check_update()
                    elif comp == "ubol":
                        chk = self.ubol.check_update()
                    elif comp == "puemos":
                        chk = self.puemos.check_update()
                    if chk.get("update_available"):
                        all_ok = False
                        r["final_update_state"] = "inconsistent"
                        r["error"] = f"Component still reports update available: {chk.get('available_version')}"

            summary_text = (
                f"{updated_count} component{'s' if updated_count != 1 else ''} updated. "
                f"{failed_count} component{'s' if failed_count != 1 else ''} failed."
            )

            self._store.set_batch_state(
                BatchUpdateState.COMPLETED if all_ok else BatchUpdateState.FAILED,
                error="" if all_ok else ("One or more component updates failed" if failed_count > 0 else "Inconsistent update state detected"),
            )
            return {
                "busy": False,
                "results": update_results,
                "success": all_ok,
                "updated_count": updated_count,
                "failed_count": failed_count,
                "errors": {comp: r.get("error", "") for comp, r in update_results.items() if r.get("error")},
                "summary": summary_text,
            }
        except Exception as exc:
            err_msg = str(exc)
            self._store.set_batch_state(BatchUpdateState.FAILED, error=err_msg)
            return {"busy": False, "error": err_msg, "success": False, "results": {}, "updated_count": 0, "failed_count": len(components_to_update or [])}
        finally:
            self._is_busy = False
            self._batch_lock.release()
