# Emoji Lookup Alfred Workflow

Search and copy emoji by shortcode or description.

## Installation

1. Download `Emoji Lookup.alfredworkflow` from the [releases](https://github.com/jefftriplett/alfred-emoji/releases) or build it yourself with `just bundle`
2. Double-click to install in Alfred

## Usage

Type `emoji` followed by a search term:

```
emoji heart
emoji fire
emoji party
emoji thumbs
```

### Modifier Keys

- **Enter** → Copy the emoji (e.g., 🎉)
- **Option (⌥) + Enter** → Copy the shortcode with colons (e.g., `:party_popper:`)
- **Cmd (⌘) + Enter** → Copy the shortcode without colons (e.g., `party_popper`)

## Development

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for Python package management
- [just](https://github.com/casey/just) for running commands

### Commands

```bash
# Install/update dependencies
just bootstrap

# Run the script directly
just run "heart"

# Run with pretty-printed JSON output
uv run main.py "heart" --indent 2

# Build the Alfred workflow
just bundle

# Clean build artifacts
just clean

# Lint and format code
just lint

# Bump version (CalVer: YYYY.0M.PATCH)
just bump
```

### Project Structure

```
├── main.py          # Main script with PEP 723 inline dependencies
├── info.plist       # Alfred workflow configuration
├── justfile         # Build and development commands
├── pyproject.toml   # Project metadata and bumpver config
├── uv.lock          # Locked dependencies
└── dist/            # Built workflow (after running `just bundle`)
    ├── Emoji Lookup.alfredworkflow
    ├── main.py
    ├── info.plist
    └── uv           # Bundled uv binary (aarch64-apple-darwin)
```

## How It Works

- Uses the [emoji](https://pypi.org/project/emoji/) library for emoji data
- Searches both shortcodes (e.g., `:fire:`) and Unicode descriptions
- Results are sorted by relevance (exact match → starts with → contains)
- Returns up to 50 results per search
- The workflow bundles a standalone `uv` binary so it works without any system dependencies

## License

MIT
