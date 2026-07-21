# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alfred workflow for searching emoji by shortcode and description. Outputs Alfred-compatible JSON to integrate with Alfred's Script Filter. When an emoji is selected, it copies the emoji character to the clipboard. Modifier keys allow copying the shortcode with or without colons.

## Commands

```bash
just bootstrap    # Install dependencies and set up the project
just run "heart"  # Run the workflow script with optional arguments
just bundle       # Build the Alfred workflow package for distribution
just open         # Open the built workflow in Alfred for testing
just clean        # Remove build artifacts and the dist folder
just lint         # Run ruff to lint and format Python code
just lock         # Update the uv.lock file
just bump         # Bump the version number (CalVer: YYYY.MM.PATCH)
just update       # Update pip, uv, and sync dependencies
just fmt          # Format the justfile

# Run with pretty-printed JSON output
uv run src/main.py "heart" --indent 2
```

## Architecture

- **src/main.py**: Core workflow script with PEP 723 inline dependencies. Searches emoji using `em-keyboard`'s emoji database and outputs Alfred-compatible JSON
- **info.plist**: Alfred workflow configuration (keyword: `emoji`, bundle ID: `com.jefftriplett.alfred-emoji-search`)
- **justfile**: Build and development commands
- **pyproject.toml**: Project metadata and bumpver configuration
- Uses `uv` for package management with Python 3.12+
- Runtime dependencies (in main.py): em-keyboard
- Dev dependencies (in pyproject.toml): alfred-workflow, bumpver, ruff

## How It Works

1. Uses `em-keyboard`'s `do_find()` for searching and `parse_emojis()` for emoji data
2. Searches shortcodes and keywords (e.g., "smile", "happy", "joy", ":d")
3. Returns matches sorted by relevance (exact match, starts with, contains)
4. Boosts frequently used emoji in search results
5. Limits results to 50 items
6. Outputs JSON for Alfred Script Filter with:
   - Default (Enter): copies emoji character
   - Alt modifier: copies shortcode with colons (e.g., `:party_popper:`)
   - Cmd modifier: copies shortcode without colons (e.g., `party_popper`)

## History Tracking

- Stores usage history in `~/.config/alfred-emoji-search/history.json`
- When query is empty, shows frequently used emoji sorted by usage count
- Frequently used emoji are boosted in search results
- Usage count displayed in subtitle (e.g., "used 5x")
- History recorded via `--record` flag when emoji is selected

## Bundling

The `just bundle` command:
1. Installs `em-keyboard` into `dist/lib/` using `uv pip install --target`
2. Copies `main.py`, `info.plist`, and `icon.png` to `dist/`
3. Creates `Emoji Search.alfredworkflow` zip package

The bundled workflow includes `em-keyboard` in `lib/` and runs via the system Python 3. The `main.py` script automatically adds the bundled `lib/` directory to `sys.path` when present.
