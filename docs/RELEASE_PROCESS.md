# Release Process

This document outlines the release verification and packaging procedures for VRKA.

---

## Pre-Release Checklist

1. **Code Quality & Syntax**: Verify that all Python files compile cleanly without errors (`python -m compileall -q .`) and all unit tests pass (`python -m unittest discover -s tests -v`).
2. **Branding & Versioning**: Confirm version metadata in `version_info.txt`, `VRKA-4.0.iss`, `pyproject.toml`, and QML files (4.5.0 Build 018).
3. **Security Audit**: Ensure no temporary test profiles, API keys, personal credentials, or local paths are present in source files.
4. **Build Packaging**: Generate standalone binary with PyInstaller and compile Windows installer with Inno Setup.
5. **Checksum & OpenPGP Signature Generation**: Produce cryptographic SHA-256 hashes in `SHA256SUMS.txt` and detached OpenPGP signatures with the authoritative release signing key (`71165A658B3A8612AC2568C6D519380BEBA1B9F7`).

---

## Publishing Releases

- Create a release commit and annotated Git tag (`v4.5.0`).
- Create a GitHub Release with detailed user-facing notes and attached binary packages.
- Verify asset hashes against `SHA256SUMS.txt` and verify detached signatures.
