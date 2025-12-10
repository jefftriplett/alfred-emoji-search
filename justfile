set dotenv-load := false

UV_VERSION := "0.9.17"
WORKFLOW_NAME := "Emoji Lookup"

@_default:
    just --list

@bootstrap:
    just update

@bump:
    uv run bumpver update

@bundle:
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
    cp info.plist main.py dist/

    # Build the .alfredworkflow package
    echo "Building {{ WORKFLOW_NAME }}.alfredworkflow..."
    cd dist && rm -f "{{ WORKFLOW_NAME }}.alfredworkflow"
    zip "{{ WORKFLOW_NAME }}.alfredworkflow" info.plist main.py uv

    echo "Done! Created dist/{{ WORKFLOW_NAME }}.alfredworkflow"

@clean:
    rm -rf dist

@fmt:
    just --fmt --unstable

@lint:
    uv run ruff check --fix .
    uv run ruff format .

@lock:
    uv lock

@run *ARGS:
    uv run main.py {{ ARGS }}

@update:
    pip install --upgrade pip uv
    uv sync
