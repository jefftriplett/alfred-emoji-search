# Emoji Search for Alfred

Search and copy emoji by shortcode or description.

## Installation

1. Download `Emoji Search.alfredworkflow` from the [releases](https://github.com/jefftriplett/alfred-emoji-search/releases) page
2. Double-click to install in Alfred

Or build it yourself with `just bundle`.

## Usage

Type `emoji` followed by a search term:

```
emoji heart
emoji fire
emoji party
emoji thumbs
emoji version   # Show version info and GitHub links
```

### Keyboard Shortcuts

| Key | Action | Example |
|-----|--------|---------|
| Enter | Copy emoji | 🎉 |
| Option + Enter | Copy shortcode with colons | `:party_popper:` |
| Cmd + Enter | Copy shortcode without colons | `party_popper` |

## How It Works

- Searches both shortcodes (`:fire:`) and keywords via [em-keyboard](https://github.com/kennethreitz/em-keyboard)
- Results sorted by relevance: exact match → starts with → contains
- Frequently used emoji are boosted in search results
- Shows frequently used emoji when query is empty
- Returns up to 50 results per search

## Data Storage

Usage history is stored following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

```
~/.config/alfred-emoji-search/history.json
```

## Development

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

### Commands

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
```

## License

MIT License - Copyright (c) 2025 Jeff Triplett
