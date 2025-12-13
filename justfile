set dotenv-load := false

UV_VERSION := "0.5.14"
WORKFLOW_NAME := "Emoji Search"

# List all available recipes
@_default:
    just --list

# Install dependencies and set up the project
@bootstrap:
    just update

# Bump the version number (CalVer: YYYY.0M.PATCH)
@bump:
    uv run bumpver update --patch

# Build the Alfred workflow package for distribution
bundle:
    #!/usr/bin/env bash
    set -euo pipefail

    # Create dist folder
    mkdir -p dist

    # Download uv binary for macOS ARM64 if not present
    if [ ! -f dist/uv ]; then
        echo "Downloading uv {{ UV_VERSION }}..."
        curl -LsSf https://github.com/astral-sh/uv/releases/download/{{ UV_VERSION }}/uv-aarch64-apple-darwin.tar.gz | tar -xz
        mv uv-aarch64-apple-darwin/uv dist/
        rm -rf uv-aarch64-apple-darwin
    fi

    # Copy workflow files to dist
    cp info.plist main.py icon.png dist/

    # Make main.py executable
    chmod +x dist/main.py

    # Build the .alfredworkflow package
    echo "Building {{ WORKFLOW_NAME }}.alfredworkflow..."
    cd dist && rm -f "{{ WORKFLOW_NAME }}.alfredworkflow"
    zip "{{ WORKFLOW_NAME }}.alfredworkflow" info.plist main.py icon.png uv

    echo "Done! Created dist/{{ WORKFLOW_NAME }}.alfredworkflow"

# Remove build artifacts and the dist folder
@clean:
    rm -rf dist

# Format the justfile
@fmt:
    just --fmt --unstable

# Run ruff to lint and format Python code
@lint:
    uv run ruff check --fix .
    uv run ruff format .

# Update the uv.lock file
@lock:
    uv lock

# Open the built workflow in Alfred for testing
@open:
    open "dist/{{ WORKFLOW_NAME }}.alfredworkflow"

# Run the workflow script with optional arguments
@run *ARGS:
    uv run main.py {{ ARGS }}

# Update pip, uv, and sync dependencies
@update:
    pip install --upgrade pip uv
    uv sync
