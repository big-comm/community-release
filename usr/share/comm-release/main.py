"""Entry point and CLI for comm-release."""

from __future__ import annotations

import sys

from utils.i18n import _
from info import collect_all
from display import (
    display_banner,
    display_basic_info,
    display_error,
    display_extended,
    display_footer,
    display_help,
    display_short,
    display_version,
)

VERSION = "2.0.0"

# ─── Argument parsing ──────────────────────────────────────────────────────────

_FLAGS = {
    "id":          False,
    "description": False,
    "release":     False,
    "codename":    False,
    "all":         False,
    "extended":    False,
    "short":       False,
    "banner":      False,
}

_KNOWN_FLAGS: dict[str, str] = {
    "-i": "id",           "--id":              "id",
    "-d": "description",  "--description":     "description",
    "-r": "release",      "--release":         "release",
    "-c": "codename",     "--codename":        "codename",
    "-a": "all",          "--all":             "all",
    "-e": "extended",     "--extended":        "extended",
    "-s": "short",        "--short":           "short",
    "-b": "banner",       "--banner":          "banner",
}


def _parse_args(argv: list[str]) -> dict[str, bool]:
    flags = dict(_FLAGS)

    for arg in argv:
        if arg in ("-p", "--program-version"):
            display_version(VERSION)
            sys.exit(0)

        if arg in ("-h", "--help"):
            display_help(VERSION)
            sys.exit(0)

        if arg in _KNOWN_FLAGS:
            flags[_KNOWN_FLAGS[arg]] = True
        else:
            display_error(_("unknown option") + f" '{arg}'")
            sys.exit(1)

    return flags


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    flags = _parse_args(sys.argv[1:])

    # Determine if any display flag was explicitly requested
    no_display = not any(
        flags[k] for k in ("id", "description", "release", "codename", "extended", "banner", "all")
    )

    if no_display:
        if flags["short"]:
            # lsb_release compatibility: -s alone → show release only
            flags["release"] = True
        else:
            # No args at all → show everything with banner
            flags.update(
                id=True, description=True, release=True, codename=True,
                extended=True, banner=True, all=True,
            )
    elif flags["all"]:
        flags.update(
            id=True, description=True, release=True, codename=True,
            extended=True, banner=True,
        )

    # Collect system information
    info = collect_all()

    # ── Short / plain-text output ──────────────────────────────────────────────
    if flags["short"]:
        parts: list[str] = []
        if flags["id"]:          parts.append(info.distrib.id)
        if flags["description"]: parts.append(f'"{info.distrib.description}"')
        if flags["release"]:     parts.append(info.distrib.release)
        if flags["codename"]:    parts.append(info.distrib.codename)
        display_short(parts)
        return

    # ── Formatted / colored output ─────────────────────────────────────────────
    if flags["banner"]:
        display_banner()

    display_basic_info(
        info,
        show_id=flags["id"],
        show_desc=flags["description"],
        show_release=flags["release"],
        show_codename=flags["codename"],
    )

    if flags["extended"]:
        display_extended(info)

    if flags["banner"]:
        display_footer()


if __name__ == "__main__":
    main()
