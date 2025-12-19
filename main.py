#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "emoji",
# ]
# ///
"""
Emoji lookup Alfred workflow

uv run main.py "smile"

Searches emoji by shortcode and description.
"""

import argparse
import json
import os
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# Add bundled libraries to path (for Alfred workflow)
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))

import emoji  # noqa: E402

# History storage location
BUNDLE_ID = "com.jefftriplett.alfred-emoji-search"


def get_history_path() -> Path:
    """Get the path to the history file."""
    # Check for Alfred's workflow data directory first
    alfred_data = os.environ.get("alfred_workflow_data")
    if alfred_data:
        data_dir = Path(alfred_data)
    else:
        # Fallback to user's home directory
        data_dir = Path.home() / ".alfred-emoji-search"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.json"


def load_history() -> dict[str, dict]:
    """
    Load emoji usage history from file.
    Returns dict mapping emoji char to {count, last_used, shortcode}.
    """
    history_path = get_history_path()
    if not history_path.exists():
        return {}

    try:
        with history_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_history(history: dict[str, dict]) -> None:
    """Save emoji usage history to file."""
    history_path = get_history_path()
    try:
        with history_path.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # Silently fail if we can't write


def record_usage(emoji_char: str, shortcode: str = "") -> None:
    """Record that an emoji was used."""
    history = load_history()

    if emoji_char in history:
        history[emoji_char]["count"] += 1
        history[emoji_char]["last_used"] = datetime.now().isoformat()
        if shortcode:
            history[emoji_char]["shortcode"] = shortcode
    else:
        history[emoji_char] = {
            "count": 1,
            "last_used": datetime.now().isoformat(),
            "shortcode": shortcode,
        }

    save_history(history)


def get_frequently_used(limit: int = 50) -> list[tuple[str, str, str, int]]:
    """
    Get frequently used emoji, sorted by usage count and recency.
    Returns list of (emoji_char, shortcode, description, count) tuples.
    """
    history = load_history()
    if not history:
        return []

    # Get all emoji data to look up descriptions
    all_emoji = {e[0]: (e[1], e[2]) for e in get_emoji_data()}

    results = []
    for emoji_char, data in history.items():
        if emoji_char in all_emoji:
            shortcode, description = all_emoji[emoji_char]
            results.append((emoji_char, shortcode, description, data["count"]))
        elif data.get("shortcode"):
            # Emoji might have been removed from library, use stored shortcode
            try:
                description = unicodedata.name(emoji_char, "").lower()
            except (TypeError, ValueError):
                description = data["shortcode"].strip(":").replace("_", " ")
            results.append((emoji_char, data["shortcode"], description, data["count"]))

    # Sort by count (descending), then by last_used (descending)
    def sort_key(item):
        emoji_char = item[0]
        count = item[3]
        last_used = history[emoji_char].get("last_used", "")
        return (-count, -len(last_used) if last_used else 0, last_used)

    results.sort(key=lambda x: (-x[3], -len(history[x[0]].get("last_used", ""))))

    return results[:limit]


def get_emoji_data() -> list[tuple[str, str, str]]:
    """
    Returns a list of (emoji_char, shortcode, description) tuples.
    """
    results = []

    for emoji_char, data in emoji.EMOJI_DATA.items():
        # Get the shortcode (e.g., :smile:)
        shortcode = data.get("en", "")
        if shortcode:
            # Clean up the shortcode format
            shortcode_clean = shortcode.replace("_", " ").strip(":")

            # Get unicode name as description
            try:
                description = unicodedata.name(emoji_char, "").lower()
            except (TypeError, ValueError):
                description = shortcode_clean

            results.append((emoji_char, shortcode, description))

    return results


def search_emoji(query: str) -> list[tuple[str, str, str]]:
    """
    Search emoji by shortcode or description.
    Returns matching (emoji_char, shortcode, description) tuples.
    Frequently used emoji are boosted in the results.
    """
    query = query.lower().strip()
    if not query:
        return []

    all_emoji = get_emoji_data()
    matches = []

    # Load history for boosting frequently used emoji
    history = load_history()

    for emoji_char, shortcode, description in all_emoji:
        shortcode_lower = shortcode.lower()
        description_lower = description.lower()

        # Check if query matches shortcode or description
        if query in shortcode_lower or query in description_lower:
            matches.append((emoji_char, shortcode, description))

    # Sort by relevance: exact match first, then usage frequency, then shortcode length
    def sort_key(item):
        emoji_char, shortcode, _ = item
        shortcode_lower = shortcode.lower()

        # Get usage count (higher = more frequently used)
        usage_count = history.get(emoji_char, {}).get("count", 0)
        # Invert for sorting (we want higher counts first)
        usage_boost = -usage_count

        # Exact match gets highest priority
        if query == shortcode_lower.strip(":"):
            return (0, usage_boost, len(shortcode))
        # Starts with query
        if shortcode_lower.strip(":").startswith(query):
            return (1, usage_boost, len(shortcode))
        return (2, usage_boost, len(shortcode))

    matches.sort(key=sort_key)

    return matches[:50]  # Limit results


def format_item(
    emoji_char: str, shortcode: str, description: str, count: int = 0
) -> dict:
    """Format a single emoji item for Alfred JSON output."""
    subtitle = f"{shortcode} - {description}"
    if count > 0:
        subtitle = f"{shortcode} - {description} (used {count}x)"

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


def main(query: str = "", indent: int | None = None):
    """
    Search for emoji by shortcode or description.
    Shows frequently used emoji when query is empty.
    """
    query = query.strip()

    if not query:
        # Show frequently used emoji when no query
        frequent = get_frequently_used()
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
                        "title": "🔍  Search emoji by name or description",
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
            # Get history to show usage counts
            history = load_history()
            result = {
                "items": [
                    format_item(
                        emoji_char,
                        shortcode,
                        description,
                        history.get(emoji_char, {}).get("count", 0),
                    )
                    for emoji_char, shortcode, description in matches
                ]
            }

    print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search emoji by shortcode or description"
    )
    parser.add_argument("query", nargs="?", default="", help="Search query")
    parser.add_argument("--indent", type=int, default=None, help="JSON indent level")
    parser.add_argument(
        "--record",
        metavar="EMOJI",
        help="Record emoji usage (called after selection)",
    )
    args = parser.parse_args()

    if args.record:
        # Record emoji usage and exit
        record_usage(args.record)
    else:
        main(args.query, args.indent)
