"""Optional Textual shell around the shared dashboard (no network on mount)."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Static
from textual.worker import get_current_worker

from dashboard import LINKS, dashboard, gradient
from info import SystemInfo, collect_all, collect_distrib
from utils.i18n import _


class ReleaseApp(App):
    TITLE = "BigCommunity"
    CSS = """
    Screen { background: #171a22; color: #edf0f7; }
    #brand { height: 1; margin: 1 2 0 2; }
    #content { height: 1fr; scrollbar-color: #ad87ff; scrollbar-background: #171a22; }
    #dashboard { width: 100%; height: auto; padding: 1 2; }
    Footer { background: #242936; color: #a6aec0; }
    Footer > .footer-key--key { background: #343b50; color: #ad87ff; }
    """
    BINDINGS = [
        Binding("r", "refresh_info", _("Refresh")),
        Binding("o", "website", _("Website")),
        Binding("s", "support", _("Support")),
        Binding("d", "donate", _("Donate")),
        Binding("q,escape", "quit", _("Quit")),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.info = SystemInfo(distrib=collect_distrib())

    def compose(self) -> ComposeResult:
        yield Static(gradient("BigCommunity  /  " + _("Distribution Information")), id="brand")
        with VerticalScroll(id="content"):
            yield Static(id="dashboard", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        # The first frame is drawn before potentially slower local probes.
        self.draw_dashboard()
        self.action_refresh_info()

    def on_resize(self) -> None:
        if self.is_mounted:
            self.draw_dashboard()

    def draw_dashboard(self) -> None:
        self.query_one("#dashboard", Static).update(dashboard(
            self.info, self.size.width - 4, interactive=True,
            compact=self.size.height < 34,
        ))

    @work(thread=True, exclusive=True, group="collect")
    def action_refresh_info(self) -> None:
        # Refresh never syncs repositories or installs packages.
        worker = get_current_worker()
        info = collect_all()
        if not worker.is_cancelled:
            self.call_from_thread(self.apply_info, info)

    def apply_info(self, info: SystemInfo) -> None:
        self.info = info
        self.draw_dashboard()

    def action_website(self) -> None:
        self.open_url(LINKS[0][2])

    def action_support(self) -> None:
        self.open_url(LINKS[1][2])

    def action_donate(self) -> None:
        self.open_url(LINKS[2][2])
