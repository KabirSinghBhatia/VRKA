"""Release authenticity and integrity verification module.

Provides fail-closed OpenPGP signature verification and SHA-256 artifact
integrity checking against pinned official VRKA release signing keys.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import warnings

# OpenPGP verification backend: PGPy (pure Python RFC 4880 with cryptography backend)
try:
    import pgpy
    from pgpy.errors import PGPError
    _HAS_PGPY = True
except ImportError:
    pgpy = None  # type: ignore
    PGPError = Exception  # type: ignore
    _HAS_PGPY = False

# Authoritative Pinned VRKA Release Signing Public Key (4096-bit RSA)
TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT = "71165A658B3A8612AC2568C6D519380BEBA1B9F7"
TRUSTED_VRKA_RELEASE_KEY_ID = "D519380BEBA1B9F7"

TRUSTED_VRKA_RELEASE_KEY_PEM = """-----BEGIN PGP PUBLIC KEY BLOCK-----

xsFNBGqj+8UBEAC6fM4M17yqqJfseQTZh/eoU885L04yVKIPXrZFaJinOr462HsV
Xxavxuxsd7MKshhCjYlHterZyqg7sFj1KxlTsY4csgMkEpc72WS5SbVW6w3xJnvj
V7sS+sOh56vvq2zdzAWVW4EagluY82HT+YtP6+zr2D/1j436IOaB6ba88yOF0c5K
L0/RHuRJTsRjQjCoyq9hIUQAZrllU1TVX4DIbyB4CC3YlvRNDh1ZTof/kOZ1lB3B
0I+E2OV+/tEgYp+iAR8v1KoflsVr6xEtFp2bo5RFiyDXTokPVReqNp/2s5ks0TQC
+7jkTX2enUet86WExGqIkxcV8G7baD62ZgBAWdJd9VoPXQIXpDwrQSK1Elv1+Rn9
tQZyWjxpinJYZ97s8aNtRvUA845ItMoJ5S3sEeRxsiOf7g0kB4fH2+G/xwns2gTg
BeO+oyld2TmP2gBwAx2rnbTPuwQbOsN2UFu2d0KNz7XFgRc3IUS0hLRkOVWhsjRs
m+DdnFvHAO2JpKd24gndDgx6iF5SRtsaE27ZZ70yEIVGui8u91Pl5+5QTN+mdOBE
DnedqGwOfQ7GrjGuVwmYDRKs9cHleR891E+cI5AkpMb6zg8pWt6jSyJPfH8LdnI9
v10i8LszIngDMiif8b5m00T3jpmn68x06aidfZBbhzwIgG6Hi6oZyWEn5wARAQAB
zVZWUktBIE9mZmljaWFsIFJlbGVhc2UgU2lnbmVyIChWUktBIFBlcnNpc3RlbnQg
UmVsZWFzZSBTaWduaW5nIEtleSkgPHNlY3VyaXR5QHZya2Eub3JnPsLBhAQTAQgA
LgUCaqP7xQIbAwILCQMVCAoDFgIAAh4BFiEEcRZaZYs6hhKsJWjG1Rk4C+uhufcA
CgkQ1Rk4C+uhufdc2xAAlX/xkYYx6iPRpGeUs9F5QMyUqk4H6pZwWeVVMd4hkYM3
Icj1xA2I19mOhUF1kSsa+8g6dO/oKLPrxhuLN0avwFytU2XJDvBpNFwCygNPA1eu
UaNoD92E60nMAbPqfuus7C0pLXsbHw2B1KaBp17w73FYBqQujr74X49i/i/q8iaK
7kzzH3Ipdy39bz5U4PJUfvF/v9uA3xcZyXd54ElL0Fw/hUodOj/y0nTC0vmdDKc+
s0MgBdaiFEmHuPL5O+DjbfIq6dQuU1C/Z4PiDBVNbPRSmLStAseUINiy7eN8lhPZ
ciThk+ZC0xjQP9fOHz8+0iNX1RsYGKto/fB+m40ieqY2jtd2tZufmCw4OuL1uJzG
RFji3iUTy4RZKgFpbKiKRUIkmSoIyg3G3WaQ6YeUeNY5h9jvJulwEGvat13kWI+U
rSndRMf/RsU4e29+UHG3xmNwBry6ZcQ/dbFq/HEDTy5ShBLjTqzcCrgZLCgelkdK
XogBDhnLFJ39y6TalRJtSjyTqMoJtMpz0P5zC+pBd8/VftMdbW9RistrErvaL1Kc
kGsQ1KX9XM//M4w+09G6HISjoTm2plI+B8zAAaa0UsCMDT6JT+tyYzX9vp8FI0Uj
M23huvW+WpW/v6hlVz706gD1jKyfYWfQXYsTr091BcahAMlGrHXOHib7efW4dds=
=auTg
-----END PGP PUBLIC KEY BLOCK-----
"""


@dataclass
class SignatureVerificationResult:
    """Outcome of an OpenPGP cryptographic signature verification."""
    is_valid: bool
    key_id: str = ""
    fingerprint: str = ""
    error: str = ""


@dataclass
class ReleaseBundleVerificationResult:
    """Comprehensive release authenticity and artifact integrity verification outcome."""
    authenticated: bool
    integrity_ok: bool
    artifact_filename: str
    expected_sha256: str = ""
    actual_sha256: str = ""
    signer_fingerprint: str = ""
    error: str = ""


def compute_file_sha256(file_path: str | Path) -> str:
    """Compute SHA-256 digest of a local file in 64KB chunks."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    h = hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def parse_sha256sums(manifest_text: str) -> dict[str, str]:
    """Parse standard SHA256SUMS.txt format ('<hash> *<filename>' or '<hash>  <filename>')."""
    mapping: dict[str, str] = {}
    for line in manifest_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+[*]?(.+)$", line)
        if m:
            mapping[m.group(2).strip()] = m.group(1).lower()
    return mapping


