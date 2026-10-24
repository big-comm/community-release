"""Regression checks for startup, CLI compatibility and honest update status."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
import gettext
import os
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "usr/share/comm-release"))

import info
import main


class LauncherTests(unittest.TestCase):
    def test_checkout_launchers_use_checkout_sources(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            python = Path(folder) / "python3"
            python.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            python.chmod(0o755)
            for command, module in (("comm-release", "main.py"),
                                    ("comm-release-gtk", "gui.py")):
                with self.subTest(command=command):
                    result = subprocess.run(
                        [str(root / "usr/bin" / command), "--help"],
                        capture_output=True, text=True, check=True,
                        env={**os.environ, "PATH": folder + os.pathsep + os.environ["PATH"]},
                    )
                    target, argument = result.stdout.splitlines()
                    self.assertEqual(Path(target).resolve(), root / "usr/share/comm-release" / module)
                    self.assertEqual(argument, "--help")


class IdentityTests(unittest.TestCase):
    def test_short_options_never_load_ui_or_collect_system_data(self):
        identity = info.DistribInfo("Example", "1.2.3", "Test", "Example Linux")
        for args, expected in ((["-rs"], "1.2.3\n"),
                               (["-r", "-s"], "1.2.3\n"),
                               (["-s"], "1.2.3\n"),
                               (["-as"], 'Example "Example Linux" 1.2.3 Test\n')):
            with self.subTest(args=args), patch.object(sys, "argv", ["comm-release", *args]), \
                 patch.object(main, "collect_distrib", return_value=identity), \
                 patch.object(main, "collect_all", side_effect=AssertionError("slow path")), \
                 patch.dict(sys.modules, {"rich": None, "textual": None}), \
                 redirect_stdout(StringIO()) as output:
                main.main()
                self.assertEqual(output.getvalue(), expected)

    def test_tui_rejects_redirected_output(self):
        with patch.object(sys, "argv", ["comm-release", "--tui"]), \
             patch.object(sys.stdin, "isatty", return_value=False), \
             redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
            main.main()
        self.assertEqual(error.exception.code, 1)


class UpdateTests(unittest.TestCase):
    def query(self, code, stdout="", stderr=""):
        result = subprocess.CompletedProcess(["pacman", "-Qu"], code, stdout, stderr)
        with patch.object(info.shutil, "which", return_value="/usr/bin/pacman"), \
             patch.object(info.subprocess, "run", return_value=result) as run:
            value = info.collect_pending_updates()
        self.assertEqual(run.call_args.args[0], ["pacman", "-Qu"])
        self.assertLessEqual(run.call_args.kwargs["timeout"], 1)
        return value

    def test_local_query_counts_updates_and_never_invokes_checkupdates(self):
        self.assertEqual(self.query(0, "a 1 -> 2\nb 2 -> 3\n"), "2 packages")

    def test_no_updates(self):
        self.assertEqual(self.query(1), "None")

    def test_failures_do_not_masquerade_as_zero_updates(self):
        self.assertEqual(self.query(1, stderr="error: unable to read database"), "Unknown")
        self.assertEqual(self.query(2), "Unknown")
        with patch.object(info.shutil, "which", return_value="/usr/bin/pacman"), \
             patch.object(info.subprocess, "run", side_effect=subprocess.TimeoutExpired("pacman", 1)):
            self.assertEqual(info.collect_pending_updates(), "Unknown")


class RenderTests(unittest.TestCase):
    def test_identity_is_visible_before_potentially_slow_package_probes(self):
        from rich.console import Console
        import dashboard

        output = StringIO()
        console = Console(width=100, height=40, file=output, color_system=None)

        def collect():
            self.assertIn("BigCommunity", output.getvalue())
            return info.SystemInfo()

        with patch.object(dashboard, "Console", return_value=console), \
             patch.object(dashboard, "collect_all", side_effect=collect):
            dashboard.display_dashboard()

    def test_hero_shows_every_row_of_the_owl_uncut(self):
        from rich.console import Console
        from dashboard import hero, owl

        output = StringIO()
        Console(width=100, file=output, color_system=None).print(
            hero(info.SystemInfo(), 100))
        text = output.getvalue()
        for line in owl().plain.splitlines():
            with self.subTest(line=line):
                self.assertIn(line.rstrip(), text)

    def test_narrow_and_wide_terminals_keep_content_within_bounds(self):
        from rich.console import Console
        from dashboard import dashboard, owl

        self.assertIn("⣿", owl().plain)
        for width in (32, 48, 60, 76, 80, 100, 120):
            with self.subTest(width=width):
                output = StringIO()
                console = Console(width=width, height=60, file=output, color_system=None)
                console.print(dashboard(info.SystemInfo(), width))
                text = output.getvalue()
                self.assertLessEqual(max(map(len, text.splitlines())), width)
                self.assertIn("BigCommunity", text)
                self.assertNotIn("\x1b", text)


class TranslationTests(unittest.TestCase):
    def test_brazilian_portuguese_catalog_contains_the_new_interface(self):
        locale_dir = Path(__file__).resolve().parents[1] / "usr/share/locale"
        translate = gettext.translation("comm-release", locale_dir, languages=["pt_BR"]).gettext
        self.assertEqual(translate("Resources"), "Recursos")
        self.assertEqual(translate("Open the interactive dashboard"), "Abrir o painel interativo")
        self.assertEqual(translate("Updates (local)"), "Pendentes (local)")
        self.assertEqual(translate("Bare Metal"), "Máquina física")

    def test_empty_catalog_uses_english_source_without_an_error(self):
        translate = gettext.translation("comm-release", languages=["zz"], fallback=True).gettext
        self.assertEqual(translate("Resources"), "Resources")


if __name__ == "__main__":
    unittest.main()
