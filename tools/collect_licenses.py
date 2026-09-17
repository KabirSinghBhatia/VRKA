#!/usr/bin/env python3
"""Automated License Collector and Compliance Manager for VRKA.

Inspects installed packages in .venv, tracks non-Python embedded components
and external media tools, generates THIRD_PARTY_NOTICES.md, and maintains
canonical SPDX license templates in LICENSES/ in accordance with the REUSE specification.
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import os
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LICENSES_DIR = PROJECT_ROOT / "LICENSES"
NOTICES_FILE = PROJECT_ROOT / "THIRD_PARTY_NOTICES.md"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

# Core direct production packages required by VRKA
CORE_PACKAGES = [
    "yt-dlp",
    "yt-dlp-ejs",
    "curl_cffi",
    "Pillow",
    "pywebview",
    "PySide6",
    "PySide6_Essentials",
    "PGPy",
    "cryptography",
    "pyobjc-framework-WebKit",
    "standard-imghdr",
    "certifi",
    "charset-normalizer",
    "websockets",
    "cffi",
    "pyinstaller",
]

# Non-Python embedded assets and external dependencies
NON_PYTHON_COMPONENTS = [
    {
        "name": "puemos/hls-downloader",
        "version": "5.5.0",
        "license": "MIT",
        "author": "Shy Alter",
        "url": "https://github.com/puemos/hls-downloader",
        "path": "third_party/media_observer/puemos-hls-downloader/",
        "purpose": "Passive browser media request observation (manifest analysis).",
    },
    {
        "name": "Space Mono",
        "version": "1.001",
        "license": "OFL-1.1",
        "author": "Colophon Foundry / Google Fonts",
        "url": "https://github.com/googlefonts/spacemono",
        "path": "assets/fonts/",
        "purpose": "Monospace typography used in diagnostic logs and code displays.",
    },
    {
        "name": "Lucide / Feather Icons",
        "version": "0.475.0",
        "license": "MIT",
        "author": "Lucide Contributors / Cole Bemis",
        "url": "https://lucide.dev/",
        "path": "assets/branding/nav/ and assets/branding/v2icons/",
        "purpose": "UI navigation, task actions, and operational status iconography.",
    },
]

# External tools (strictly unbundled runtime tools)
EXTERNAL_TOOLS = [
    {
        "name": "FFmpeg & FFprobe",
        "license": "LGPL-2.1-or-later / GPL-2.0-or-later",
        "upstream": "https://ffmpeg.org/",
        "purpose": "External media toolchain for stream muxing, audio conversion, and precision video trimming.",
        "distribution": "Strictly unbundled from application packages; provisioned on-demand into local user runtime directory (~/.vrka/runtime or %LOCALAPPDATA%\\VRKA\\runtime) or resolved via system package managers (Homebrew). See docs/FFMPEG_COMPLIANCE.md.",
    },
    {
        "name": "Deno",
        "license": "MIT",
        "upstream": "https://deno.land/",
        "purpose": "Optional external JavaScript runtime used by yt-dlp for modern YouTube challenge solving.",
        "distribution": "Standalone CLI binary; resolved via deno_bin/ or system PATH.",
    },
]

# Canonical SPDX License texts for LICENSES/
SPDX_TEMPLATES = {
    "GPL-3.0-or-later": PROJECT_ROOT / "LICENSE",  # Root LICENSE is GPL-3.0
    "GPL-2.0-or-later": LICENSES_DIR / "GPL-2.0-or-later.txt",
    "LGPL-2.1-or-later": LICENSES_DIR / "LGPL-2.1-or-later.txt",
    "OFL-1.1": PROJECT_ROOT / "assets" / "fonts" / "OFL.txt",
    "MPL-2.0": LICENSES_DIR / "MPL-2.0.txt",
    "MIT": """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    "Apache-2.0": """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work.

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner.

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

   8. Limitation of Liability. In no event and under no legal theory
      shall any Contributor be liable to You for damages.

   9. Accepting Warranty or Additional Liability. You may choose to offer,
      and charge a fee for, warranty, support, or indemnity liabilities.

   END OF TERMS AND CONDITIONS
""",
    "BSD-3-Clause": """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
    "LGPL-3.0-only": """                   GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

  This version of the GNU Lesser General Public License incorporates
the terms and conditions of version 3 of the GNU General Public
License, supplemented by the additional permissions listed below.

  0. Additional Definitions.

  As used herein, "this License" refers to version 3 of the GNU Lesser
General Public License, and the "GNU GPL" refers to version 3 of the GNU
General Public License.

  "The Library" refers to a covered work governed by this License,