def verify_openpgp_signature(
    content: bytes | str,
    signature: bytes | str,
    trusted_pubkey_pem: str = TRUSTED_VRKA_RELEASE_KEY_PEM,
    expected_fingerprint: str = TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
) -> SignatureVerificationResult:
    """Verify an OpenPGP signature against the pinned trusted release key.

    Strict fail-closed security guarantees:
    - Rejects missing, empty, or unparseable signatures.
    - Rejects signatures made by untrusted or mismatched keys.
    - Rejects tampered or modified content.
    - Requires pgpy runtime availability.
    """
    if not _HAS_PGPY:
        return SignatureVerificationResult(
            is_valid=False,
            error="OpenPGP verification engine (pgpy) is not installed in runtime.",
        )

    if not signature:
        return SignatureVerificationResult(is_valid=False, error="Missing OpenPGP signature payload.")

    if not content:
        return SignatureVerificationResult(is_valid=False, error="Missing content to verify.")

    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = bytes(content)

    if isinstance(signature, bytes):
        sig_text = signature.decode("utf-8", errors="replace")
    else:
        sig_text = str(signature)

    try:
        # Load and validate trusted public key
        trusted_key, _ = pgpy.PGPKey.from_blob(trusted_pubkey_pem.strip())
        key_fp = str(trusted_key.fingerprint).upper().replace(" ", "")
        key_id = str(trusted_key.fingerprint.keyid)

        if expected_fingerprint:
            exp_fp = expected_fingerprint.upper().replace(" ", "")
            if key_fp != exp_fp:
                return SignatureVerificationResult(
                    is_valid=False,
                    key_id=key_id,
                    fingerprint=key_fp,
                    error=f"Trusted public key fingerprint mismatch: {key_fp} != {exp_fp}",
                )

        # Parse signature
        sig = pgpy.PGPSignature.from_blob(sig_text.strip())

        # Verify signature against content
        # Filter pgpy warnings regarding self-sig parser limitations
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                verification = trusted_key.verify(content_bytes, sig)
            except Exception as v_exc:
                return SignatureVerificationResult(
                    is_valid=False,
                    key_id=key_id,
                    fingerprint=key_fp,
                    error=f"OpenPGP signature verification rejected: {v_exc}",
                )

        if bool(verification):
            return SignatureVerificationResult(
                is_valid=True,
                key_id=key_id,
                fingerprint=key_fp,
            )
        else:
            return SignatureVerificationResult(
                is_valid=False,
                key_id=key_id,
                fingerprint=key_fp,
                error="OpenPGP cryptographic signature check failed (corrupted or forged payload).",
            )

    except Exception as exc:
        return SignatureVerificationResult(
            is_valid=False,
            error=f"Malformed OpenPGP key or signature: {exc}",
        )


