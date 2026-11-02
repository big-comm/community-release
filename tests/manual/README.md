# Installed-package checks

Use a disposable BigCommunity session or test VM. Automated checks do not
install packages, refresh repositories, open browsers or start the GTK window.

1. Run `make check`, commit the reviewed tree, then run `make pkg`. Check the
   generated `SOURCE-REVISION` against the commit intended for testing.
2. Inspect the package with `pacman -Qip` and `pacman -Qlp`. Confirm it contains
   both launchers, the three new dashboard assets/modules, icons, catalogs,
   license, desktop file and `/etc/comm-release`. No `__pycache__` should appear.
3. Install the test package through pacman in the test environment. Check
   `comm-release`, `comm-release -rs`, `comm-release -as`, `--help` and `-p`.
   The tool reports 2.1.0; release and codename still come from the system.
4. With python-textual installed, run `comm-release --tui`. Resize to 120 × 40,
   80 × 24 and 48 × 24; scroll; press `r`; exit with both `q` and Escape.
   Pressing `o`, `s` or `d` should open only its respective community link.
5. On a test system without python-textual, the snapshot and short queries must
   work. `--tui` must explain the missing optional dependency without a traceback.
6. Pipe short queries to a file and check there are no ANSI sequences. Check
   `NO_COLOR=1 comm-release` and a Portuguese UTF-8 session as well.
7. Disconnect the network and repeat the snapshot/TUI. Update counts must remain
   explicitly local; a broken package database should be unavailable, not green
   with zero updates. No startup should synchronize repositories.
8. Open `comm-release-gtk` and its desktop entry. Confirm the existing GTK layout,
   icons and Pamac button still work. Pending updates must be labeled local.

Do not change the host's system identity to test the tool. Keep the previous
distribution package available for rollback through pacman in the test VM.
