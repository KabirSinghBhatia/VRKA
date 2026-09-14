"""In-App Application Self-Update System for VRKA 4.5.1 on Windows.

Security & Integrity Architecture:
- Official GitHub Releases API integration (MaverickRox/VRKA)
- 24-hour rate-limiting gate for automatic background checks
- Manual check bypass with immediate feedback
- Strict semantic version comparison (SemanticVersion)
- Downgrade rejection: strictly requires latest > current
- HTTPS-only per-hop redirect validation (max 5 hops, reject HTTP downgrade)
- Approved host allowlisting (GitHub API and release asset CDN domains)
- Distribution-aware Windows asset pattern matching (Setup installer vs Portable)
- SHA-256 manifest verification for transfer integrity
- Authoritative OpenPGP signature verification via pinned release signing keys
- Staged downloading in %LOCALAPPDATA%\\VRKA\\updates\\
- Strict fail-closed error handling and atomic staging
- Concurrency locks preventing duplicate downloads or verification jobs
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time
from typing import Any, Callable
import urllib.parse
import urllib.request
from dataclasses import dataclass

from vrka_core.updater_state import AppUpdateState, UpdateStateStore

# Approved GitHub release hosts for redirect validation
_APPROVED_HOSTS = (
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "raw.githubusercontent.com",
)

# Asset patterns matching official desktop packaging
_SETUP_EXE_PATTERN = re.compile(r"^VRKA-.*(?:setup|installer).*\.exe$", re.IGNORECASE)
_PORTABLE_ZIP_PATTERN = re.compile(r"^VRKA-.*portable.*\.zip$", re.IGNORECASE)
_PORTABLE_EXE_PATTERN = re.compile(r"^VRKA-.*portable.*\.exe$", re.IGNORECASE)

# Global lock preventing concurrent app update operations
_APP_UPDATE_LOCK = threading.Lock()


def is_installer_installation() -> bool:
    """Detect whether current running instance was installed by Inno Setup installer."""
    try:
        exe_path = Path(sys.executable).resolve()
        # 1. Inno Setup leaves unins000.exe in the installation root
        if (exe_path.parent / "unins000.exe").is_file():
            return True
        # 2. Check standard installation directories
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app = os.environ.get("LOCALAPPDATA", "")
        p_str = str(exe_path).lower()
        if (
            p_str.startswith(prog_files.lower())
            or p_str.startswith(prog_files_x86.lower())
            or (local_app and p_str.startswith(os.path.join(local_app, "Programs").lower()))
        ):
            return True
    except Exception:
        pass
    return False


@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: str = ""

    @classmethod
    def parse(cls, ver_str: str) -> SemanticVersion:
        cleaned = re.sub(r"^[vV]", "", ver_str.strip())
        match = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:-(.+))?$", cleaned)
        if not match:
            return cls(0, 0, 0, ver_str)
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3) or 0)
        prerelease = match.group(4) or ""
        return cls(major, minor, patch, prerelease)

    def __lt__(self, other: SemanticVersion) -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return self.prerelease < other.prerelease

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )


@dataclass
class AppUpdateInfo:
    current_version: str
    latest_version: str
    tag_name: str
    release_notes: str
    published_at: str
    asset_name: str
    asset_download_url: str
    sha256_manifest_url: str
    signature_url: str
    is_newer: bool
    distribution_type: str = "installer"


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


def check_for_application_update(
    current_version_str: str = "4.5.1",
    repo_url: str = "https://api.github.com/repos/MaverickRox/VRKA/releases/latest",
    timeout: float = 10.0,
    store: UpdateStateStore | None = None,
) -> AppUpdateInfo | None:
    """Query GitHub Releases API for latest VRKA desktop release."""
    req = urllib.request.Request(
        repo_url,
        headers={
            "User-Agent": f"VRKA/{current_version_str} (Windows x64)",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    opener = urllib.request.build_opener(SafeRedirectHandler())
    with opener.open(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    tag_name = str(data.get("tag_name") or "")
    release_version = tag_name.lstrip("vV")
    body = str(data.get("body") or "")
    published_at = str(data.get("published_at") or "")

    current_semver = SemanticVersion.parse(current_version_str)
    latest_semver = SemanticVersion.parse(release_version)
    # Reject downgrades strictly: is_newer only if latest > current
    is_newer = current_semver < latest_semver

    assets = data.get("assets", [])
    asset_name = ""
    asset_url = ""
    sha256_url = ""
    sig_url = ""

    # Check distribution type
    is_installed = is_installer_installation()
    dist_type = "installer" if is_installed else "portable"

    # Match manifest and signature files
    for a in assets:
        name = str(a.get("name") or "")
        durl = str(a.get("browser_download_url") or "")
        if name.endswith(".asc") and ("sha256" in name.lower() or "manifest" in name.lower()):
            sig_url = durl
        elif "sha256" in name.lower() or name.lower() == "sha256sums.txt":
            sha256_url = durl

    # Select appropriate binary distribution asset
    if is_installed:
        # Prefer Setup.exe for installer installation
        for a in assets:
            name = str(a.get("name") or "")
            durl = str(a.get("browser_download_url") or "")
            if _SETUP_EXE_PATTERN.match(name):
                asset_name = name
                asset_url = durl
                break
    else:
        # Prefer Portable.zip or Portable.exe for portable installation
        for a in assets:
            name = str(a.get("name") or "")
            durl = str(a.get("browser_download_url") or "")
            if _PORTABLE_ZIP_PATTERN.match(name):
                asset_name = name
                asset_url = durl
                break
        if not asset_url:
            for a in assets:
                name = str(a.get("name") or "")
                durl = str(a.get("browser_download_url") or "")
                if _PORTABLE_EXE_PATTERN.match(name):
                    asset_name = name
                    asset_url = durl
                    break

    # Fallback to Setup.exe if portable was not found
    if not asset_url:
        for a in assets:
            name = str(a.get("name") or "")
            durl = str(a.get("browser_download_url") or "")
            if _SETUP_EXE_PATTERN.match(name):
                asset_name = name
                asset_url = durl
                break

    info = AppUpdateInfo(
        current_version=current_version_str,
        latest_version=release_version,
        tag_name=tag_name,
        release_notes=body,
        published_at=published_at,
        asset_name=asset_name,
        asset_download_url=asset_url,
        sha256_manifest_url=sha256_url,
        signature_url=sig_url,
        is_newer=is_newer,
        distribution_type=dist_type,
    )

    if store:
        store.set_app_state(
            AppUpdateState.AVAILABLE if is_newer else AppUpdateState.IDLE,
            current_version=current_version_str,
            available_version=release_version,
            asset_name=asset_name,
            last_check=round(time.time(), 2),
            error="",
        )

    return info


def download_and_verify_update(
    update_info: AppUpdateInfo,
    staging_dir: Path | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
    require_signature: bool = True,
    store: UpdateStateStore | None = None,
) -> Path:
    """Download, verify SHA-256 integrity, and authenticate OpenPGP release signature.

    Security & Authenticity Model:
    1. Rejects duplicate concurrent update operations with thread lock.
    2. Downloads to .downloading staging file.
    3. SHA-256 establishes artifact integrity against transfer corruption.
    4. OpenPGP signature verification establishes release authenticity against pinned key.
    5. Fails closed: corrupt or unverified downloads are deleted immediately.
    """
    from vrka_core.release_verifier import verify_release_artifact

    if not _APP_UPDATE_LOCK.acquire(blocking=False):
        raise RuntimeError("Another application update download is already in progress.")

    if not update_info.asset_download_url:
        _APP_UPDATE_LOCK.release()
        raise ValueError("No valid release installer asset found in update metadata")

    if staging_dir is None:
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        staging_dir = local_app_data / "VRKA" / "updates"

    staging_dir.mkdir(parents=True, exist_ok=True)
    target_file = staging_dir / update_info.asset_name
    temp_file = staging_dir / f"{update_info.asset_name}.downloading"

    if store:
        store.set_app_state(AppUpdateState.DOWNLOADING)

    opener = urllib.request.build_opener(SafeRedirectHandler())

    try:
        # 1. Fetch SHA256 manifest and OpenPGP signature
        manifest_text = ""
        signature_text = ""
        if update_info.sha256_manifest_url:
            try:
                req = urllib.request.Request(
                    update_info.sha256_manifest_url,
                    headers={"User-Agent": "VRKA-Updater"},
                )
                with opener.open(req, timeout=15.0) as resp:
                    manifest_text = resp.read().decode("utf-8", errors="replace")
            except Exception as m_exc:
                if require_signature:
                    raise ValueError(f"Failed to fetch release manifest: {m_exc}") from m_exc

        if update_info.signature_url:
            try:
                req = urllib.request.Request(
                    update_info.signature_url,
                    headers={"User-Agent": "VRKA-Updater"},
                )
                with opener.open(req, timeout=15.0) as resp:
                    signature_text = resp.read().decode("utf-8", errors="replace")
            except Exception as s_exc:
                if require_signature:
                    raise ValueError(f"Failed to fetch OpenPGP signature: {s_exc}") from s_exc

        if require_signature and (not manifest_text or not signature_text):
            raise ValueError("Authenticated release verification failed: missing signed manifest or OpenPGP signature.")

        # 2. Stream binary asset
        if temp_file.exists():
            temp_file.unlink()

        req = urllib.request.Request(
            update_info.asset_download_url,
            headers={"User-Agent": "VRKA-Updater"},
        )
        with opener.open(req, timeout=30.0) as resp, open(temp_file, "wb") as out:
            total_size = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            chunk_size = 64 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total_size > 0:
                    progress_cb(downloaded, total_size)

        if store:
            store.set_app_state(AppUpdateState.VERIFYING)

        # 3. Authenticate & Verify Integrity
        if manifest_text and signature_text:
            ver_res = verify_release_artifact(
                artifact_path=temp_file,
                manifest_content=manifest_text,
                signature_content=signature_text,
            )
            if not ver_res.authenticated or not ver_res.integrity_ok:
                if temp_file.exists():
                    temp_file.unlink()
                raise ValueError(f"Authenticated release verification rejected: {ver_res.error}")

        # 4. Atomic move to final target
        if target_file.exists():
            target_file.unlink()
        shutil.move(temp_file, target_file)

        if store:
            store.set_app_state(AppUpdateState.READY_TO_INSTALL, asset_name=target_file.name)

        return target_file
    except Exception as exc:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        if store:
            store.set_app_state(AppUpdateState.FAILED, error=str(exc))
        raise
    finally:
        _APP_UPDATE_LOCK.release()
