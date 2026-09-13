"""Run the real shell launcher against controlled interpreter installations."""

import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="emoji launcher ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copy(ROOT / "src/launch.sh", self.root / "launch.sh")
        (self.root / "main.py").write_text(
            "import json, sys; print(json.dumps(sys.argv[1:]))"
        )

    def launch(self, override, *args):
        env = dict(os.environ, emoji_python=override)
        return subprocess.run(
            ["/bin/bash", str(self.root / "launch.sh"), *args],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_supported_python_and_argument_preservation(self):
        args = ("--record", "🔥", "--record-term=party popper", '"$HOME`echo nope`')
        result = self.launch(sys.executable, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), list(args))

    def test_missing_override_displays_setup_message(self):
        result = self.launch(str(self.root / "missing-python"), "fire")
        self.assertEqual(result.returncode, 1)
        item = json.loads(result.stdout)["items"][0]
        self.assertFalse(item["valid"])
        self.assertIn("3.12", item["title"])

    def test_old_python_is_rejected_before_running_main(self):
        candidate = self.root / "old-python"
        candidate.write_text("#!/bin/bash\nexit 1\n")
        candidate.chmod(0o755)
        result = self.launch(str(candidate), "fire")
        self.assertEqual(result.returncode, 1)
        self.assertIn("items", json.loads(result.stdout))

    @unittest.skipUnless(Path("/usr/bin/python3").exists(), "No system Python")
    def test_actual_system_python(self):
        result = self.launch("/usr/bin/python3", "fire")
        version = subprocess.check_output(
            [
                "/usr/bin/python3",
                "-c",
                "import sys; print(sys.version_info >= (3, 12))",
            ],
            text=True,
        ).strip()
        if version == "True":
            self.assertEqual(json.loads(result.stdout), ["fire"])
        else:
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["items"][0]["valid"])
            self.assertNotIn("Traceback", result.stderr)

    def test_python_on_path(self):
        (self.root / "python3").symlink_to(sys.executable)
        with patch.dict(os.environ, PATH=f"{self.root}:/usr/bin:/bin"):
            result = self.launch("", "fire")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["fire"])

    def test_both_workflow_actions_use_launcher(self):
        data = plistlib.loads((ROOT / "info.plist").read_bytes())
        for obj in data["objects"]:
            if obj["uid"] in ("script-filter", "record-usage"):
                self.assertTrue(
                    obj["config"]["script"].startswith("/bin/bash ./launch.sh")
                )
