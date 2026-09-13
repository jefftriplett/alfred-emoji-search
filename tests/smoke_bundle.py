"""Exercise a staged bundle in a subprocess with isolated user history."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def smoke(bundle):
    with tempfile.TemporaryDirectory() as home:
        env = dict(
            os.environ,
            HOME=home,
            PYTHONPATH="",
            PYTHONDONTWRITEBYTECODE="1",
            emoji_python=sys.executable,
        )
        for query in (
            "",
            "version",
            ":fire:",
            "party popper",
            ":d",
            "no-such-emoji-zzzz",
        ):
            result = subprocess.run(
                ["/bin/bash", str(bundle / "launch.sh"), "--", query],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            items = json.loads(result.stdout)["items"]
            assert items, query
            if query in (":fire:", "party popper", ":d"):
                assert items[0].get("valid", True), query
                assert items[0]["arg"], query
        assert not (Path(home) / ".config").exists(), "Search must not write history"


if __name__ == "__main__":
    smoke(Path(sys.argv[1]).resolve())
