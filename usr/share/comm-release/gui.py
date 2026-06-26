"""GTK4/libadwaita interface for comm-release."""

from __future__ import annotations

import math
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk, Pango

from info import SystemInfo, collect_all
from utils.i18n import _

APP_ID = "org.bigcommunity.CommRelease"
APP_TITLE = "BigCommunity"
APP_ICON_NAME = APP_ID
BRAND_ICON_NAME = "about"

BLUE = "#2f93ff"
BLUE_SOFT = "#78a8f8"
PINK = "#ff4fa3"
PURPLE = "#a855f7"
VIOLET = "#777ce8"
GREEN = "#54d875"
WARN = "#e4b562"
RED = "#ff5574"

CSS = f"""
window {{
  background-color: @window_bg_color;
  color: @window_fg_color;
}}

headerbar {{
  background-color: @headerbar_bg_color;
  box-shadow: none;
  border-bottom: 0;
}}

.main-view {{
  padding: 6px 14px 8px;
  background-color: @window_bg_color;
}}

.hero-card,
.info-card,
.footer-button {{
  border-radius: 16px;
  border: 1px solid alpha(currentColor, .08);
  background-color: @card_bg_color;
  box-shadow: 0 1px 3px alpha(black, .12);
}}

.hero-card {{
  padding: 10px 24px;
  min-height: 92px;
  background-image:
    radial-gradient(ellipse at 32% 0%, alpha({PURPLE}, .12), alpha({PURPLE}, 0) 34%),
    radial-gradient(ellipse at 78% 0%, alpha({BLUE}, .08), alpha({BLUE}, 0) 38%),
    linear-gradient(135deg, @card_bg_color, @view_bg_color);
}}

.info-card {{
  padding: 10px 20px;
  min-height: 126px;
}}

.footer-button {{
  padding: 8px 16px;
  min-height: 40px;
  border-radius: 12px;
}}

.footer-button:hover,
.outline-button:hover {{
  background-color: alpha(currentColor, .06);
}}

.hero-pill {{
  padding: 4px 9px;
  border-radius: 999px;
  border: 1px solid currentColor;
  background-color: alpha(currentColor, .06);
}}

.icon-chip {{
  min-width: 30px;
  min-height: 30px;
  border-radius: 9px;
  background-color: alpha(currentColor, .07);
}}

.brand-title {{
  font-size: 32px;
  font-weight: 900;
}}

.brand-logo {{
  margin-right: 18px;
}}

.hero-line {{
  font-size: 13px;
  color: alpha(currentColor, .73);
}}

.card-title {{
  font-size: 17px;
  font-weight: 800;
}}

.ring-value {{
  font-size: 16px;
}}

.ring-caption {{
  font-size: 12px;
}}

.label-dim {{
  color: alpha(currentColor, .67);
}}

.value {{
  font-weight: 700;
}}

.value-blue {{
  color: {BLUE};
}}

.value-blue-soft {{
  color: {BLUE_SOFT};
}}

.value-pink {{
  color: {PINK};
}}

.value-purple {{
  color: {PURPLE};
}}

.value-green {{
  color: {GREEN};
}}

.value-warn {{
  color: {WARN};
}}

.value-red {{
  color: {RED};
}}

.thin-separator {{
  background-color: alpha(currentColor, .08);
}}

.pending-badge {{
  min-width: 58px;
  min-height: 20px;
  padding: 1px 7px;
  border-radius: 999px;
  color: white;
  background-color: {RED};
  font-size: 13px;
  font-weight: 800;
}}

.outline-button {{
  min-height: 30px;
  padding: 4px 11px;
  border-radius: 9px;
  border: 1px solid alpha(currentColor, .12);
  background-color: alpha(currentColor, .025);
  font-weight: 700;
}}

.primary-button {{
  min-height: 30px;
  padding: 4px 13px;
  border-radius: 10px;
  color: @accent_fg_color;
  background-color: @accent_bg_color;
  font-weight: 800;
}}

.primary-button:hover {{
  background-color: shade(@accent_bg_color, 1.06);
}}
"""


def _icons_dir() -> str:
    app_dir = Path(__file__).resolve().parent
    return str(app_dir.parent / "icons")


