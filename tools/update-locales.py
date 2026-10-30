#!/usr/bin/env python3
"""Extract translatable source strings and merge all existing catalogs."""

import argparse
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--pot-only", action="store_true")
args = parser.parse_args()
version = re.search(r'^VERSION = "([^"]+)"',
                    (root / "usr/share/comm-release/main.py").read_text(), re.MULTILINE)[1]
sources = sorted(str(p.relative_to(root))
                 for p in (root / "usr/share/comm-release").rglob("*.py"))
subprocess.run([
    "xgettext", "--language=Python", "--from-code=UTF-8", "--keyword=_",
    "--package-name=community-release",
    f"--package-version={version}", "--output=locale/comm-release.pot", *sources,
], cwd=root, check=True)
if not args.pot_only:
    for source in sorted((root / "locale").glob("*.po")):
        # A similar English string is not evidence that its old translation
        # is still correct. New messages stay untranslated until reviewed.
        subprocess.run([
            "msgmerge", "--quiet", "--no-fuzzy-matching", "--update", "--backup=none",
            str(source), str(root / "locale/comm-release.pot"),
        ], check=True)
