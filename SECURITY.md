# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| 4.5.1 (Build 019) | :white_check_mark: |
| < 4.5.1 | :x: |

---

## Reporting a Vulnerability

If you discover a potential vulnerability in VRKA, please report it responsibly through GitHub Private Vulnerability Reporting:

1. Go to the **Security** tab: [Report a vulnerability](https://github.com/MaverickRox/VRKA/security/advisories/new)
2. Provide a clear description, reproduction steps, and any relevant logs with personal data redacted.

Please allow up to 48 hours for initial triage before public disclosure.

---

## Security Architecture

- **Cryptographic Release Verification**:
  - Official release packages and manifests include detached OpenPGP signatures (`.asc`) created with the project's 4096-bit RSA release signing key.
  - Verification checks the pinned public key fingerprint: `71165A658B3A8612AC2568C6D519380BEBA1B9F7` (Key ID: `D519380BEBA1B9F7`).
  - OpenPGP release signing operates independently of Windows Authenticode signing. It provides cryptographic authenticity and integrity verification across all platforms without requiring commercial code-signing certificates.
  - Verification fails closed: packages with missing, invalid, or mismatched signatures are rejected.
- **SHA-256 Package Integrity**:
  - Release archives and update payloads are verified against SHA-256 manifests (`SHA256SUMS.txt`) before extraction or execution.
- **Secure Transport & Redirect Allowlisting**:
  - Updates and runtime downloads use TLS/HTTPS exclusively.
  - Per-hop redirect validation enforces host allowlisting (`github.com`, `api.github.com`, `objects.githubusercontent.com`).
  - Redirect hops are limited to a maximum of 5 to prevent loops and redirect attacks.
- **RFC 7230 HTTP Header Validation**:
  - Custom HTTP headers (Referer, Origin, and user-specified headers) are validated against RFC 7230 token grammar.
  - CRLF (`\r`, `\n`) and null-byte (`\0`) injection attempts are rejected fail-closed to prevent header injection and HTTP response splitting.
- **Sensitive Data Redaction**:
  - Authentication tokens, cookies (`Authorization`, `Cookie`, `X-Auth-Token`), signed query parameters, and local filesystem paths are automatically scrubbed from logs and diagnostic exports.
- **Browser Privacy & Session Clearing**:
  - The WebView2 browser fallback session runs in an isolated profile with uBlock Origin Lite content filtering.
  - Stored session cookies, DOM storage, and network cache can be purged at any time from **Settings** > **Browser Privacy**.
- **Task-Scoped Subprocesses**:
  - Child processes (yt-dlp, FFmpeg, WebView2) are tracked in a process registry and terminated upon task completion, cancellation, or application exit.
- **DRM Non-Circumvention**:
  - VRKA does not circumvent or decrypt DRM-protected streams. If encryption is detected, extraction halts with an explanatory notice.