def _add_css() -> None:
    provider = Gtk.CssProvider()
    try:
        provider.load_from_data(CSS)
    except TypeError:
        provider.load_from_data(CSS.encode())

    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        Gtk.IconTheme.get_for_display(display).add_search_path(_icons_dir())
    Gtk.Window.set_default_icon_name(APP_ICON_NAME)


def _label(
    text: str,
    *classes: str,
    xalign: float = 0.0,
    selectable: bool = False,
) -> Gtk.Label:
    label = Gtk.Label(label=text, xalign=xalign)
    label.set_selectable(selectable)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    for css_class in classes:
        if css_class:
            label.add_css_class(css_class)
    return label


def _markup(text: str, *classes: str, xalign: float = 0.0) -> Gtk.Label:
    label = Gtk.Label(xalign=xalign)
    label.set_markup(text)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    for css_class in classes:
        if css_class:
            label.add_css_class(css_class)
    return label


def _symbol(icon_name: str, size: int = 24, *classes: str) -> Gtk.Image:
    image = Gtk.Image.new_from_icon_name(icon_name)
    image.set_pixel_size(size)
    image.set_halign(Gtk.Align.CENTER)
    image.set_valign(Gtk.Align.CENTER)
    for css_class in classes:
        if css_class:
            image.add_css_class(css_class)
    return image


def _icon_chip(icon_name: str, color_class: str = "") -> Gtk.Box:
    chip = Gtk.Box()
    chip.add_css_class("icon-chip")
    chip.set_halign(Gtk.Align.START)
    chip.set_valign(Gtk.Align.CENTER)
    chip.set_size_request(30, 30)

    image = _symbol(icon_name, 20, color_class)
    image.set_hexpand(True)
    image.set_vexpand(True)
    chip.append(image)
    return chip


def _brand_icon(size: int, opacity: float = 1.0) -> Gtk.Image:
    image = Gtk.Image.new_from_icon_name(BRAND_ICON_NAME)
    image.set_pixel_size(size)
    image.set_opacity(opacity)
    image.add_css_class("brand-logo")
    return image


def _brand_title() -> Gtk.Box:
    title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    title.set_valign(Gtk.Align.CENTER)
    title.append(_label("Big", "brand-title"))
    title.append(
        _markup(
            f"<span foreground='{PINK}'>Com</span>"
            f"<span foreground='{PURPLE}'>mun</span>"
            f"<span foreground='{BLUE}'>ity</span>",
            "brand-title",
        )
    )
    return title


def _display_distribution_id(info: SystemInfo) -> str:
    if info.distrib.description and info.distrib.description != "Unknown Distribution":
        return info.distrib.description
    return info.distrib.id


def _friendly_date(value: str, include_time: bool = False) -> str:
    if value in ("", "Unknown"):
        return value or "Unknown"

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    parsed: datetime | None = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            break
        except ValueError:
            continue

    if parsed is None:
        return value

    months = ("jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez.")
    base = f"{parsed.day} de {months[parsed.month - 1]} de {parsed.year}"
    if include_time or " " in value:
        return f"{base} {parsed:%H:%M}"
    return base


def _pending_count(value: str) -> str:
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else "0"


def _pending_badge_count(value: str) -> str:
    count = _pending_count(value)
    try:
        return str(min(int(count), 99999))
    except ValueError:
        return count[:5]


def _pending_style(value: str) -> str:
    if value in ("None", "Unknown", "0 packages", ""):
        return "value-green"
    return "value-red"


def _card_header(title: str, icon_name: str, icon_class: str = "") -> Gtk.Box:
    header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    header.set_halign(Gtk.Align.START)
    header.set_hexpand(False)
    header.set_valign(Gtk.Align.CENTER)
    header.append(_icon_chip(icon_name, icon_class))

    title_label = _label(title, "card-title")
    title_label.set_halign(Gtk.Align.START)
    title_label.set_hexpand(False)
    header.append(title_label)
    return header


def _data_row(label: str, value: str | Gtk.Widget, style_class: str = "") -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
    row.set_hexpand(True)
    row.set_valign(Gtk.Align.CENTER)

    name = _label(label, "label-dim")
    name.set_width_chars(19)
    name.set_hexpand(False)
    row.append(name)

    if isinstance(value, Gtk.Widget):
        data = value
    else:
        data = _label(value, "value", style_class, selectable=True)
    data.set_hexpand(True)
    row.append(data)
    return row


