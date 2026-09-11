"""HTTP header validation and multi-tier secret redaction for VRKA 4.5.

Conforms to RFC 7230 token specifications and protects against CRLF
injection, unauthorized header formatting, and credential leakage in logs.
"""

from __future__ import annotations

import re
from typing import Any

# RFC 7230 Section 3.2.6 token specification (strict \A and \Z to prevent newline match)
_TOKEN_RE = re.compile(r"\A[a-zA-Z0-9!#$%&'*+\-.^_`|~]+\Z")

# Sensitive header patterns for redaction
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(auth|token|secret|password|cookie|credential|key|proxy-auth|signature)"
)

# Secret parameter patterns in URLs or diagnostic strings (token=..., key=..., etc.)
_SECRET_PARAM_RE = re.compile(
    r"(?i)(?:([?&]|\b)(?:token|sig|signature|key|auth|session|credential|secret|password)=)[^&\s\r\n]+"
)


def validate_header_name(name: str) -> bool:
    """Validate header name against RFC 7230 token rules without pre-stripping."""
    if not isinstance(name, str):
        return False
    if not name or len(name) > 256:
        return False
    if any(ch in name for ch in ("\r", "\n", "\0", " ", "\t")):
        return False
    return bool(_TOKEN_RE.match(name))


def validate_header_value(value: str) -> bool:
    """Validate header value and strictly reject CRLF or null-byte injection."""
    if not isinstance(value, str):
        return False
    # Reject CRLF injection, line feeds, and null bytes
    if any(ch in value for ch in ("\r", "\n", "\0")):
        return False
    # Check for non-printable control characters (except tab)
    for ch in value:
        code = ord(ch)
        if code < 32 and code != 9:
            return False
    return len(value) <= 8192


def parse_custom_headers(raw: str | dict[str, str] | list[str] | Any) -> tuple[dict[str, str], list[str]]:
    """Parse and validate custom headers into a normalized dict.

    Returns:
        (headers_dict, errors_list)
    """
    headers: dict[str, str] = {}
    errors: list[str] = []

    if not raw:
        return headers, errors

    if isinstance(raw, dict):
        for k, v in raw.items():
            k_str = str(k)
            v_str = str(v)
            if not validate_header_name(k_str):
                errors.append(f"Invalid header name: '{k_str}' (RFC 7230 violation)")
                continue
            if not validate_header_value(v_str):
                errors.append(f"Invalid header value for '{k_str}' (CRLF or control character detected)")
                continue
            headers[k_str] = v_str.strip()
        return headers, errors

    lines: list[str] = []
    if isinstance(raw, str):
        lines = [line for line in raw.splitlines() if line.strip()]
    elif isinstance(raw, (list, tuple)):
        lines = [str(item) for item in raw if str(item).strip()]

    for line in lines:
        if ":" not in line:
            errors.append(f"Malformed header line (missing ':' delimiter): '{line[:40]}'")
            continue
        key, _, val = line.partition(":")
        k_str = key.strip()
        v_str = val.strip()

        if not validate_header_name(k_str):
            errors.append(f"Invalid header name: '{k_str}' (must be valid RFC 7230 token)")
            continue
        if not validate_header_value(v_str):
            errors.append(f"Invalid header value for '{k_str}' (CRLF or invalid characters rejected)")
            continue
        headers[k_str] = v_str

    return headers, errors


def redact_sensitive_headers(headers: dict[str, str] | list[str] | str) -> dict[str, str] | list[str] | str:
    """Redact sensitive authorization, cookies, and tokens from headers."""
    if isinstance(headers, dict):
        redacted: dict[str, str] = {}
        for k, v in headers.items():
            if _SENSITIVE_KEY_RE.search(k):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = v
        return redacted

    if isinstance(headers, list):
        redacted_list: list[str] = []
        for item in headers:
            if ":" in item:
                k, _, _ = item.partition(":")
                if _SENSITIVE_KEY_RE.search(k.strip()):
                    redacted_list.append(f"{k.strip()}: [REDACTED]")
                    continue
            redacted_list.append(item)
        return redacted_list

    if isinstance(headers, str):
        lines = headers.splitlines()
        redacted_lines: list[str] = []
        for line in lines:
            if ":" in line:
                k, _, _ = line.partition(":")
                if _SENSITIVE_KEY_RE.search(k.strip()):
                    redacted_lines.append(f"{k.strip()}: [REDACTED]")
                    continue
            redacted_lines.append(line)
        return "\n".join(redacted_lines)

    return headers


def redact_secrets_from_text(text: str) -> str:
    """Universal text scrubber removing embedded tokens, auth headers, and secrets."""
    if not isinstance(text, str) or not text:
        return ""
    # Redact query parameters or key=value secrets
    sanitized = re.sub(
        r"(?i)(\b(?:token|sig|signature|key|auth|session|credential|secret|password)=)[^&\s\r\n]+",
        r"\1[REDACTED]",
        text,
    )
    # Redact URL query parameters like ?token=... or &sig=...
    sanitized = re.sub(
        r"([?&](?:token|sig|signature|key|auth|session|credential|secret|password)=)[^&\s\r\n]+",
        r"\1[REDACTED]",
        sanitized,
    )
    # Redact standard auth/cookie headers
    sanitized = re.sub(
        r"(?i)(Authorization:\s*(?:Bearer|Basic)?\s*)[^\r\n]+",
        r"\1[REDACTED]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?i)(Cookie:\s*)[^\r\n]+",
        r"\1[REDACTED]",
        sanitized,
    )
    return sanitized
