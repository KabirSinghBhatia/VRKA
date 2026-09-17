# Third-Party License Texts & SPDX Specifications

This directory stores canonical SPDX license templates in accordance with the [REUSE Specification](https://reuse.software/) and a machine-readable dependency inventory for all components distributed with VRKA releases.

- **Authoritative Catalog**: Refer to [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) in the project root for the consolidated human-readable inventory of components, copyright notices, and upstream links.
- **Machine-Readable Manifest**: See `manifest.json` in this directory for structured component names, versions, authors, and license classifications.
- **External Media Tools**: In accordance with [docs/FFMPEG_COMPLIANCE.md](../docs/FFMPEG_COMPLIANCE.md), FFmpeg and FFprobe binaries are strictly **unbundled** from VRKA application releases and managed in user space at runtime.
- **Automated Management**: This directory and `THIRD_PARTY_NOTICES.md` are automatically maintained by:
  ```bash
  .venv/bin/python tools/collect_licenses.py --dump-licenses --update-notices
  ```