def _rows(rows: list[tuple[str, str, str]]) -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    box.set_hexpand(True)

    for index, (label, value, style_class) in enumerate(rows):
        box.append(_data_row(label, value, style_class))
        if index < len(rows) - 1:
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.add_css_class("thin-separator")
            separator.set_margin_top(5)
            separator.set_margin_bottom(5)
            box.append(separator)
    return box


def _info_card(
    title: str,
    icon_name: str,
    rows: list[tuple[str, str, str]],
    icon_class: str = "",
) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    card.add_css_class("info-card")
    card.set_hexpand(True)
    card.set_vexpand(True)
    card.append(_card_header(title, icon_name, icon_class))
    card.append(_rows(rows))
    return card


def _hero_pill(text: str, icon_name: str, color_class: str) -> Gtk.Box:
    pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    pill.add_css_class("hero-pill")
    pill.add_css_class(color_class)
    pill.set_valign(Gtk.Align.CENTER)
    pill.append(_symbol(icon_name, 18, color_class))
    pill.append(_label(text, "value", color_class))
    return pill


def _hero() -> Gtk.Overlay:
    hero = Gtk.Overlay()
    hero.add_css_class("hero-card")
    hero.set_hexpand(True)

    content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
    content.set_hexpand(True)
    content.set_vexpand(True)
    content.set_valign(Gtk.Align.CENTER)
    content.append(_brand_icon(58))

    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    text.set_hexpand(True)
    text.set_valign(Gtk.Align.CENTER)
    text.append(_brand_title())
    text.append(_label("Uma distribuição Linux moderna, estável e amigável.", "hero-line"))
    text.append(
        _markup(
            "Baseada no <span foreground='#ff4fa3' weight='bold'>Manjaro Linux</span>, "
            "com foco em simplicidade, desempenho e liberdade.",
            "hero-line",
        )
    )

    pills = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    pills.set_margin_top(3)
    pills.append(_hero_pill("Open Source", "applications-system-symbolic", "value-blue"))
    pills.append(_hero_pill("Livre", "checkbox-checked-symbolic", "value-pink"))
    pills.append(_hero_pill("Comunitário", "system-users-symbolic", "value-purple"))
    text.append(pills)

    content.append(text)
    hero.set_child(content)

    return hero


def _hex_to_rgba(color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    color = color.lstrip("#")
    return (
        int(color[0:2], 16) / 255,
        int(color[2:4], 16) / 255,
        int(color[4:6], 16) / 255,
        alpha,
    )


def _ring(
    value: str,
    subtitle: str,
    fraction: float,
    color: str,
    value_class: str,
) -> Gtk.Overlay:
    area = Gtk.DrawingArea()
    area.set_content_width(146)
    area.set_content_height(146)

    def draw(_area, cr, width: int, height: int) -> None:
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10

        cr.set_line_width(6)
        cr.set_line_cap(1)
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.16)
        cr.arc(center_x, center_y, radius, 0, math.tau)
        cr.stroke()

        cr.set_source_rgba(*_hex_to_rgba(color))
        cr.arc(center_x, center_y, radius, -math.pi / 2, -math.pi / 2 + math.tau * fraction)
        cr.stroke()

    area.set_draw_func(draw)

    label = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    label.set_halign(Gtk.Align.CENTER)
    label.set_valign(Gtk.Align.CENTER)

    value_label = _label(value, "value", value_class, "ring-value", xalign=0.5)
    value_label.set_halign(Gtk.Align.CENTER)
    subtitle_label = _label(subtitle, "label-dim", "ring-caption", xalign=0.5)
    subtitle_label.set_halign(Gtk.Align.CENTER)
    label.append(value_label)
    label.append(subtitle_label)

    overlay = Gtk.Overlay()
    overlay.set_child(area)
    overlay.add_overlay(label)
    overlay.set_halign(Gtk.Align.CENTER)
    return overlay


def _metric(
    title: str,
    value: str,
    subtitle: str,
    fraction: float,
    color: str,
    value_class: str,
) -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.set_hexpand(True)
    box.set_halign(Gtk.Align.CENTER)
    box.append(_label(title, "label-dim", xalign=0.5))
    box.append(_ring(value, subtitle, fraction, color, value_class))
    return box


