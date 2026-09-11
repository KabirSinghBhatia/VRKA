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

- **RFC 7230 Header Validation**: All custom headers are strictly validated against token syntax and checked for CRLF (`\r`, `\n`) or null byte (`\0`) injection.
- **Redacted Logging & Diagnostics**: Sensitive headers (`Authorization`, `Cookie`, `X-Auth-Token`, `Proxy-Authorization`), signed tokens, and browser session data are automatically scrubbed before reaching logs or exported diagnostics.
- **Application & Runtime Updates**: The updater downloads only over TLS/HTTPS with per-hop redirect validation restricted to approved hosts (`github.com`, `githubusercontent.com`). Downloads are verified against SHA-256 manifests. *Note: SHA-256 downloaded alongside mutable release assets provides integrity against transfer corruption and basic tampering; full release authenticity relies on HTTPS transport and the host trust model.*
- **Task-Scoped Subprocesses**: All helper and browser processes are registered with the task context and terminated upon task completion or cancellation.
- **DRM Respect**: VRKA intentionally terminates extraction on DRM-protected media streams.
