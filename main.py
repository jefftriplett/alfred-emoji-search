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
import sys
from pathlib import Path

# Add bundled libraries to path (for Alfred workflow)
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))

from em.cli import do_find, parse_emojis  # noqa: E402

VERSION = "2026.7.2"
GITHUB_URL = "https://github.com/jefftriplett/alfred-emoji-search"
HISTORY_DIR = Path.home() / ".config" / "alfred-emoji-search"
HISTORY_FILE = HISTORY_DIR / "history.json"


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

    # Use em-keyboard's built-in search
    results = do_find(lookup, (query,))

    matches = []
    for name, emoji_char in results:
        shortcode = f":{name}:"
        description = name.replace("_", " ")
        count = history.get(emoji_char, 0)
        matches.append((emoji_char, shortcode, description, count))

    # Re-sort to boost frequently used emoji
    def sort_key(item):
        emoji_char, shortcode, _, count = item
        shortcode_lower = shortcode.lower()
        if query == shortcode_lower.strip(":"):
            priority = 0
        elif shortcode_lower.strip(":").startswith(query):
            priority = 1
        else:
            priority = 2
        return (priority, -count, len(shortcode))

    matches.sort(key=sort_key)

    return matches[:50]


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
                "subtitle": "Press Enter to copy version",
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
