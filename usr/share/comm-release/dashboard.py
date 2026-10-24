"""Shared Rich dashboard for the one-shot CLI and the interactive TUI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from info import SystemInfo, collect_all, collect_distrib
from utils.i18n import _

FG = "#edf0f7"
MUTED = "#a6aec0"
DIM = "#747f95"
BLUE = "#379bff"
PINK = "#ff4fa3"
PURPLE = "#ad87ff"
GREEN = "#58d68a"
BORDER = "#414655"
LINKS = (
    ("Website", "communitybig.org", "https://communitybig.org", BLUE),
    ("Support", "t.me/BigLinuxCommunity", "https://t.me/BigLinuxCommunity", PURPLE),
    ("Donate", "t.me/DoacaoCommunityBot", "https://t.me/DoacaoCommunityBot", PINK),
)


def display_value(value: str) -> str:
    if value == "Unknown":
        return _("Unavailable")
    if value == "Bare Metal":
        return _("Bare Metal")
    repositories = re.fullmatch(r"(\d+) (Pacman|APT) repositories", value)
    if repositories:
        return f"{repositories[1]} · {repositories[2]}"
    return value


def gradient(value: str) -> Text:
    """Paint a small wordmark without requiring a special terminal font."""
    text = Text(value, style="bold")
    stops = ((55, 155, 255), (173, 135, 255), (255, 79, 163))
    for i in range(len(value)):
        position = i / max(1, len(value) - 1) * 2
        segment = min(1, int(position))
        fraction = position - segment
        rgb = tuple(round(a + (b - a) * fraction)
                    for a, b in zip(stops[segment], stops[segment + 1]))
        text.stylize("#%02x%02x%02x" % rgb, i, i + 1)
    return text


@lru_cache(maxsize=1)
def owl() -> Text:
    # Pre-rendered at build time. No image converter or fastfetch at startup.
    path = Path(__file__).with_name("assets") / "owl.ansi"
    try:
        text = Text.from_ansi(path.read_text())
        text.rstrip()
        return text
    except OSError:
        return gradient("BigCommunity")


def card(title: str, body, accent: str, *, width: int | None = None) -> Panel:
    return Panel(
        body, title=Text(" " + title + " ", style=f"bold {accent}"),
        title_align="left", border_style=BORDER, box=box.ROUNDED,
        padding=(1, 2), width=width,
    )


def rows(items: list[tuple[str, str, str]], width: int) -> Table:
    short_labels = {
        _("Distributor ID"): "ID", _("Release"): _("Version"),
        _("Codename"): _("Code name"), _("Processor"): "CPU",
        _("Architecture"): _("Arch"), _("Install Date"): _("Installed"),
        _("Last Update"): _("Updated"), _("Repositories"): _("Repos"),
        _("Updates (local)"): _("Pending"),
    }
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(width=max(9, min(19, width // 3)), style=MUTED,
                     overflow="ellipsis", no_wrap=True)
    table.add_column(ratio=1, overflow="ellipsis", no_wrap=True)
    for label, value, color in items:
        if width < 48:
            label = short_labels.get(label, label)
        table.add_row(Text(label), Text(display_value(value), style=color))
    return table


def hero(info: SystemInfo, width: int, compact: bool = False) -> Panel:
    brand = Group(
        gradient("BigCommunity"),
        Text(_("Distribution Information"), style=MUTED),
        Text(),
        Text.assemble((info.distrib.release, f"bold {FG}"), ("  /  ", DIM),
                      (info.distrib.codename, PURPLE)),
        Text(),
        Text.assemble(("Open Source", BLUE), ("  ·  ", DIM),
                      (_("Free software"), PINK), ("  ·  ", DIM),
                      (_("Community-driven"), PURPLE)),
    )
    if width >= 72 and not compact:
        content = Table.grid(expand=True, padding=(0, 3))
        content.add_column(width=24)
        content.add_column(ratio=1)
        content.add_row(owl(), Align(brand, vertical="middle", height=10))
    else:
        content = brand
    return Panel(content, box=box.ROUNDED, border_style=PURPLE,
                 padding=(0 if width >= 72 and not compact else 1, 2), width=width)


def distribution(info: SystemInfo, width: int) -> Panel:
    return card(_("Distribution"), rows([
        (_("Distributor ID"), info.distrib.id, BLUE),
        (_("Description"), info.distrib.description, FG),
        (_("Release"), info.distrib.release, PURPLE),
        (_("Codename"), info.distrib.codename, PURPLE),
    ], width), BLUE, width=width)


def system(info: SystemInfo, width: int) -> Panel:
    return card(_("System"), rows([
        (_("Processor"), info.cpu, FG),
        (_("Architecture"), info.architecture, BLUE),
        (_("Kernel"), info.kernel, BLUE),
        (_("Environment"), info.environment, GREEN),
    ], width), PURPLE, width=width)


def resources(info: SystemInfo, width: int) -> Panel:
    total = info.memory_total_kib
    available = info.memory_available_kib
    if total > 0 and available >= 0:
        used = max(0, min(total, total - available))
        ratio = used / total
        bar_width = max(8, width - 8)
        filled = round(ratio * bar_width)
        bar = Text.assemble(("━" * filled, PINK), ("━" * (bar_width - filled), BORDER))
        memory = Text.assemble(
            (_("Memory"), MUTED), ("  ", DIM),
            (f"{used / 1024**2:.1f} / {total / 1024**2:.1f} GiB", f"bold {PINK}"),
            (f"  {ratio:.0%}", MUTED),
        )
    else:
        memory = Text.assemble((_("Memory") + "  ", MUTED), (info.memory, PINK))
        bar = Text("─" * max(8, width - 8), style=BORDER)
    uptime = Text.assemble((_("Uptime") + "  ", MUTED), (info.uptime, f"bold {GREEN}"))
    return card(_("Resources"), Group(memory, bar, Text(), uptime), PINK, width=width)


def status(info: SystemInfo, width: int) -> Panel:
    pending = info.pending_updates
    if pending == "None":
        pending = _("No pending updates")
        color = GREEN
    elif pending == "Unknown":
        pending = _("Unavailable")
        color = MUTED
    else:
        count = re.fullmatch(r"(\d+) packages", pending)
        if count:
            pending = count[1]
        color = PINK
    return card(_("Status"), rows([
        (_("Install Date"), info.install_date, FG),
        (_("Last Update"), info.last_update[:16], FG),
        (_("Repositories"), info.repositories, BLUE),
        (_("Updates (local)"), pending, color),
    ], width), GREEN, width=width)


def footer(width: int):
    if width >= 100:
        table = Table.grid(expand=True, padding=(0, 2))
        for _item in LINKS:
            table.add_column(ratio=1)
        table.add_row(*[
            Text.assemble((_(label) + "  ", MUTED),
                          (domain, f"{color} link {url}"))
            for label, domain, url, color in LINKS
        ])
        return table
    return Group(*[
        Text.assemble((_(label) + "  ", MUTED), (domain, f"{color} link {url}"))
        for label, domain, url, color in LINKS
    ])


def dashboard(info: SystemInfo, width: int, *, interactive: bool = False,
              compact: bool = False, show_hero: bool = True) -> Group:
    """Build a bounded, responsive snapshot with no terminal side effects."""
    width = max(12, min(width, 124))
    sections = [hero(info, width, compact)] if show_hero else []
    if width >= 76:
        left = (width - 2) // 2
        right = width - left - 2
        for first, second in ((distribution, system), (resources, status)):
            pair = Table.grid(padding=(0, 2))
            pair.add_column(width=left)
            pair.add_column(width=right)
            pair.add_row(first(info, left), second(info, right))
            sections.append(pair)
    else:
        sections.extend(factory(info, width) for factory in
                        (distribution, system, resources, status))
    sections.append(Panel(footer(width), box=box.ROUNDED, border_style=BORDER,
                          padding=(0, 2), width=width))
    sections.append(Text(_("Updates use the local database; no network sync."), style=DIM))
    if not interactive:
        sections.append(Text.assemble(("comm-release --tui", PURPLE),
                                      ("  ·  " + _("Interactive dashboard"), MUTED)))
    return Group(*sections)


def display_dashboard(info: SystemInfo | None = None) -> None:
    console = Console()
    width = max(12, min(console.width - 2, 124))
    identity = info or SystemInfo(distrib=collect_distrib())
    # Flush the identity before local package probes; even a slow or locked
    # database must not delay the first visible frame.
    console.print(Align.center(hero(identity, width)))
    info = info or collect_all()
    console.print(Align.center(dashboard(info, width, show_hero=False)))
