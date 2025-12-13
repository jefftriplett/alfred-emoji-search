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
```

### Keyboard Shortcuts

| Key | Action | Example |
|-----|--------|---------|
| Enter | Copy emoji | 🎉 |
| Option + Enter | Copy shortcode with colons | `:party_popper:` |
| Cmd + Enter | Copy shortcode without colons | `party_popper` |

## How It Works

- Searches both shortcodes (`:fire:`) and Unicode descriptions
- Results sorted by relevance: exact match → starts with → contains
- Returns up to 50 results per search
- Self-contained workflow with bundled `uv` binary (no system dependencies required)

## Development

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

### Commands

```bash
just bootstrap    # Install dependencies
just run "heart"  # Run the script
just bundle       # Build the workflow
just clean        # Remove build artifacts
just lint         # Lint and format code
just bump         # Bump version (CalVer: YYYY.0M.PATCH)
```

## License

MIT
