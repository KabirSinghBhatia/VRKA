# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| 4.5 (Build 018) | :white_check_mark: |
| < 4.5 | :x: |

---

## Reporting a Vulnerability

We take the security and privacy of VRKA seriously. If you discover a potential vulnerability, please report it responsibly using GitHub Private Vulnerability Reporting:

1. Navigate to the **Security** tab of this repository: [https://github.com/MaverickRox/VRKA/security/advisories/new](https://github.com/MaverickRox/VRKA/security/advisories/new)
2. Click **Report a vulnerability**.
3. Provide a clear explanation of the issue, steps to reproduce, and any relevant logs (with personal data redacted).

Alternatively, you may contact the maintainer at [GitHub Security Advisories](https://github.com/MaverickRox/VRKA/security/advisories/new).

Please allow up to 48 hours for initial triage before public disclosure.

---

## Security Architecture Highlights

- **Cryptographic Release Authenticity**:
  - All official release assets and manifests are accompanied by detached OpenPGP signatures (`.asc`) generated using the project's authoritative 4096-bit RSA release signing key.
  - Verification enforces the pinned trusted key fingerprint: `71165A658B3A8612AC2568C6D519380BEBA1B9F7` (Key ID: `D519380BEBA1B9F7`).
  - Strict fail-closed semantics: releases with missing, invalid, or mismatched signatures are rejected immediately.
- **SHA-256 Integrity Verification**:
  - Every release and update package is validated against authoritative SHA-256 checksum manifests before extraction or execution.
- **HTTPS Transport & Host Allowlisting**:
  - Application and runtime updates use TLS/HTTPS exclusively.
  - Per-hop redirect validation enforces strict host allowlisting (`github.com`, `api.github.com`, `objects.githubusercontent.com`).
  - Redirect hops are hard-bounded (maximum 5 hops) to prevent redirect loops or open-redirect exploits.
- **RFC 7230 HTTP Header Validation**:
  - Custom HTTP headers (Referer, Origin, and user-specified headers) are strictly validated against token grammar.
  - CRLF (`\r`, `\n`) and null-byte (`\0`) injections are rejected fail-closed to prevent HTTP response splitting.
- **Sensitive Data Redaction**:
  - All authentication credentials, cookies, tokens (`Authorization`, `Cookie`, `X-Auth-Token`, `Proxy-Authorization`), signed query parameters, and private file paths are automatically scrubbed from logs and exported diagnostics.
- **Component Update Isolation**:
  - Update mechanisms for core components (yt-dlp engine, uBlock Origin Lite rulesets, Puemos media observer) run in isolated operational states with independent update locks, version tracking, and rollback capabilities.
- **Browser Privacy & Session Purge**:
  - The passive WebView2 browser fallback operates in an isolated environment with uBlock Origin Lite filtering.
  - Complete browser session data (cookies, DOM storage, HTTP cache) can be purged instantly via the "Clear All Session Data" action in Settings.
- **Task-Scoped Subprocesses**:
  - Helper processes, extractors, and browser instances are bound to task execution contexts and terminated cleanly upon task completion, cancellation, or error.
- **DRM Non-Circumvention**:
  - VRKA terminates extraction immediately upon detecting DRM-protected streams.