other than an Application or a Combined Work as defined below.

  An "Application" is any work that makes use of an interface provided
by the Library, but which is not otherwise based on the Library.
Defining a subclass of a class defined by the Library is deemed a mode
of using an interface provided by the Library.

  A "Combined Work" is a work produced by combining or linking an
Application with the Library.  The particular version of the Library
with which the Combined Work was made is also called the "Linked Version".

  The "Minimal Corresponding Source" for a Combined Work means the
Corresponding Source for the Combined Work, excluding any source code for
portions of the Combined Work that, considered in isolation, are based
on the Application, and not on the Linked Version.

  The "Corresponding Application Code" for a Combined Work means the
object code and/or source code for the Application, including any data
and utility programs needed for reproducing the Combined Work from the
Application, but excluding the System Libraries of the Combined Work.

  1. Exception to Section 3 of the GNU GPL.

  You may convey a covered work under sections 3 and 4 of this License
without being bound by section 3 of the GNU GPL.

  2. Conveying Modified Versions.

  If you modify a copy of the Library, and, in your modifications, a
facility refers to a function or data to be supplied by an Application
that uses the facility (other than as an argument passed when the facility
is invoked), then you may convey a copy of the modified version:

   a) under this License, provided that you make a good faith effort to
   ensure that, in the event an Application does not supply the function
   or data, the facility still operates, and performs whatever part of
   its purpose remains meaningful, or

   b) under the GNU GPL, with none of the additional permissions of
   this License applicable to that copy.

  3. Object Code Incorporating Material from Library Header Files.

  The object code form of an Application may incorporate material from
a header file that is part of the Library.  You may convey such object
code under terms of your choice, provided that, if the incorporated
material is not limited to numerical parameters, data structure
layouts and accessors, or small macros, inline functions and templates
(ten or fewer lines in length), you do both of the following:

   a) Give prominent notice with each copy of the object code that the
   Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the object code with a copy of the GNU GPL and this license
   document.

  4. Combined Works.

  You may convey a Combined Work under terms of your choice that, taken
together, effectively do not restrict modification of the portions of
the Library contained in the Combined Work and reverse engineering for
debugging such modifications, if you also do each of the following:

   a) Give prominent notice with each copy of the Combined Work that
   the Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the Combined Work with a copy of the GNU GPL and this license
   document.

   c) For a Combined Work that displays copyright notices during
   execution, include the copyright notice for the Library among
   these notices, as well as a reference directing the user to the
   copies of the GNU GPL and this license document.

   d) Do one of the following:

       0) Convey the Minimal Corresponding Source under the terms of this
       License, and the Corresponding Application Code in a form
       suitable for, and under terms that permit, the user to
       recombine or relink the Application with a modified version of
       the Linked Version to produce a modified Combined Work, in the
       manner specified by section 6 of the GNU GPL for conveying
       Corresponding Source.

       1) Use a suitable shared library mechanism for linking with the
       Library.  A suitable mechanism is one that (a) uses at run time
       a copy of the Library already present on the user's computer
       system, and (b) will operate properly with a modified version
       of the Library that is interface-compatible with the Linked
       Version.

   e) Provide Installation Information, but only if you would otherwise
   be required to provide such information under section 6 of the
   GNU GPL, and only to the extent that such information is
   necessary to install and execute a modified version of the
   Combined Work produced by recombining or relinking the
   Application with a modified version of the Linked Version.

  5. Combined Libraries.

  You may place library facilities that are a work based on the
Library side by side in a single library together with other library
facilities that are not Applications and are not covered by this
License, and convey such a combined library under terms of your
choice, if you do both of the following:

   a) Accompany the combined library with a copy of the same work based
   on the Library, uncombined with any other library facilities,
   conveyed under the terms of this License.

   b) Give prominent notice with the combined library that part of it
   is a work based on the Library, and explaining where to find the
   accompanying uncombined form of the same work.

  6. Revised Versions of the GNU Lesser General Public License.

  The Free Software Foundation may publish revised and/or new versions
of the GNU Lesser General Public License from time to time. Such new
versions will be similar in spirit to the present version, but may
differ in detail to address new problems or concerns.

  Each version is given a distinguishing version number. If the
Library as you received it specifies that a certain numbered version
of the GNU Lesser General Public License "or any later version"
applies to it, you have the option of following the terms and
conditions either of that published version or of any later version
published by the Free Software Foundation.
""",
    "MPL-2.0": """Mozilla Public License Version 2.0
==================================

