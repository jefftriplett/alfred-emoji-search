#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "emoji",
#     "pydantic",
#     "typer",
# ]
# ///
"""
Emoji lookup Alfred workflow

uv run main.py "smile"

Searches emoji by shortcode and description.
"""

import unicodedata

import emoji
import typer
from pydantic import BaseModel


class Mod(BaseModel):
    arg: str
    subtitle: str
    valid: bool = True


class Mods(BaseModel):
    alt: Mod | None = None
    cmd: Mod | None = None


class Command(BaseModel):
    arg: str
    subtitle: str
    title: str
    mods: Mods | None = None


class CommandContainer(BaseModel):
    items: list[Command]


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
    """
    query = query.lower().strip()
    if not query:
        return []

    all_emoji = get_emoji_data()
    matches = []

    for emoji_char, shortcode, description in all_emoji:
        shortcode_lower = shortcode.lower()
        description_lower = description.lower()

        # Check if query matches shortcode or description
        if query in shortcode_lower or query in description_lower:
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


def main(query: str = typer.Argument(""), indent: int = None):
    """
    Search for emoji by shortcode or description.
    """
    matches = search_emoji(query)

    if not matches:
        container = CommandContainer(
            items=[
                Command(
                    arg="",
                    subtitle="No emoji found",
                    title=f"No results for '{query}'",
                )
            ]
        )
    else:
        container = CommandContainer(
            items=[
                Command(
                    arg=emoji_char,
                    subtitle=f"{shortcode} - {description}",
                    title=f"{emoji_char}  {shortcode.strip(':')}",
                    mods=Mods(
                        alt=Mod(
                            arg=shortcode,
                            subtitle=f"Copy shortcode: {shortcode}",
                        ),
                        cmd=Mod(
                            arg=shortcode.strip(":"),
                            subtitle=f"Copy without colons: {shortcode.strip(':')}",
                        ),
                    ),
                )
                for emoji_char, shortcode, description in matches
            ]
        )

    print(container.model_dump_json(indent=indent))


if __name__ == "__main__":
    typer.run(main)
