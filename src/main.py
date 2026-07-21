#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "em-keyboard",
# ]
# ///
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
from em.cli import do_find, parse_emojis  # noqa: E402

VERSION = "2026.7.4"
GITHUB_URL = "https://github.com/jefftriplett/alfred-emoji-search"
HISTORY_DIR = Path.home() / ".config" / "alfred-emoji-search"
HISTORY_FILE = HISTORY_DIR / "history.json"
SEARCH_HISTORY_FILE = HISTORY_DIR / "search_history.json"


def _env_flag(name: str, default: bool = True) -> bool:
    """
    Read a boolean setting from the environment (set via Alfred's workflow
    configuration). Unset/empty falls back to ``default`` so existing installs
    keep working before the settings are configured.
    """
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def log_search_enabled() -> bool:
    """Whether search terms should be recorded to disk."""
    return _env_flag("log_search_history", True)


def weight_by_search_enabled() -> bool:
    """Whether search history should influence result ordering."""
    return _env_flag("weight_by_search_history", True)


def load_history() -> dict[str, int]:
    """Load emoji usage history from disk."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_history(history: dict[str, int]) -> None:
    """Save emoji usage history to disk."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history))


def record_usage(emoji_char: str) -> None:
    """Record that an emoji was used."""
    history = load_history()
    history[emoji_char] = history.get(emoji_char, 0) + 1
    save_history(history)


def load_search_history() -> dict[str, int]:
    """Load search-term history (term -> times searched) from disk."""
    if SEARCH_HISTORY_FILE.exists():
        try:
            return json.loads(SEARCH_HISTORY_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_search_history(history: dict[str, int]) -> None:
    """Save search-term history to disk."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    SEARCH_HISTORY_FILE.write_text(json.dumps(history))


def record_search(query: str) -> None:
    """Record that a search term was used (respects the logging setting)."""
    if not log_search_enabled():
        return
    query = query.lower().strip()
    if not query:
        return
    history = load_search_history()
    history[query] = history.get(query, 0) + 1
    save_search_history(history)


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
    query = query.lower().strip()
    if not query:
        return []

    history = load_history()
    lookup = parse_emojis()
    search_history = load_search_history() if weight_by_search_enabled() else {}

    # Use em-keyboard's built-in search
    results = do_find(lookup, (query,))

    scored = []
    for name, emoji_char in results:
        shortcode = f":{name}:"
        description = name.replace("_", " ")
        count = history.get(emoji_char, 0)
        # Boost emoji whose keywords match terms we've searched before. Matching
        # whole keywords means partial keystrokes ("he", "hea") logged while
        # typing don't skew results — only completed terms line up.
        search_score = sum(
            search_history.get(keyword.lower(), 0)
            for keyword in lookup.get(emoji_char, ())
        )
        scored.append((emoji_char, shortcode, description, count, search_score))

    # Re-sort to boost frequently used and frequently searched emoji
    def sort_key(item):
        _, shortcode, _, count, search_score = item
        term = shortcode.lower().strip(":")
        if query == term:
            priority = 0
        elif term.startswith(query):
            priority = 1
        else:
            priority = 2
        return (priority, -(count + search_score), len(shortcode))

    scored.sort(key=sort_key)

    return [(e, s, d, c) for e, s, d, c, _ in scored[:50]]


def format_item(
    emoji_char: str, shortcode: str, description: str, count: int = 0
) -> dict:
    """Format an emoji as an Alfred result item."""
    subtitle = f"{shortcode} - {description}"
    if count > 0:
        subtitle = f"{subtitle} (used {count}x)"

    return {
        "arg": emoji_char,
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
                "valid": True,
            },
            {
                "title": "📦 View on GitHub",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": GITHUB_URL,
                "valid": True,
            },
            {
                "title": "🐛 Report an Issue",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": f"{GITHUB_URL}/issues",
                "valid": True,
            },
            {
                "title": "📥 Check for Updates",
                "subtitle": "⏎ Copy URL  ·  ⌘⏎ Open in browser",
                "arg": f"{GITHUB_URL}/releases",
                "valid": True,
            },
        ]
    }


def main(query: str = "", indent: int | None = None, record: str | None = None):
    """
    Search for emoji by shortcode or description.
    """
    if record:
        record_usage(record)
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
        record_search(query)
        matches = search_emoji(query)
        if not matches:
            result = {
                "items": [
                    {
                        "arg": "",
                        "subtitle": "No emoji found",
                        "title": f"No results for '{query}'",
                    }
                ]
            }
        else:
            result = {
                "items": [
                    format_item(emoji_char, shortcode, description, count)
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
    args = parser.parse_args()
    main(args.query, args.indent, args.record)