def verify_release_artifact(
    artifact_path: str | Path,
    manifest_content: bytes | str,
    signature_content: bytes | str,
    trusted_pubkey_pem: str = TRUSTED_VRKA_RELEASE_KEY_PEM,
    expected_fingerprint: str = TRUSTED_VRKA_RELEASE_KEY_FINGERPRINT,
) -> ReleaseBundleVerificationResult:
    """Verify both release authenticity (OpenPGP signature) and artifact integrity (SHA-256).

    Ensures that:
    1. The manifest is cryptographically signed by the pinned trusted release key.
    2. The target artifact exists in the signed manifest.
    3. The actual SHA-256 of the artifact exactly matches the signed hash.
    """
    p = Path(artifact_path)
    filename = p.name

    if isinstance(manifest_content, bytes):
        manifest_text = manifest_content.decode("utf-8", errors="replace")
    else:
        manifest_text = str(manifest_content)

    # 1. Verify OpenPGP Signature on Manifest (Authenticity)
    sig_result = verify_openpgp_signature(
        content=manifest_text,
        signature=signature_content,
        trusted_pubkey_pem=trusted_pubkey_pem,
        expected_fingerprint=expected_fingerprint,
    )

    if not sig_result.is_valid:
        return ReleaseBundleVerificationResult(
            authenticated=False,
            integrity_ok=False,
            artifact_filename=filename,
            signer_fingerprint=sig_result.fingerprint,
            error=f"Release authenticity check failed: {sig_result.error}",
        )

    # 2. Parse Manifest Checksums
    checksums: dict[str, str] = {}
    if manifest_text.strip().startswith("{"):
        try:
            m_json = json.loads(manifest_text)
            for art in m_json.get("artifacts", []):
                if isinstance(art, dict) and "filename" in art and "sha256" in art:
                    checksums[art["filename"]] = art["sha256"].lower()
        except Exception as j_exc:
            return ReleaseBundleVerificationResult(
                authenticated=True,
                integrity_ok=False,
                artifact_filename=filename,
                signer_fingerprint=sig_result.fingerprint,
                error=f"Failed to parse signed JSON release manifest: {j_exc}",
            )
    else:
        checksums = parse_sha256sums(manifest_text)

    if filename not in checksums:
        return ReleaseBundleVerificationResult(
            authenticated=True,
            integrity_ok=False,
            artifact_filename=filename,
            signer_fingerprint=sig_result.fingerprint,
            error=f"Artifact '{filename}' is not listed in the signed release manifest.",
        )

    expected_sha256 = checksums[filename]

    # 3. Compute Actual Artifact Digest (Integrity)
    try:
        actual_sha256 = compute_file_sha256(p)
    except Exception as read_exc:
        return ReleaseBundleVerificationResult(
            authenticated=True,
            integrity_ok=False,
            artifact_filename=filename,
            expected_sha256=expected_sha256,
            signer_fingerprint=sig_result.fingerprint,
            error=f"Failed to read artifact file for SHA-256 computation: {read_exc}",
        )

    if actual_sha256 != expected_sha256:
        return ReleaseBundleVerificationResult(
            authenticated=True,
            integrity_ok=False,
            artifact_filename=filename,
            expected_sha256=expected_sha256,
            actual_sha256=actual_sha256,
            signer_fingerprint=sig_result.fingerprint,
            error=f"SHA-256 integrity mismatch: expected {expected_sha256}, got {actual_sha256}",
        )

    # 4. Authenticated & Verified Clean
    return ReleaseBundleVerificationResult(
        authenticated=True,
        integrity_ok=True,
        artifact_filename=filename,
        expected_sha256=expected_sha256,
        actual_sha256=actual_sha256,
        signer_fingerprint=sig_result.fingerprint,
    )