def _resources_card(info: SystemInfo) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    card.add_css_class("info-card")
    card.set_hexpand(True)
    card.set_vexpand(True)
    card.append(_card_header("Recursos", "utilities-system-monitor-symbolic"))

    body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
    body.set_hexpand(True)
    body.set_vexpand(True)
    body.set_valign(Gtk.Align.CENTER)
    body.append(_metric("Memória", info.memory, "Total", 0.78, PINK, "value-pink"))

    separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    separator.add_css_class("thin-separator")
    body.append(separator)

    body.append(_metric("Tempo de atividade", info.uptime, "Ativo", 0.88, GREEN, "value-green"))
    card.append(body)
    return card


def _system_card(info: SystemInfo) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    card.add_css_class("info-card")
    card.set_hexpand(True)
    card.set_vexpand(True)
    card.append(_card_header("Sistema", "computer-symbolic"))

    card.append(
        _rows(
            [
                (_("Processor"), info.cpu, ""),
                (_("Architecture"), info.architecture, "value-blue"),
                (_("Kernel"), info.kernel, "value-blue"),
                (_("Environment"), info.environment, "value-green"),
            ]
        )
    )
    return card


def _status_data_row(label: str, value: Gtk.Widget, action: Gtk.Widget | None = None) -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    row.set_valign(Gtk.Align.CENTER)
    row.set_hexpand(True)

    name = _label(label, "label-dim")
    name.set_width_chars(18)
    row.append(name)

    value.set_hexpand(True)
    row.append(value)

    if action is not None:
        row.append(action)
    return row


def _root_window(widget: Gtk.Widget) -> Gtk.Window | None:
    root = widget.get_root()
    if isinstance(root, Gtk.Window):
        return root
    return None


def _message_dialog(source: Gtk.Widget, heading: str, body: str) -> Adw.MessageDialog:
    dialog = Adw.MessageDialog.new(_root_window(source), heading, body)
    dialog.add_response("close", "Fechar")
    dialog.set_default_response("close")
    dialog.set_close_response("close")
    return dialog


