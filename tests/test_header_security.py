"""Unit tests for HTTP header validation, injection rejection, and secret redaction."""

import unittest
from vrka_core.header_security import (
    parse_custom_headers,
    redact_secrets_from_text,
    redact_sensitive_headers,
    validate_header_name,
    validate_header_value,
)


class HeaderSecurityTests(unittest.TestCase):
    def test_valid_header_names(self):
        valid = ["User-Agent", "Accept", "X-Custom-Header_1", "Content-Type", "Referer", "Origin"]
        for name in valid:
            self.assertTrue(validate_header_name(name), f"Expected valid header name: {name}")

    def test_invalid_header_names_rejected(self):
        invalid = [
            "",
            "Header Name",  # Space
            "Header:Value",  # Colon
            "Header\r\n",  # CRLF
            "Header\n",  # Newline
            "Header\0",  # Null byte
            "Header@Value",  # @ is not a tchar in RFC 7230
            "Header[Value]",  # Bracket
        ]
        for name in invalid:
            self.assertFalse(validate_header_name(name), f"Expected invalid header name rejected: {name}")

    def test_crlf_injection_in_value_rejected(self):
        malicious = [
            "value\r\nInjected-Header: evil",
            "value\nInjected-Header: evil",
            "value\rInjected-Header: evil",
            "value\0with_null",
            "value\x01with_control",
        ]
        for val in malicious:
            self.assertFalse(validate_header_value(val), f"Expected CRLF injection rejected: {val}")

    def test_parse_custom_headers_multiline(self):
        raw = "Referer: https://example.com/stream\r\nOrigin: https://example.com\r\nX-Auth-Token: secret_12345"
        headers, errors = parse_custom_headers(raw)
        self.assertEqual(len(errors), 0)
        self.assertEqual(headers.get("Referer"), "https://example.com/stream")
        self.assertEqual(headers.get("Origin"), "https://example.com")
        self.assertEqual(headers.get("X-Auth-Token"), "secret_12345")

    def test_parse_custom_headers_catches_errors(self):
        raw = "Invalid Header Space: val\r\nValid: good\r\nBadValue: evil\r\ninjection"
        headers, errors = parse_custom_headers(raw)
        self.assertEqual(headers.get("Valid"), "good")
        self.assertEqual(len(errors), 2)

    def test_redact_sensitive_headers_dict(self):
        headers = {
            "Authorization": "Bearer secret_jwt_token",
            "Cookie": "session=abcd1234efgh",
            "Proxy-Authorization": "Basic dXNlcjpwYXNz",
            "X-Api-Key": "super_secret_key",
            "User-Agent": "VRKA/4.5",
            "Referer": "https://example.com",
        }
        redacted = redact_sensitive_headers(headers)
        self.assertEqual(redacted["Authorization"], "[REDACTED]")
        self.assertEqual(redacted["Cookie"], "[REDACTED]")
        self.assertEqual(redacted["Proxy-Authorization"], "[REDACTED]")
        self.assertEqual(redacted["X-Api-Key"], "[REDACTED]")
        self.assertEqual(redacted["User-Agent"], "VRKA/4.5")
        self.assertEqual(redacted["Referer"], "https://example.com")

    def test_redact_secrets_from_text(self):
        log_sample = (
            "Requesting https://media.cdn.com/stream.m3u8?token=SECRET_123&other=val\n"
            "Authorization: Bearer SECRET_TOKEN_XYZ\n"
            "Cookie: sessionid=SESS_999\n"
            "Stream download started."
        )
        scrubbed = redact_secrets_from_text(log_sample)
        self.assertNotIn("SECRET_123", scrubbed)
        self.assertNotIn("SECRET_TOKEN_XYZ", scrubbed)
        self.assertNotIn("SESS_999", scrubbed)
        self.assertIn("[REDACTED]", scrubbed)


if __name__ == "__main__":
    unittest.main()
