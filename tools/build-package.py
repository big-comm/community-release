#!/usr/bin/env python3
"""Build an Arch package from the exact committed tree, without installing it."""

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parent.parent


def git(*args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


if git("status", "--porcelain", "--untracked-files=normal"):
    sys.exit("Commit the reviewed changes before running make pkg.")

commit = git("rev-parse", "HEAD")
target = root / "build" / commit[:12]
target.mkdir(parents=True, exist_ok=True)
source = target / f"community-release-{commit[:12]}.tar.gz"
subprocess.run([
    "git", "-C", str(root), "archive", "--format=tar.gz",
    "--prefix=community-release/", f"--output={source}", commit,
], check=True)
checksum = hashlib.sha256(source.read_bytes()).hexdigest()

# Use the production PKGBUILD's build/check/package functions. Only the
# source transport changes: a checksummed local archive replaces the Git URL.
recipe = git("show", f"{commit}:pkgbuild/PKGBUILD")
recipe = re.sub(r"^source=.*$", f'source=("{source.name}")', recipe, flags=re.MULTILINE)
recipe = re.sub(r"^md5sums=.*$", f"sha256sums=('{checksum}')", recipe, flags=re.MULTILINE)
(target / "PKGBUILD").write_text(recipe + "\n")
(target / "pkgbuild.install").write_text(git("show", f"{commit}:pkgbuild/pkgbuild.install") + "\n")
subprocess.run(
    ["makepkg", "--force", "--cleanbuild", "--noconfirm"], cwd=target, check=True,
    env={**os.environ, "PKGDEST": str(target), "BUILDDIR": str(target)},
)
packages = sorted(p for p in target.glob("*.pkg.tar*") if not p.name.endswith(".sig"))
if not packages:
    sys.exit("makepkg finished without a package archive in the build directory.")
manifest = f"{commit}\n{checksum}  {source.name}\n"
for package in packages:
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    manifest += f"{digest}  {package.name}\n"
(target / "SOURCE-REVISION").write_text(manifest)
print(f"Built from {commit}", flush=True)
for package in packages:
    print(package)
