#!/usr/bin/env python3
"""Build GNU gettext catalogs for source previews and packaging."""

from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
for source in sorted((root / "locale").glob("*.po")):
    language = source.stem.replace("-", "_")
    target = root / "usr/share/locale" / language / "LC_MESSAGES/comm-release.mo"
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["msgfmt", "--check", str(source), "-o", str(target)], check=True)
