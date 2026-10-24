"""Entry point and CLI for comm-release."""

from __future__ import annotations

import sys

from utils.i18n import _
from info import SystemInfo, collect_all, collect_distrib

VERSION = "2.1.0"

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
    "tui":         False,
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
    "-t": "tui",          "--tui":             "tui",
}


def _parse_args(argv: list[str]) -> dict[str, bool]:
    flags = dict(_FLAGS)

    # Accept lsb_release-style combinations such as -rs and -as.
    argv = [part for arg in argv for part in (
        [f"-{ch}" for ch in arg[1:]]
        if arg.startswith("-") and not arg.startswith("--") and len(arg) > 2
        else [arg]
    )]

    for arg in argv:
        if arg in ("-p", "--program-version"):
            from display import display_version
            display_version(VERSION)
            sys.exit(0)

        if arg in ("-h", "--help"):
            from display import display_help
            display_help(VERSION)
            sys.exit(0)

        if arg in _KNOWN_FLAGS:
            flags[_KNOWN_FLAGS[arg]] = True
        else:
            from display import display_error
            display_error(_("unknown option") + f" '{arg}'")
            sys.exit(1)

    return flags


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    flags = _parse_args(sys.argv[1:])

    if flags["tui"]:
        if any(flags[k] for k in flags if k != "tui"):
            print(_("Use --tui on its own."), file=sys.stderr)
            sys.exit(1)
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print(_("--tui requires an interactive terminal."), file=sys.stderr)
            sys.exit(1)
        try:
            from tui import ReleaseApp
        except ModuleNotFoundError as exc:
            if exc.name != "textual":
                raise
            print(_("The interactive mode requires python-textual."), file=sys.stderr)
            sys.exit(1)
        ReleaseApp().run()
        return

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

    # ── Short / plain-text output ──────────────────────────────────────────────
    if flags["short"]:
        # Identity queries never import Rich or query hardware / package tools.
        info = SystemInfo(distrib=collect_distrib())
        parts: list[str] = []
        if flags["id"]:          parts.append(info.distrib.id)
        if flags["description"]: parts.append(f'"{info.distrib.description}"')
        if flags["release"]:     parts.append(info.distrib.release)
        if flags["codename"]:    parts.append(info.distrib.codename)
        print(" ".join(parts))
        return

    if flags["all"]:
        from dashboard import display_dashboard
        display_dashboard()
        return

    from display import (
        display_banner, display_basic_info, display_extended, display_footer,
    )
    info = collect_all() if flags["extended"] else SystemInfo(distrib=collect_distrib())

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
