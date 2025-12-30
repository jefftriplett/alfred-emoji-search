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

from em.cli import parse_emojis  # noqa: E402


def get_emoji_data() -> list[tuple[str, str, list[str]]]:
    """
    Returns a list of (emoji_char, shortcode, keywords) tuples.
    Uses em-keyboard's emoji database.
    """
    results = []
    lookup = parse_emojis()

    for emoji_char, keywords in lookup.items():
        if keywords:
            # First keyword is the primary shortcode
            shortcode = f":{keywords[0]}:"
            results.append((emoji_char, shortcode, keywords))

    return results


def search_emoji(query: str) -> list[tuple[str, str, str]]:
    """
    Search emoji by shortcode or keywords.
    Returns matching (emoji_char, shortcode, description) tuples.
    """
    query = query.lower().strip()
    if not query:
        return []

    all_emoji = get_emoji_data()
    matches = []

    for emoji_char, shortcode, keywords in all_emoji:
        # Check if query matches any keyword
        keywords_lower = [kw.lower() for kw in keywords]
        if any(query in kw for kw in keywords_lower):
            # Use primary shortcode as description for display
            description = keywords[0].replace("_", " ")
            matches.append((emoji_char, shortcode, description))

    # Sort by relevance: exact shortcode match first, then by shortcode length
    def sort_key(item):
        _, shortcode, _ = item
        shortcode_lower = shortcode.lower()
        # Exact match gets highest priority
        if query == shortcode_lower.strip(":"):
            return (0, len(shortcode))
        # Starts with query
        if shortcode_lower.strip(":").startswith(query):
            return (1, len(shortcode))
        return (2, len(shortcode))

    matches.sort(key=sort_key)

    return matches[:50]  # Limit results


def main(query: str = "", indent: int | None = None):
    """
    Search for emoji by shortcode or description.
    """
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
                {
                    "arg": emoji_char,
                    "subtitle": f"{shortcode} - {description}",
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
    args = parser.parse_args()
    main(args.query, args.indent)
