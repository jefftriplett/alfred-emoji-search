# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alfred workflow for searching emoji by shortcode and description. Outputs Alfred-compatible JSON to integrate with Alfred's Script Filter. When an emoji is selected, it copies the emoji character to the clipboard.

## Commands

```bash
# Install/update dependencies
just bootstrap      # or: just update

# Run the main workflow
just run "smile"    # search for emoji matching "smile"
just run "heart"    # search for heart emoji

# Linting and formatting
just lint           # runs ruff check --fix and ruff format

# Bundle for Alfred distribution
just bundle         # installs Alfred_Workflow to dist/
```

## Architecture

- **main.py**: Core workflow that searches emoji using the `emoji` library and outputs Alfred-compatible JSON using Pydantic models (`Item`, `ItemContainer`)
- Uses `uv` for package management with Python 3.12
- Dependencies: alfred-workflow, emoji, pydantic, typer, ruff

## How It Works

1. Loads emoji data from the `emoji` library
2. Searches shortcodes (e.g., `:smile:`) and Unicode descriptions
3. Returns matches sorted by relevance (exact match, starts with, contains)
4. Outputs JSON for Alfred Script Filter with emoji as the `arg` (for clipboard)
