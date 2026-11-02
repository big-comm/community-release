"""Exercise the actual Textual lifecycle, resize, keyboard and refresh."""

import asyncio
from importlib.util import find_spec
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "usr/share/comm-release"))


@unittest.skipUnless(find_spec("textual"), "optional python-textual is not installed")
class TuiTests(unittest.IsolatedAsyncioTestCase):
    async def test_mount_refresh_resize_links_and_quit(self):
        from info import DistribInfo, SystemInfo
        from tui import ReleaseApp

        first = SystemInfo(distrib=DistribInfo(release="1.0"))
        second = SystemInfo(distrib=DistribInfo(release="2.0"))
        with patch("tui.collect_all", side_effect=[first, second]) as collect:
            app = ReleaseApp()
            with patch.object(app, "open_url") as open_url:
                async with app.run_test(size=(120, 40)) as pilot:
                    await app.workers.wait_for_complete()
                    self.assertEqual(app.info.distrib.release, "1.0")
                    await pilot.resize_terminal(48, 24)
                    await pilot.press("r")
                    await app.workers.wait_for_complete()
                    self.assertEqual(app.info.distrib.release, "2.0")
                    await pilot.press("o", "s", "d")
                    self.assertEqual(open_url.call_count, 3)
                    await pilot.press("q")
            self.assertEqual(collect.call_count, 2)

    async def test_slow_collection_does_not_block_quit(self):
        import time
        from info import SystemInfo
        from tui import ReleaseApp

        def slow():
            time.sleep(.2)
            return SystemInfo()

        with patch("tui.collect_all", side_effect=slow):
            app = ReleaseApp()
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.press("q")
            self.assertIsNone(app._exception)


if __name__ == "__main__":
    unittest.main()
