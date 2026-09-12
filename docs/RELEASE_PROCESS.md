# Release Process

This document outlines the release verification, packaging, and publishing procedures for VRKA.

---

## 1. Pre-Release Verification

1. **Test Suite**: Run the complete test suite:
   ```powershell
   python -m unittest discover -s tests -v
   ```
2. **Bytecode Compilation**: Ensure all source files compile cleanly:
   ```powershell
   python -m compileall -q .
   ```
3. **Version Consistency**: Verify that the version (`4.5.0`) and build (`018`) are synchronized across:
   - `pyproject.toml`
   - `vrka_downloader.py`
   - `vrka_qml/app.py`
   - `version_info.txt`
   - `VRKA-4.0.iss`
   - `CITATION.cff`
4. **Cleanliness**: Ensure no temporary profiles, test logs, credentials, or personal filesystem paths are committed.

---

## 2. Build Packaging

Run the release packaging pipeline:

```powershell
python tools/generate_release_build018.py
```

This generates release artifacts in `releases/VRKA-4.5.0-Build-018/`:
- `VRKA-4.5.0-Build-018-Setup.exe` (Windows installer)
- `VRKA-4.5.0-Build-018-Portable.zip` (Portable directory archive)
- `VRKA-4.5.0-Build-018-Portable.exe` (Single-file executable)
- `VRKA-4.5.0-Build-018-Source.zip` (Source archive)
- `SHA256SUMS.txt` and `SHA256SUMS.txt.asc`
- `RELEASE-MANIFEST.json` and `RELEASE-MANIFEST.json.asc`

---

## 3. Cryptographic Verification

1. **Checksum Verification**: Check SHA-256 hashes against `SHA256SUMS.txt`:
   ```powershell
   Get-FileHash releases\VRKA-4.5.0-Build-018\* -Algorithm SHA256
   ```
2. **Signature Verification**: Verify detached OpenPGP signatures against the authoritative pinned public key:
   - Fingerprint: `71165A658B3A8612AC2568C6D519380BEBA1B9F7`
   - Key ID: `D519380BEBA1B9F7`

---

## 4. Publishing Releases

1. Push release commit and tag to GitHub:
   ```powershell
   git push origin main
   git push origin v4.5.0
   ```
2. Create or update the GitHub Release:
   ```powershell
   gh release create v4.5.0 --title "VRKA 4.5 Build 018" --notes-file releases/RELEASE_NOTES_v4.5.0.md releases/VRKA-4.5.0-Build-018/*
   ```
3. Confirm that GitHub Actions CI matrix builds and security workflows complete successfully.
