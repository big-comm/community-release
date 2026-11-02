# Terminal dashboard decisions

## Entry points and startup

The default command prints a snapshot and returns to the shell. Full-screen
interaction is explicit (`--tui`) so shell startup and existing scripts keep
working. Rich is already required by the package. Textual is an optional
dependency imported only by the interactive entry point.

Short identity queries read release files without querying hardware, packages
or the network and without importing either presentation framework. Identity is
drawn before the default snapshot starts its slower local probes. The TUI runs
those probes in a cancellable worker so refresh and shutdown remain responsive.

## Identity and layout

The owl is generated ahead of time from the current distribution SVG, as in
bigcommunity-fastfetch. The terminal only reads a small ANSI asset; neither
fastfetch nor an SVG renderer is a runtime dependency. The face remains the
terminal background. Plain output respects redirection and `NO_COLOR`.

Four cards follow the existing GTK information window: distribution, system,
resources and status. The snapshot and TUI share their Rich renderables. Wide
terminals use two columns; narrow terminals stack cards; the TUI scrolls on
short terminals. Ellipsized hardware names can be read with `comm-release -e`.

## Updates and release identity

`checkupdates` refreshes repository state and can delay startup. The dashboard
uses `pacman -Qu` against the existing database, with a bounded timeout. It
explicitly labels counts as local. A failure is unknown, never zero updates.
No startup path synchronizes repositories or installs packages.

The information tool version and the distribution version are separate.
Releasing tool 2.1.0 does not change `/etc/lsb-release` or the 1.7.0 codename.

## Development and packaging

The workflow follows Big AI Agents: English source text, gettext catalogs,
checkout previews, `make check`, and `make pkg` from a committed tree with a
real source checksum. The existing BigCommunity PKGBUILD remains the production
recipe; the local builder changes only its source transport. It does not
install packages or publish anything.

Catalog updates preserve existing translations without guessing similar
messages. New untranslated entries use the English source until reviewed.
Portuguese has explicit translations for the new dashboard text. CI exercises
the TUI with no browser actions or package installations by the tests.
