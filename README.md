# Emoji Search for Alfred

Search and copy emoji by shortcode or description.

## Installation

1. Download `Emoji Search.alfredworkflow` from the [releases](https://github.com/jefftriplett/alfred-emoji-search/releases) page
2. Double-click to install in Alfred

Python **3.12 or newer** must be installed separately. The workflow checks your
PATH, standard Homebrew locations (Apple Silicon and Intel), and python.org
installations. It skips older interpreters, including macOS's Python 3.9.
If no supported interpreter is available, Alfred displays an installation message.

For a custom installation, add the workflow environment variable `emoji_python`
in Alfred's workflow configuration and set it to the absolute Python executable
path (for example, `/opt/homebrew/bin/python3`). An explicit override must point
to Python 3.12+; an invalid override displays the same setup message.

Or build it yourself with `just bundle`.

## Usage

Type `emoji` followed by a search term:

```
emoji heart
emoji fire
emoji party
emoji thumbs
emoji :fire:
emoji party popper
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
- Terms you've searched and selected an emoji for nudge matching emoji higher in the results
- Shows frequently used emoji when query is empty
- Returns up to 50 results per search

## Settings

Configure the workflow in Alfred (right-click the workflow → **Configure Workflow…**):

| Setting | Default | Description |
|---------|---------|-------------|
| Log search history | On | Record search terms when you select an emoji to `search_history.json`. Turn off to stop logging searches entirely. |
| Personalize ordering | On | Use your search history to weight the order of results. Turn off to rank results without it. |

## Data Storage

History is stored following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

```
~/.config/alfred-emoji-search/history.json         # emoji usage counts
~/.config/alfred-emoji-search/search_history.json  # search-term counts
```

Search terms are recorded only when you select an emoji, including with modifier keys. Typing and canceled searches do not write history. Turning off logging preserves existing history; delete `search_history.json` to clear it.

## Development

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

### Commands

```bash
just bootstrap    # Install dependencies and set up the project
just run "heart"  # Run the workflow script with optional arguments
just test         # Run regression tests
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
