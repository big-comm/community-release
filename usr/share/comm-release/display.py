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
MUTED       = "#9aa3b8"
DIM         = "#68708a"
PINK        = "bold #ff4fa3"
PURPLE      = "bold #a855f7"
VIOLET      = "bold #7c5cff"
BLUE        = "bold #2294ff"
BORDER      = "#3f4b8f"
BORDER_BLUE = "#1777d4"
BORDER_PINK = "#bf3b8e"
OK          = "bold #2fe66b"
ERROR       = "bold #ff5f6d"
WATERMARK   = "#111939"


def _content_width(limit: int = 104) -> int:
    available = max(32, console.width - 4)
    return min(available, limit)


def _column_width() -> int:
    return max(40, min((_content_width(118) - 4) // 2, 58))


def _panel(
    renderable,
    *,
    title: str | None = None,
    width: int | None = None,
    border_style: str = BORDER,
    title_style: str = PINK,
    padding: tuple[int, int] = (1, 2),
) -> Panel:
    return Panel(
        renderable,
        title=f"[{title_style}]{title}[/]" if title else None,
        border_style=border_style,
        box=box.ROUNDED,
        padding=padding,
        width=width,
    )


def _section(
    renderable,
    *,
    label: str,
    icon: str,
    width: int | None = None,
    border_style: str = BORDER,
    title_style: str = PINK,
) -> Panel:
    header = Text.assemble(
        (icon, title_style),
        ("  " + label.upper(), title_style),
    )
    content = Group(header, Padding(renderable, (1, 0, 0, 0)))

    return _panel(
        content,
        width=width,
        border_style=border_style,
        title_style=title_style,
    )


def _key_value_table(rows: list[tuple[str, str, str]]) -> Table:
    table = Table.grid(padding=(0, 1))
    table.add_column("label", style=MUTED, no_wrap=True)
    table.add_column("sep", style=DIM, no_wrap=True)
    table.add_column("value", no_wrap=False)

    for label, value, style in rows:
        table.add_row(label, ":", Text(value, style=style))

    return table


def _icon_table(rows: list[tuple[str, str, str, str]], *, min_rows: int = 0) -> Table:
    table = Table.grid(padding=(0, 1))
    table.add_column("icon", style=DIM, justify="center", no_wrap=True)
    table.add_column("label", style=MUTED, no_wrap=True)
    table.add_column("sep", style=DIM, no_wrap=True)
    table.add_column("value", no_wrap=False)

    padded_rows = rows + [("", "", "", DIM)] * max(0, min_rows - len(rows))
    for icon, label, value, style in padded_rows:
        table.add_row(
            Text(icon, style=style),
            label,
            ":" if label or value else "",
            Text(value, style=style),
        )

    return table


def _dot_matrix(style: str) -> Text:
    return Text("•  •  •  •  •\n  •  •  •  •\n•  •  •  •  •", style=style)


def _brand_mark(style: str = WATERMARK) -> Text:
    return Text("  ◉   ◉\n    ◡\n╰─────╯", style=style)


# ─── Banner ────────────────────────────────────────────────────────────────────

def display_banner() -> None:
    logo = Text("◉◡◉", style=VIOLET)
    title = Text.assemble(
        ("Big", WHITE),
        ("Com", PINK),
        ("mun", PURPLE),
        ("ity", BLUE),
    )
    brand = Table.grid(padding=(0, 1))
    brand.add_column(justify="right", no_wrap=True)
    brand.add_column(justify="left", no_wrap=True)
    brand.add_row(logo, title)

    subtitle = Text(_("Distribution Information"), style=MUTED)
    accent = Text.assemble(
        ("Open Source", BLUE),
        ("     |     ", DIM),
        ("Livre", PINK),
        ("     |     ", DIM),
        ("Comunitário", VIOLET),
    )

    center = Group(
        Align.center(brand),
        Align.center(subtitle),
        Padding(Align.center(accent), (1, 0, 0, 0)),
    )
    if console.width >= 100:
        content = Table.grid(expand=True)
        content.add_column(ratio=1, justify="left")
        content.add_column(ratio=4, justify="center")
        content.add_column(ratio=1, justify="right")
        content.add_row(
            Padding(_dot_matrix("#0d4ea6"), (1, 0, 0, 0)),
            center,
            Padding(_dot_matrix("#72265f"), (1, 0, 0, 0)),
        )
    else:
        content = center

    console.print(
        Align.center(
            _panel(
                content,
                width=_content_width(96),
                border_style=BORDER_PINK,
                padding=(0, 2),
            )
        )
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

    body = _key_value_table(rows)
    if console.width >= 84:
        layout = Table.grid(expand=True)
        layout.add_column(ratio=3)
        layout.add_column(width=18, justify="right")
        layout.add_row(body, Align.center(_brand_mark()))
        body = layout

    console.print(
        Align.center(
            _section(
                body,
                label=_("Distribution Information"),
                icon="◆",
                width=_content_width(96),
                border_style=VIOLET,
                title_style=PINK,
            )
        )
    )


# ─── Extended system information ───────────────────────────────────────────────

def _system_panel(info: SystemInfo, *, width: int | None = None) -> Panel:
    rows = [
        ("▪", _("Environment"),  info.environment,  OK),
        ("◇", _("Architecture"), info.architecture, BLUE),
        ("▦", _("Kernel"),       info.kernel,       BLUE),
        ("✦", _("Processor"),    info.cpu,          WHITE),
        ("▰", _("Memory"),       info.memory,       PINK),
        ("◷", _("Uptime"),       info.uptime,       OK),
    ]

    return _section(
        _icon_table(rows),
        label=_("System Info"),
        icon="▣",
        width=width,
        border_style=BORDER_BLUE,
        title_style=BLUE,
    )


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
        ("□", _("Install Date"),    info.install_date,    BLUE),
        ("↻", _("Last Update"),     info.last_update,     VIOLET),
        ("▦", _("Repositories"),    info.repositories,    BLUE),
        ("↑", _("Pending Updates"), info.pending_updates, pending_style),
    ]

    return _section(
        _icon_table(rows, min_rows=min_rows),
        label=_("System Status"),
        icon="⌁",
        width=width,
        border_style=PURPLE,
        title_style=PURPLE,
    )


def display_extended(info: SystemInfo) -> None:
    console.print()

    if console.width >= 108:
        width = _column_width()
        panels = [
            _system_panel(info, width=width),
            _status_panel(info, width=width, min_rows=8),
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

    if console.width >= 118:
        donate_label = _("Donate: ").strip()
        content = Align.center(
            Text.assemble(
                ("◎ ", BLUE),
                (_("Website:"), MUTED),
                (" https://communitybig.org", BLUE),
                ("  │  ", DIM),
                ("♙ ", VIOLET),
                (_("Support:"), MUTED),
                (" https://t.me/BigLinuxCommunity", VIOLET),
                ("  │  ", DIM),
                ("♡ ", PINK),
                (donate_label, MUTED),
                (" https://t.me/DoacaoCommunityBot", PINK),
            )
        )
        footer_width = _content_width(136)
        footer_padding = (0, 1)
    else:
        table = Table.grid(padding=(0, 1))
        table.add_column("label", style=MUTED, justify="right", no_wrap=True)
        table.add_column("url", no_wrap=True)
        table.add_row(_("Website:"), Text("https://communitybig.org", style=BLUE))
        table.add_row(_("Support:"), Text("https://t.me/BigLinuxCommunity", style=VIOLET))
        table.add_row(_("Donate: "), Text("https://t.me/DoacaoCommunityBot", style=PINK))
        content = Align.center(table)
        footer_width = _content_width(96)
        footer_padding = (0, 2)

    console.print(
        Align.center(
            _panel(
                content,
                width=footer_width,
                border_style=BORDER,
                padding=footer_padding,
            )
        )
    )
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
