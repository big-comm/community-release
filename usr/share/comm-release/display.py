"""Rich-based display for comm-release."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from utils.i18n import _
from info import SystemInfo

console = Console()

# BigCommunity web palette: clean whites, violet, magenta and restrained blue.
WHITE       = "bold #f8fafc"
MUTED       = "#a8adbd"
DIM         = "#6f7688"
PINK        = "bold #ec4899"
PURPLE      = "bold #b45cff"
VIOLET      = "bold #8b5cf6"
BLUE        = "bold #3b82f6"
BORDER      = "#4c3f91"
OK          = "bold #22c55e"
ERROR       = "bold #ef4444"


def _content_width(limit: int = 86) -> int:
    return max(44, min(console.width - 4, limit))


def _column_width() -> int:
    return max(44, min((console.width - 10) // 2, 62))


def _panel(renderable, *, title: str | None = None, width: int | None = None) -> Panel:
    return Panel(
        renderable,
        title=f"[{PINK}]{title}[/]" if title else None,
        border_style=BORDER,
        box=box.ROUNDED,
        padding=(1, 2),
        width=width,
    )


def _key_value_table(rows: list[tuple[str, str, str]], *, min_rows: int = 0) -> Table:
    table = Table.grid(padding=(0, 1))
    table.add_column("label", style=MUTED, justify="right", no_wrap=True)
    table.add_column("sep", style=DIM, no_wrap=True)
    table.add_column("value", no_wrap=False)

    padded_rows = rows + [("", "", DIM)] * max(0, min_rows - len(rows))
    for label, value, style in padded_rows:
        table.add_row(label, ":" if label or value else "", Text(value, style=style))

    return table


# ─── Banner ────────────────────────────────────────────────────────────────────

def display_banner() -> None:
    title = Text()
    title.append("Big", style=WHITE)
    title.append("Community", style=PINK)

    subtitle = Text(_("Distribution Information"), style=MUTED)
    accent = Text("Open Source  |  Livre  |  Comunitário", style=VIOLET)

    content = Group(
        Align.center(title),
        Align.center(subtitle),
        Padding(Align.center(accent), (1, 0, 0, 0)),
    )
    console.print(
        Align.center(_panel(content, width=_content_width(76)))
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
        rows.append((_("Distributor ID"), info.distrib.id,          PINK))
    if show_desc:
        rows.append((_("Description"),    info.distrib.description,  WHITE))
    if show_release:
        rows.append((_("Release"),        info.distrib.release,       VIOLET))
    if show_codename:
        rows.append((_("Codename"),       info.distrib.codename,      PURPLE))

    if not rows:
        return

    console.print(
        Align.center(
            _panel(
                _key_value_table(rows),
                title=_("Distribution Information"),
                width=_content_width(),
            )
        )
    )


# ─── Extended system information ───────────────────────────────────────────────

def _system_panel(info: SystemInfo, *, width: int | None = None) -> Panel:
    rows = [
        (_("Environment"),  info.environment,  OK),
        (_("Architecture"), info.architecture, VIOLET),
        (_("Kernel"),       info.kernel,       BLUE),
        (_("Processor"),    info.cpu,          WHITE),
        (_("Memory"),       info.memory,       PURPLE),
        (_("Uptime"),       info.uptime,       OK),
    ]

    return _panel(_key_value_table(rows), title=_("System Info"), width=width)


def _status_panel(
    info: SystemInfo,
    *,
    width: int | None = None,
    min_rows: int = 0,
) -> Panel:
    pending_style = (
        ERROR
        if info.pending_updates not in ("None", "Unknown", "0 packages")
        else OK
    )
    rows = [
        (_("Install Date"),    info.install_date,    DIM),
        (_("Last Update"),     info.last_update,     DIM),
        (_("Repositories"),    info.repositories,    BLUE),
        (_("Pending Updates"), info.pending_updates, pending_style),
    ]

    return _panel(
        _key_value_table(rows, min_rows=min_rows),
        title=_("System Status"),
        width=width,
    )


def display_extended(info: SystemInfo) -> None:
    console.print()

    if console.width >= 104:
        width = _column_width()
        panels = [
            _system_panel(info, width=width),
            _status_panel(info, width=width, min_rows=6),
        ]
        console.print(
            Align.center(Columns(panels, padding=(2, 2), equal=True, expand=False))
        )
        return

    width = _content_width()
    console.print(Align.center(_system_panel(info, width=width)))
    console.print(Align.center(_status_panel(info, width=width)))


# ─── Footer ────────────────────────────────────────────────────────────────────

def display_footer() -> None:
    console.print()

    if console.width >= 100:
        table = Table.grid(padding=(0, 3))
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_column(no_wrap=True)
        table.add_row(
            Text.assemble(
                (_("Website:"), MUTED),
                (" https://communitybig.org", BLUE),
            ),
            Text.assemble(
                (_("Support:"), MUTED),
                (" https://t.me/BigLinuxCommunity", VIOLET),
            ),
            Text.assemble(
                (_("Donate: "), MUTED),
                (" https://t.me/DoacaoCommunityBot", PINK),
            ),
        )
        console.print(Align.center(table))
    else:
        table = Table.grid(padding=(0, 1))
        table.add_column("label", style=MUTED, justify="right", no_wrap=True)
        table.add_column("url", no_wrap=True)
        table.add_row(_("Website:"), Text("https://communitybig.org", style=BLUE))
        table.add_row(_("Support:"), Text("https://t.me/BigLinuxCommunity", style=VIOLET))
        table.add_row(_("Donate: "), Text("https://t.me/DoacaoCommunityBot", style=PINK))
        console.print(Align.center(table))

    console.print()


# ─── Short (plain-text) output ─────────────────────────────────────────────────

def display_short(parts: list[str]) -> None:
    print(" ".join(parts))


# ─── Colored help screen ───────────────────────────────────────────────────────

def display_help(version: str) -> None:
    display_banner()

    title = Text.assemble(
        (f"comm-release v{version}", PURPLE),
        ("  -  ", DIM),
        (_("Distribution Information Tool"), WHITE),
    )
    usage = Text.assemble(
        (_("Usage"), VIOLET),
        (":  ", DIM),
        ("comm-release", PINK),
        ("  [OPTION]...", WHITE),
    )
    description = Text(
        _("With no OPTION specified defaults to showing all information (same as -a)."),
        style=MUTED,
    )

    console.print(Align.center(title))
    console.print()
    console.print(Align.center(usage))
    console.print(Align.center(description))
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

    table = Table.grid(padding=(0, 2))
    table.add_column("flag", style=VIOLET, no_wrap=True)
    table.add_column("desc", style=WHITE, no_wrap=False)

    for flag, desc in options:
        table.add_row(flag, desc)

    console.print(
        Align.center(
            _panel(table, title=_("Options:"), width=_content_width())
        )
    )
    console.print()


# ─── Version screen ────────────────────────────────────────────────────────────

def display_version(version: str) -> None:
    title = Text.assemble(
        ("BigCommunity comm-release  v", WHITE),
        (version, PINK),
    )
    copyright_text = Text(_("Copyright (C) 2025 BigCommunity"), style=MUTED)
    license_text = Text(
        _("This is free software; see the source for copying conditions."),
        style=DIM,
    )

    console.print(Align.center(title))
    console.print()
    console.print(Align.center(copyright_text))
    console.print(Align.center(license_text))
    console.print()


# ─── Error ─────────────────────────────────────────────────────────────────────

def display_error(message: str) -> None:
    console.print(
        Text.assemble(
            (_("Error"), ERROR),
            (":  ", DIM),
            (message, WHITE),
        )
    )
