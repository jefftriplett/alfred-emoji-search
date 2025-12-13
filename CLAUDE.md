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
just bump         # Bump the version number (CalVer: YYYY.0M.PATCH)
just update       # Update pip, uv, and sync dependencies
just fmt          # Format the justfile

# Run with pretty-printed JSON output
uv run main.py "heart" --indent 2
```

## Architecture

- **main.py**: Core workflow script with PEP 723 inline dependencies. Searches emoji using the `emoji` library and outputs Alfred-compatible JSON using Pydantic models (`Command`, `CommandContainer`, `Mod`, `Mods`)
- **info.plist**: Alfred workflow configuration (keyword: `emoji`, bundle ID: `com.jefftriplett.alfred-emoji-search`)
- **justfile**: Build and development commands
- **pyproject.toml**: Project metadata and bumpver configuration
- Uses `uv` for package management with Python 3.12+
- Runtime dependencies (in main.py): emoji, pydantic, typer
- Dev dependencies (in pyproject.toml): alfred-workflow, bumpver, ruff

## How It Works

1. Loads emoji data from the `emoji` library's `EMOJI_DATA` dictionary
2. Searches shortcodes (e.g., `:smile:`) and Unicode descriptions via `unicodedata.name()`
3. Returns matches sorted by relevance (exact match, starts with, contains)
4. Limits results to 50 items
5. Outputs JSON for Alfred Script Filter with:
   - Default (Enter): copies emoji character
   - Alt modifier: copies shortcode with colons (e.g., `:party_popper:`)
   - Cmd modifier: copies shortcode without colons (e.g., `party_popper`)

## Bundling

The `just bundle` command:
1. Downloads a standalone `uv` binary (aarch64-apple-darwin) to `dist/`
2. Copies `main.py` and `info.plist` to `dist/`
3. Creates `Emoji Search.alfredworkflow` zip package

The bundled workflow is self-contained and requires no system dependencies.
