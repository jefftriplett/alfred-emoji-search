set dotenv-load := false

WORKFLOW_NAME := "Emoji Search"

# List all available recipes
@_default:
    just --list

# Install dependencies and set up the project
@bootstrap:
    just update

# Bump the version number (CalVer: YYYY.0M.PATCH)
@bump:
    uv run --locked bumpver update --patch

# Build the Alfred workflow package for distribution
bundle:
    #!/usr/bin/env bash
    set -euo pipefail

    mkdir -p dist
    bundle_stage=$(mktemp -d "$PWD/dist/.bundle.XXXXXX")
    trap 'rm -rf "$bundle_stage"' EXIT

    uv export --locked --no-dev --no-emit-project --prune alfred-workflow --output-file "$bundle_stage/requirements.txt"
    uv pip install --python 3.12 --target "$bundle_stage/lib" --require-hashes -r "$bundle_stage/requirements.txt"
    cp info.plist icon.png "$bundle_stage/"
    cp src/main.py src/launch.sh "$bundle_stage/"
    chmod +x "$bundle_stage/main.py" "$bundle_stage/launch.sh"

    uv run --locked --python 3.12 python tests/smoke_bundle.py "$bundle_stage"
    (cd "$bundle_stage" && zip -qr "{{ WORKFLOW_NAME }}.alfredworkflow" info.plist main.py launch.sh icon.png lib/)
    mv "$bundle_stage/{{ WORKFLOW_NAME }}.alfredworkflow" dist/
    echo "Created dist/{{ WORKFLOW_NAME }}.alfredworkflow"

# Run regression tests
@test:
    uv run --locked python -m unittest discover -s tests -v

# Remove build artifacts and the dist folder
@clean:
    rm -rf dist

# Format the justfile
@fmt:
    just --fmt --unstable

# Run ruff to lint and format Python code
@lint:
    uv tool run ruff check --fix .
    uv tool run ruff format .

# Update the uv.lock file
@lock:
    uv lock

# Open the built workflow in Alfred for testing
@open:
    open "dist/{{ WORKFLOW_NAME }}.alfredworkflow"

# Run the workflow script with optional arguments
@run *ARGS:
    uv run --locked python src/main.py {{ ARGS }}

# Update pip, uv, and sync dependencies
@update:
    pip install --upgrade pip uv
    uv sync
