import contextlib
import importlib.util
import io
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("emoji_main", ROOT / "src/main.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        for name, value in (
            ("HISTORY_DIR", self.directory),
            ("HISTORY_FILE", self.directory / "history.json"),
            ("SEARCH_HISTORY_FILE", self.directory / "search_history.json"),
        ):
            patcher = patch.object(m, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.dict(
            os.environ, log_search_history="1", weight_by_search_history="1"
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def output(self, query):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            m.main(query)
        return json.loads(output.getvalue())["items"]

    def test_normalized_searches_and_emoticons(self):
        for query, expected in (
            (":fire:", ":fire:"),
            ("Party   Popper", ":party_popper:"),
            ("red heart", ":red_heart:"),
        ):
            self.assertEqual(m.search_emoji(query)[0][1], expected)
        self.assertTrue(m.search_emoji(":d"))
        self.assertEqual(m.normalize_query(":d"), ":d")
        self.assertLessEqual(len(m.search_emoji("a")), 50)

    def test_search_is_read_only_and_selection_records(self):
        item = self.output("Party Popper")[0]
        self.assertFalse(m.SEARCH_HISTORY_FILE.exists())
        variables = item["variables"]
        m.main(record=variables["selected_emoji"], record_term=variables["search_term"])
        self.assertEqual(m.load_search_history(), {"party_popper": 1})
        self.assertEqual(m.load_history(), {item["arg"]: 1})
        self.assertEqual(self.output("")[0]["arg"], item["arg"])
        with patch.dict(os.environ, log_search_history="0"):
            m.record_search("fire")
        self.assertNotIn("fire", m.load_search_history())

    def test_invalid_history(self):
        for data in (b"[]", b"null", b"{", b"\xff", b'{"fire":"bad","x":true,"y":-1}'):
            for path in (m.HISTORY_FILE, m.SEARCH_HISTORY_FILE):
                path.write_bytes(data)
            self.assertTrue(m.search_emoji("fire"))
            m.record_usage("🔥")
            self.assertEqual(m.load_history(), {"🔥": 1})

    def test_write_failure_preserves_history(self):
        m.record_usage("🔥")
        with (
            patch.object(m.os, "replace", side_effect=OSError("failed")),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            m.record_usage("🔥")
        self.assertEqual(m.load_history(), {"🔥": 1})
        self.assertEqual(
            {p.name for p in self.directory.iterdir()}, {"history.json", "history.lock"}
        )

    def test_concurrent_increments(self):
        code = f"import runpy; m=runpy.run_path({str(ROOT / 'src/main.py')!r}); [m['record_usage']('🔥') for _ in range(20)]"
        env = dict(os.environ, HOME=str(self.directory))
        processes = [
            subprocess.Popen([sys.executable, "-c", code], env=env) for _ in range(4)
        ]
        for process in processes:
            self.assertEqual(process.wait(timeout=30), 0)
        path = self.directory / ".config/alfred-emoji-search/history.json"
        self.assertEqual(json.loads(path.read_text()), {"🔥": 80})

    def test_result_routing(self):
        item = self.output("fire")[0]
        self.assertEqual(item["variables"]["result_action"], "copy")
        self.assertEqual(item["mods"]["cmd"]["arg"], "fire")
        self.assertEqual(item["mods"]["alt"]["arg"], ":fire:")
        for link in m.get_version_info()["items"][1:]:
            self.assertEqual(link["variables"]["result_action"], "copy")
            self.assertEqual(link["mods"]["cmd"]["variables"]["result_action"], "open")
        self.assertFalse(self.output("no-such-emoji-zzzz")[0]["valid"])
        workflow = plistlib.loads((ROOT / "info.plist").read_bytes())
        objects = {obj["uid"]: obj for obj in workflow["objects"]}
        self.assertEqual(objects["copy-filter"]["config"]["matchstring"], "^copy$")
        self.assertEqual(objects["url-filter"]["config"]["matchstring"], "^open$")
        self.assertEqual(
            {e["destinationuid"] for e in workflow["connections"]["script-filter"]},
            {"copy-filter", "url-filter"},
        )

    def test_history_weighting_toggle(self):
        baseline = m.search_emoji("face")
        target = baseline[-1][0]
        keyword = m.parse_emojis()[target][0]
        m.SEARCH_HISTORY_FILE.write_text(json.dumps({keyword: 1000}))
        self.assertNotEqual(m.search_emoji("face"), baseline)
        with patch.dict(os.environ, weight_by_search_history="0"):
            self.assertEqual(m.search_emoji("face"), baseline)