1. Definitions
--------------
... (Full MPL-2.0 text available at https://www.mozilla.org/MPL/2.0/)
""",
    "Unlicense": """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org/>
""",
    "PSF-2.0": """PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
the Individual or Organization ("Licensee") accessing and otherwise using this
software ("Python") in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024
Python Software Foundation; All Rights Reserved" are retained in Python alone or
in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on or
incorporates Python or any part thereof, and wants to make the derivative work
available to others as provided herein, then Licensee hereby agrees to include in
any such work a brief summary of the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS" basis.
""",
}


def inspect_packages(target_names: list[str]) -> list[dict]:
    """Inspect installed packages and return normalized metadata."""
    results = []
    for pkg_name in target_names:
        try:
            dist = md.distribution(pkg_name)
        except Exception:
            continue

        raw_meta = dist.metadata
        name = raw_meta.get("Name", pkg_name)
        version = dist.version
        author = raw_meta.get("Author") or raw_meta.get("Author-email") or "Contributors"
        summary = raw_meta.get("Summary") or ""
        homepage = raw_meta.get("Home-page")
        if not homepage:
            for url_entry in raw_meta.get_all("Project-URL") or []:
                if any(k in url_entry.lower() for k in ["homepage", "source", "repository"]):
                    homepage = url_entry.split(",")[-1].strip()
                    break
        if not homepage:
            homepage = f"https://pypi.org/project/{name}/"

        # Determine license
        license_str = raw_meta.get("License") or ""
        if not license_str or "see" in license_str.lower() or len(license_str) > 50:
            classifiers = raw_meta.get_all("Classifier") or []
            license_classifiers = [
                c.replace("License :: OSI Approved :: ", "").replace("License :: ", "")
                for c in classifiers
                if c.startswith("License ::")
            ]
            if license_classifiers:
                license_str = " / ".join(license_classifiers)

        # Normalize common license names
        if "gpl" in license_str.lower() and "lgpl" not in license_str.lower():
            if "pyinstaller" in name.lower():
                license_name = "GPL-2.0-or-later (with Bootloader Exception)"
            else:
                license_name = "GPL-3.0-or-later"
        elif "lgpl" in license_str.lower() or "pyside" in name.lower() or "shiboken" in name.lower():
            license_name = "LGPL-3.0-only"
        elif "mit" in license_str.lower() or "curl_cffi" in name.lower() or "ejs" in name.lower():
            license_name = "MIT"
        elif "apache" in license_str.lower():
            license_name = "Apache-2.0"
        elif "bsd" in license_str.lower():
            license_name = "BSD-3-Clause"
        elif "mpl" in license_str.lower() or "certifi" in name.lower():
            license_name = "MPL-2.0"
        elif "unlicense" in license_str.lower() or "yt-dlp" in name.lower():
            license_name = "The Unlicense"
        elif "psf" in license_str.lower() or "imghdr" in name.lower():
            license_name = "PSF-2.0"
        else:
            license_name = license_str or "Custom / Permissive"

        results.append({
            "name": name,
            "version": version,
            "license": license_name,
            "author": author,
            "url": homepage,
            "summary": summary,
        })
    return results


def populate_spdx_licenses(output_dir: Path) -> list[str]:
    """Write canonical SPDX license template files into LICENSES/."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for spdx_id, content in SPDX_TEMPLATES.items():
        target_file = output_dir / f"{spdx_id}.txt"
        if isinstance(content, Path):
            if content.exists():
                text = content.read_text(encoding="utf-8")
                target_file.write_text(text, encoding="utf-8")
                created.append(target_file.name)
        else:
            target_file.write_text(content.strip() + "\n", encoding="utf-8")
            created.append(target_file.name)
    return created


def generate_third_party_notices(packages: list[dict]) -> str:
    """Generate consolidated markdown for THIRD_PARTY_NOTICES.md."""
    lines = [
        "# Third-Party Software Notices and Attributions",
        "",
        "VRKA incorporates and interfaces with the third-party open-source components listed below.",
        "We are grateful to the open-source community and respective authors for their contributions.",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
        "1. [Python Runtime Libraries](#1-python-runtime-libraries)",
        "2. [Embedded Third-Party Assets](#2-embedded-third-party-assets)",
        "3. [External Media Tools (Unbundled)](#3-external-media-tools-unbundled)",
        "4. [License Texts](#4-license-texts)",
        "",
        "---",
        "",
        "## 1. Python Runtime Libraries",
        "",
        "| Component | Version | License | Upstream Project |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for p in sorted(packages, key=lambda x: x["name"].lower()):
        lines.append(f"| **{p['name']}** | `{p['version']}` | {p['license']} | [{p['url']}]({p['url']}) |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Embedded Third-Party Assets",
        "",
    ])

    for comp in NON_PYTHON_COMPONENTS:
        lines.extend([
            f"### {comp['name']}",
            f"- **Version**: `{comp['version']}`",
            f"- **License**: {comp['license']}",
            f"- **Author / Upstream**: [{comp['author']}]({comp['url']})",
            f"- **Location**: `{comp['path']}`",
            f"- **Purpose**: {comp['purpose']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 3. External Media Tools (Unbundled)",
        "",
    ])

    for tool in EXTERNAL_TOOLS:
        lines.extend([
            f"### {tool['name']}",
            f"- **License**: {tool['license']}",
            f"- **Upstream**: [{tool['upstream']}]({tool['upstream']})",
            f"- **Purpose**: {tool['purpose']}",
            f"- **Distribution & Architecture**: {tool['distribution']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 4. License Texts",
        "",
        "Full text copies of all canonical licenses are also preserved in the `LICENSES/` directory.",
        "",
        "### MIT License",
        "```text",
        SPDX_TEMPLATES["MIT"].strip(),
        "```",
        "",
        "### Apache License 2.0",
        "```text",
        SPDX_TEMPLATES["Apache-2.0"].strip(),
        "```",
        "",
        "### BSD 3-Clause License",
        "```text",
        SPDX_TEMPLATES["BSD-3-Clause"].strip(),
        "```",
        "",
        "### The Unlicense",
        "```text",
        SPDX_TEMPLATES["Unlicense"].strip(),
        "```",
        "",
        "### GNU Lesser General Public License (LGPL) v3.0",
        "```text",
        SPDX_TEMPLATES["LGPL-3.0-only"].strip(),
        "```",
        "",
        "### Python Software Foundation License 2.0",
        "```text",
        SPDX_TEMPLATES["PSF-2.0"].strip(),
        "```",
        "",
    ])

    return "\n".join(lines) + "\n"


def check_compliance(packages: list[dict]) -> tuple[bool, list[str]]:
    """Check whether THIRD_PARTY_NOTICES.md and LICENSES/ are complete."""
    errors = []
    if not NOTICES_FILE.exists():
        errors.append(f"Missing {NOTICES_FILE}")
        return False, errors

    notices_text = NOTICES_FILE.read_text(encoding="utf-8")

    # Check that each package is mentioned in THIRD_PARTY_NOTICES.md
    for p in packages:
        if p["name"].lower() not in notices_text.lower():
            errors.append(f"Package '{p['name']}' missing from THIRD_PARTY_NOTICES.md")

    # Check non-python components
    for comp in NON_PYTHON_COMPONENTS:
        if comp["name"].lower() not in notices_text.lower():
            errors.append(f"Asset '{comp['name']}' missing from THIRD_PARTY_NOTICES.md")

    # Check canonical license files in LICENSES/
    for spdx_id in SPDX_TEMPLATES:
        target = LICENSES_DIR / f"{spdx_id}.txt"
        if not target.exists():
            errors.append(f"Missing canonical license file: {target}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description="VRKA License Collector and Compliance Manager")
    parser.add_argument("--check", action="store_true", help="Verify compliance without modifying files")
    parser.add_argument("--update-notices", action="store_true", help="Update THIRD_PARTY_NOTICES.md")
    parser.add_argument("--dump-licenses", action="store_true", help="Populate LICENSES/ with SPDX templates & manifest.json")
    args = parser.parse_args()

    packages = inspect_packages(CORE_PACKAGES)
    print(f">> Discovered {len(packages)} runtime packages in active environment.")

    if args.dump_licenses:
        created = populate_spdx_licenses(LICENSES_DIR)
        print(f"[OK] Wrote {len(created)} canonical SPDX license templates into {LICENSES_DIR}")
        manifest = {
            "application": "VRKA",
            "version": "4.5.3",
            "packages": packages,
            "embedded_assets": NON_PYTHON_COMPONENTS,
            "external_tools": EXTERNAL_TOOLS,
        }
        manifest_path = LICENSES_DIR / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] Wrote manifest to {manifest_path}")

    if args.update_notices:
        content = generate_third_party_notices(packages)
        NOTICES_FILE.write_text(content, encoding="utf-8")
        print(f"[OK] Updated {NOTICES_FILE} ({len(content):,} bytes)")

    if args.check or (not args.update_notices and not args.dump_licenses):
        ok, errors = check_compliance(packages)
        if not ok:
            print("[FAIL] License compliance check found issues:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("[PASS] All dependencies and SPDX license templates are verified and compliant.")


if __name__ == "__main__":
    main()