def _show_repositories(source: Gtk.Widget, info: SystemInfo) -> None:
    dialog = _message_dialog(
        source,
        "Repositórios",
        f"Repositórios configurados: {info.repositories}",
    )
    pacman_conf = Path("/etc/pacman.conf")
    if pacman_conf.is_file():
        dialog.add_response("open", "Abrir pacman.conf")
        dialog.set_response_appearance("open", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect(
            "response",
            lambda _dialog, response: Gtk.show_uri(None, pacman_conf.as_uri(), 0)
            if response == "open"
            else None,
        )
    dialog.present()


def _open_updates(source: Gtk.Widget) -> None:
    pamac_manager = shutil.which("pamac-manager")
    if pamac_manager is None:
        dialog = _message_dialog(
            source,
            "Atualizações",
            "pamac-manager não foi encontrado no sistema.",
        )
        dialog.present()
        return

    try:
        subprocess.Popen(
            [pamac_manager, "--updates"],
            start_new_session=True,
        )
    except OSError as error:
        dialog = _message_dialog(
            source,
            "Atualizações",
            f"Não foi possível abrir o Pamac: {error}",
        )
        dialog.present()


def _button(label: str, css_class: str) -> Gtk.Button:
    button = Gtk.Button(label=label)
    button.add_css_class(css_class)
    return button


def _status_card(info: SystemInfo) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    card.add_css_class("info-card")
    card.set_hexpand(True)
    card.set_vexpand(True)
    card.append(_card_header("Status", "software-update-available-symbolic"))

    rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    status_rows: list[Gtk.Widget] = [
        _status_data_row(
            "Data de Instalação",
            _label(_friendly_date(info.install_date), "value"),
        ),
        _status_data_row(
            "Última Atualização",
            _label(_friendly_date(info.last_update, include_time=True), "value"),
        ),
    ]

    repo_value = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    repo_value.append(_symbol("network-workgroup-symbolic", 18, "value-blue"))
    repo_value.append(_label(info.repositories, "value", "value-blue", selectable=True))
    repo_button = _button("Repos", "outline-button")
    repo_button.set_tooltip_text("Ver repositórios configurados")
    repo_button.connect("clicked", lambda button: _show_repositories(button, info))
    status_rows.append(_status_data_row("Repositórios", repo_value, repo_button))

    pending = info.pending_updates
    pending_value = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    if _pending_style(pending) == "value-green":
        pending_value.append(_label(pending, "value", "value-green", selectable=True))
    else:
        badge = _label(_pending_badge_count(pending), "pending-badge", xalign=0.5)
        badge.set_width_chars(5)
        badge.set_max_width_chars(5)
        pending_value.append(badge)
    update_button = _button("Atualizar", "primary-button")
    update_button.set_tooltip_text("Abrir atualizações no Pamac")
    update_button.connect("clicked", lambda button: _open_updates(button))
    status_rows.append(
        _status_data_row(
            "Pendentes",
            pending_value,
            update_button,
        )
    )

    for index, row in enumerate(status_rows):
        rows.append(row)
        if index < len(status_rows) - 1:
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.add_css_class("thin-separator")
            separator.set_margin_top(5)
            separator.set_margin_bottom(5)
            rows.append(separator)

    card.append(rows)
    return card


def _open_uri(uri: str) -> None:
    Gtk.show_uri(None, uri, 0)


def _footer_link(title: str, subtitle: str, uri: str, icon_name: str, icon_class: str) -> Gtk.Button:
    button = Gtk.Button()
    button.add_css_class("footer-button")
    button.set_hexpand(True)
    button.connect("clicked", lambda _button, target=uri: _open_uri(target))

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    box.set_valign(Gtk.Align.CENTER)
    box.append(_symbol(icon_name, 30, icon_class))
    box.append(_label(title, "value"))

    separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    separator.add_css_class("thin-separator")
    box.append(separator)

    box.append(_label(subtitle, "value-blue-soft"))
    box.append(_symbol("window-new-symbolic", 18, "label-dim"))
    button.set_child(box)
    return button


def _footer() -> Gtk.Grid:
    footer = Gtk.Grid(column_spacing=12, row_spacing=8)
    footer.set_hexpand(True)
    footer.set_column_homogeneous(True)
    links = [
        _footer_link("Website", "communitybig.org", "https://communitybig.org", "network-workgroup-symbolic", "value-blue"),
        _footer_link("Suporte", "t.me/BigLinuxCommunity", "https://t.me/BigLinuxCommunity", "send-to-symbolic", "value-blue"),
        _footer_link("Doações", "t.me/DoacaoCommunityBot", "https://t.me/DoacaoCommunityBot", "emblem-favorite-symbolic", "value-pink"),
    ]
    for index, link in enumerate(links):
        footer.attach(link, index, 0, 1, 1)
    return footer


def _content(info: SystemInfo) -> Gtk.Widget:
    main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    main.add_css_class("main-view")
    main.set_hexpand(True)

    main.append(_hero())

    cards = Gtk.Grid(column_spacing=12, row_spacing=8)
    cards.set_hexpand(True)
    cards.set_column_homogeneous(True)

    cards.attach(
        _info_card(
            "Distribuição",
            "preferences-system-details-symbolic",
            [
                (_("Distributor ID"), _display_distribution_id(info), "value-blue"),
                (_("Description"), info.distrib.description, ""),
                (_("Release"), info.distrib.release, "value-purple"),
                (_("Codename"), info.distrib.codename, "value-purple"),
            ],
        ),
        0,
        0,
        1,
        1,
    )
    cards.attach(_system_card(info), 1, 0, 1, 1)
    cards.attach(_resources_card(info), 0, 1, 1, 1)
    cards.attach(_status_card(info), 1, 1, 1, 1)
    main.append(cards)
    main.append(_footer())

    clamp = Adw.Clamp()
    clamp.set_maximum_size(1240)
    clamp.set_tightening_threshold(860)
    clamp.set_child(main)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
    scrolled.set_child(clamp)
    return scrolled


class ReleaseWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app)
        self.set_title(f"{APP_TITLE} - {_('Distribution Information')}")
        self.set_icon_name(APP_ICON_NAME)
        self.set_default_size(1160, 760)
        self.set_size_request(820, 720)

        header = Adw.HeaderBar()
        menu_button = Gtk.Button.new_from_icon_name("open-menu-symbolic")
        menu_button.add_css_class("flat")
        header.pack_start(menu_button)
        header.set_title_widget(
            Adw.WindowTitle(
                title=APP_TITLE,
                subtitle=_("Distribution Information"),
            )
        )

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(_content(collect_all()))
        self.set_content(view)


class ReleaseApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        _add_css()

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = ReleaseWindow(self)
        window.present()


def main(argv: list[str] | None = None) -> int:
    app = ReleaseApplication()
    return app.run(argv or sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
