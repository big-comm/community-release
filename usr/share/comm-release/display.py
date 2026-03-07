"""Rich-based display for comm-release."""

from __future__ import annotations

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from utils.i18n import _
from info import SystemInfo

console = Console()

# ─── Color palette (BigCommunity theme) ───────────────────────────────────────
BLUE_DARK  = "bold #1f6feb"   # Deep blue   — labels / borders
LIGHT_BLUE = "bold #58a6ff"   # Light blue  — secondary values
CYAN       = "bold #39d5f5"   # Cyan        — IDs and key accents
WHITE      = "bold white"     # White       — descriptions / values
GREEN      = "bold #56d364"   # Green       — environment / uptime / ok
YELLOW     = "bold #e3b341"   # Yellow      — architecture / notices
RED        = "bold #f85149"   # Red         — errors / pending updates
PURPLE     = "bold #bc8cff"   # Purple      — section headers
ORANGE     = "bold #d18616"   # Orange      — processor
GRAY       = "#8b949e"        # Gray        — dates / dim text


# ─── Banner ────────────────────────────────────────────────────────────────────

def display_banner() -> None:
    title = Text()
    title.append("Big", style=LIGHT_BLUE)
    title.append("Community", style=CYAN)

    subtitle = Text(_("Distribution Information"), style=GRAY)

    content = Align.center(Text.assemble(title, "\n", subtitle))
    console.print(
        Panel(content, border_style=BLUE_DARK, expand=False, padding=(1, 8))
    )
    console.print()


# ─── Basic distribution info ───────────────────────────────────────────────────

def display_basic_info(
    info: SystemInfo,
    *,
    show_id: bool = False,
    show_desc: bool = False,
    show_release: bool = False,
    show_codename: bool = False,
) -> None:
    rows = []
    if show_id:
        rows.append((_("Distributor ID"), info.distrib.id,          CYAN))
    if show_desc:
        rows.append((_("Description"),    info.distrib.description,  WHITE))
    if show_release:
        rows.append((_("Release"),        info.distrib.release,       LIGHT_BLUE))
    if show_codename:
        rows.append((_("Codename"),       info.distrib.codename,      CYAN))

    if not rows:
        return

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("label", style=BLUE_DARK, justify="right", no_wrap=True)
    table.add_column("sep",   style=GRAY,      no_wrap=True)
    table.add_column("value",                  no_wrap=False)

    for label, value, style in rows:
        table.add_row(label, ":", Text(value, style=style))

    console.print(table)


# ─── Extended system information ───────────────────────────────────────────────

def _system_panel(info: SystemInfo) -> Panel:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("label", style=BLUE_DARK, justify="right", no_wrap=True)
    table.add_column("sep",   style=GRAY,      no_wrap=True)
    table.add_column("value",                  no_wrap=False)

    table.add_row(_("Environment"),  ":", Text(info.environment,  style=GREEN))
    table.add_row(_("Architecture"), ":", Text(info.architecture, style=YELLOW))
    table.add_row(_("Kernel"),       ":", Text(info.kernel,       style=LIGHT_BLUE))
    table.add_row(_("Processor"),    ":", Text(info.cpu,          style=ORANGE))
    table.add_row(_("Memory"),       ":", Text(info.memory,       style=CYAN))
    table.add_row(_("Uptime"),       ":", Text(info.uptime,       style=GREEN))

    return Panel(
        table,
        title=f"[{PURPLE}]{_('System Info')}[/]",
        border_style=BLUE_DARK,
        expand=True,
    )


def _status_panel(info: SystemInfo) -> Panel:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("label", style=BLUE_DARK, justify="right", no_wrap=True)
    table.add_column("sep",   style=GRAY,      no_wrap=True)
    table.add_column("value",                  no_wrap=False)

    pending_style = (
        RED
        if info.pending_updates not in ("None", "Unknown", "0 packages")
        else GREEN
    )

    table.add_row(_("Install Date"),    ":", Text(info.install_date,    style=GRAY))
    table.add_row(_("Last Update"),     ":", Text(info.last_update,     style=GRAY))
    table.add_row(_("Repositories"),    ":", Text(info.repositories,    style=LIGHT_BLUE))
    table.add_row(_("Pending Updates"), ":", Text(info.pending_updates, style=pending_style))

    return Panel(
        table,
        title=f"[{PURPLE}]{_('System Status')}[/]",
        border_style=BLUE_DARK,
        expand=True,
    )


def display_extended(info: SystemInfo) -> None:
    console.print()
    console.print(Columns([_system_panel(info), _status_panel(info)]))


# ─── Footer ────────────────────────────────────────────────────────────────────

def display_footer() -> None:
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("bullet", style=PURPLE,    no_wrap=True)
    table.add_column("label",  style=GRAY,      no_wrap=True)
    table.add_column("url",                     no_wrap=True)

    table.add_row("◆", _("Website:"), Text("https://communitybig.org",          style=CYAN))
    table.add_row("◆", _("Support:"), Text("https://t.me/BigLinuxCommunity",     style=LIGHT_BLUE))
    table.add_row("◆", _("Donate: "), Text("https://t.me/DoacaoCommunityBot",    style=ORANGE))

    console.print(table)
    console.print()


# ─── Short (plain-text) output ─────────────────────────────────────────────────

def display_short(parts: list[str]) -> None:
    print(" ".join(parts))


# ─── Colored help screen ───────────────────────────────────────────────────────

def display_help(version: str) -> None:
    display_banner()

    console.print(
        Text.assemble(
            (f"comm-release v{version}", BLUE_DARK),
            ("  —  ", GRAY),
            (_("Distribution Information Tool"), WHITE),
        )
    )
    console.print()

    console.print(
        Text.assemble(
            (_("Usage"), LIGHT_BLUE),
            (":  ", GRAY),
            ("comm-release", CYAN),
            ("  [OPTION]...", WHITE),
        )
    )
    console.print(
        Text(
            _("With no OPTION specified defaults to showing all information (same as -a)."),
            style=YELLOW,
        )
    )
    console.print()

    console.print(Text(_("Options:"), style=LIGHT_BLUE))
    console.print()

    options = [
        ("-i,  --id",              _("Display the distributor ID")),
        ("-d,  --description",     _("Display the distribution description")),
        ("-r,  --release",         _("Display the release number")),
        ("-c,  --codename",        _("Display the codename")),
        ("-a,  --all",             _("Display all information")),
        ("-e,  --extended",        _("Display extended system information")),
        ("-s,  --short",           _("Use short output format (plain text)")),
        ("-b,  --banner",          _("Display with banner")),
        ("-p,  --program-version", _("Display program version")),
        ("-h,  --help",            _("Display this help message")),
    ]

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("flag", style=CYAN,  no_wrap=True)
    table.add_column("desc", style=WHITE, no_wrap=False)

    for flag, desc in options:
        table.add_row(flag, desc)

    console.print(table)
    console.print()


# ─── Version screen ────────────────────────────────────────────────────────────

def display_version(version: str) -> None:
    console.print(
        Text.assemble(
            ("BigCommunity comm-release  v", BLUE_DARK),
            (version, CYAN),
        )
    )
    console.print()
    console.print(Text(_("Copyright (C) 2025 BigCommunity"), style=WHITE))
    console.print(
        Text(
            _("This is free software; see the source for copying conditions."),
            style=GRAY,
        )
    )
    console.print()


# ─── Error ─────────────────────────────────────────────────────────────────────

def display_error(message: str) -> None:
    console.print(
        Text.assemble(
            (_("Error"), RED),
            (":  ", GRAY),
            (message, WHITE),
        )
    )
