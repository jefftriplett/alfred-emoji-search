#!/usr/bin/env python3
"""
Emoji lookup Alfred workflow

uv run main.py "smile"

Searches emoji by shortcode and description.
Uses em-keyboard's emoji database for rich keyword search.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add bundled libraries to path (for Alfred workflow)
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))

from em._version import __version__ as EM_VERSION  # noqa: E402
from em.cli import do_find  # noqa: E402

VERSION = "2026.7.5"
GITHUB_URL = "https://github.com/jefftriplett/alfred-emoji-search"
HISTORY_DIR = Path.home() / ".config" / "alfred-emoji-search"
HISTORY_FILE = HISTORY_DIR / "history.json"
SEARCH_HISTORY_FILE = HISTORY_DIR / "search_history.json"


def _env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean Alfred workflow environment variable.

    Alfred passes checkbox settings as "1"/"0" (or "true"/"false").
    Defaults to ``default`` when the variable is unset so existing installs
    keep working before the settings are configured.
    """
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def normalize_query(query: str) -> str:
    """Accept wrapped shortcodes and space-separated names, preserving emoticons."""
    query = query.lower().strip()
    if len(query) > 2 and query.startswith(":") and query.endswith(":"):
        query = query[1:-1]
    return "_".join(query.split())


def parse_emojis() -> dict[str, list[str]]:
    # The installed/bundled package is a directory. Avoid importlib.resources'
    # archive-handling imports on every Script Filter invocation.
    import em

    return json.loads(Path(em.__file__).with_name("emojis.json").read_text("utf-8"))


def _load_counts(path: Path) -> dict[str, int]:
    try:
        data = json.loads(path.read_text("utf-8"))
    except (ValueError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: count
        for key, count in data.items()
        if key and type(count) is int and count > 0
    }


def _record_count(path: Path, key: str) -> None:
    """Serialize increments and replace atomically; history must not block use."""
    import fcntl
    import tempfile

    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            history = _load_counts(path)
            history[key] = history.get(key, 0) + 1
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False
            ) as output:
                temporary = Path(output.name)
                json.dump(history, output)
            os.replace(temporary, path)
            temporary = None
    except OSError as exc:
        print(f"Could not record history: {exc}", file=sys.stderr)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def load_search_history() -> dict[str, int]:
    return _load_counts(SEARCH_HISTORY_FILE)


def record_search(term: str) -> None:
    term = normalize_query(term)
    if term and _env_flag("log_search_history"):
        _record_count(SEARCH_HISTORY_FILE, term)


def load_history() -> dict[str, int]:
    return _load_counts(HISTORY_FILE)


def record_usage(emoji_char: str) -> None:
    if emoji_char:
        _record_count(HISTORY_FILE, emoji_char)


def get_frequent_emoji(limit: int = 20) -> list[tuple[str, str, str, int]]:
    """
    Get frequently used emoji sorted by usage count.
    Returns (emoji_char, shortcode, description, count) tuples.
    """
    history = load_history()
    if not history:
        return []

    lookup = parse_emojis()
    frequent = []

    for emoji_char, count in sorted(history.items(), key=lambda x: -x[1]):
        if emoji_char in lookup:
            keywords = lookup[emoji_char]
            shortcode = f":{keywords[0]}:"
            description = keywords[0].replace("_", " ")
            frequent.append((emoji_char, shortcode, description, count))

    return frequent[:limit]


def search_emoji(query: str) -> list[tuple[str, str, str, int]]:
    """
    Search emoji by shortcode or keywords using em-keyboard's do_find.
    Returns matching (emoji_char, shortcode, description, usage_count) tuples.
    """
    query = normalize_query(query)
    if not query:
        return []

    history = load_history()
    lookup = parse_emojis()

    # Search history weighting (opt-out via workflow setting)
    weight_by_search = _env_flag("weight_by_search_history")
    search_history = load_search_history() if weight_by_search else {}

    # Use em-keyboard's built-in search
    results = do_find(lookup, (query,))

    matches = []
    for name, emoji_char in results:
        shortcode = f":{name}:"
        description = name.replace("_", " ")
        count = history.get(emoji_char, 0)
        # Sum search counts of this emoji's keywords. Only whole-keyword
        # matches count, so partial keystrokes logged mid-typing don't skew.
        search_score = (
            sum(search_history.get(kw, 0) for kw in lookup.get(emoji_char, []))
            if search_history
            else 0
        )
        matches.append((emoji_char, shortcode, description, count, search_score))

    # Re-sort to boost frequently used and previously searched emoji
    def sort_key(item):
        _, shortcode, _, count, search_score = item
        shortcode_lower = shortcode.lower()
        if query == shortcode_lower.strip(":"):
            priority = 0
        elif shortcode_lower.strip(":").startswith(query):
            priority = 1
        else:
            priority = 2
        return (priority, -(count + search_score), len(shortcode))

    matches.sort(key=sort_key)

    return [(e, s, d, c) for e, s, d, c, _ in matches[:50]]


def format_item(
    emoji_char: str, shortcode: str, description: str, count: int = 0, query: str = ""
) -> dict:
    """Format an emoji as an Alfred result item."""
    subtitle = f"{shortcode} - {description}"
    if count > 0:
        subtitle = f"{subtitle} (used {count}x)"

    return {
        "arg": emoji_char,
        "variables": {
            "result_action": "copy",
            "selected_emoji": emoji_char,
            "search_term": normalize_query(query),
        },
        "subtitle": subtitle,
        "title": f"{emoji_char}  {shortcode.strip(':')}",
        "mods": {
            "alt": {
                "arg": shortcode,
                "subtitle": f"Copy shortcode: {shortcode}",
                "valid": True,
            },
            "cmd": {
                "arg": shortcode.strip(":"),
                "subtitle": f"Copy without colons: {shortcode.strip(':')}",
                "valid": True,
            },
        },
    }


def get_version_info() -> dict:
    """Return Alfred items showing version and GitHub info."""
    return {
        "items": [
            {
                "title": f"✨ Emoji Search v{VERSION}",
                "subtitle": f"Powered by em-keyboard v{EM_VERSION}",
                "arg": VERSION,
                "variables": {
                    "result_action": "copy",
                    "selected_emoji": "",
                    "search_term": "",
                },
                "valid": True,
            },
            {
                "title": "📦 View on GitHub",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": GITHUB_URL,
                "variables": {
                    "result_action": "copy",
                    "selected_emoji": "",
                    "search_term": "",
                },
                "mods": {
                    "cmd": {
                        "variables": {
                            "result_action": "open",
                            "selected_emoji": "",
                            "search_term": "",
                        }
                    }
                },
                "valid": True,
            },
            {
                "title": "🐛 Report an Issue",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": f"{GITHUB_URL}/issues",
                "variables": {
                    "result_action": "copy",
                    "selected_emoji": "",
                    "search_term": "",
                },
                "mods": {
                    "cmd": {
                        "variables": {
                            "result_action": "open",
                            "selected_emoji": "",
                            "search_term": "",
                        }
                    }
                },
                "valid": True,
            },
            {
                "title": "📥 Check for Updates",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": f"{GITHUB_URL}/releases",
                "variables": {
                    "result_action": "copy",
                    "selected_emoji": "",
                    "search_term": "",
                },
                "mods": {
                    "cmd": {
                        "variables": {
                            "result_action": "open",
                            "selected_emoji": "",
                            "search_term": "",
                        }
                    }
                },
                "valid": True,
            },
        ]
    }


def main(
    query: str = "",
    indent: int | None = None,
    record: str | None = None,
    record_term: str = "",
):
    """
    Search for emoji by shortcode or description.
    """
    if record is not None:
        record_usage(record)
        if record:
            record_search(record_term)
        return

    query = query.strip()

    # Handle special commands
    if query.lower() in ("version", "about", "info", "help"):
        result = get_version_info()
        print(json.dumps(result, indent=indent))
        return

    if not query:
        frequent = get_frequent_emoji()
        if frequent:
            result = {
                "items": [
                    format_item(emoji_char, shortcode, description, count)
                    for emoji_char, shortcode, description, count in frequent
                ]
            }
        else:
            result = {
                "items": [
                    {
                        "arg": "",
                        "subtitle": "Start typing to search emoji",
                        "title": "Search emoji by name or keyword",
                        "valid": False,
                    }
                ]
            }
    else:
        matches = search_emoji(query)
        if not matches:
            result = {
                "items": [
                    {
                        "arg": "",
                        "subtitle": "No emoji found",
                        "title": f"No results for '{query}'",
                        "valid": False,
                    }
                ]
            }
        else:
            result = {
                "items": [
                    format_item(emoji_char, shortcode, description, count, query)
                    for emoji_char, shortcode, description, count in matches
                ]
            }

    print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search emoji by shortcode or description"
    )
    parser.add_argument("query", nargs="?", default="", help="Search query")
    parser.add_argument("--indent", type=int, default=None, help="JSON indent level")
    parser.add_argument("--record", type=str, default=None, help="Record emoji usage")
    parser.add_argument(
        "--record-term", default="", help="Record an accepted search term"
    )
    args = parser.parse_args()
    main(args.query, args.indent, args.record, args.record_term)
