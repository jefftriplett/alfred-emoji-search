#!/bin/bash
# Alfred's PATH may omit Homebrew and python.org installations.
set -u
workflow_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

run_python() {
    local candidate="$1"
    shift
    [[ -x "$candidate" ]] || return
    "$candidate" -I -S -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1 || return
    exec "$candidate" "$workflow_dir/main.py" "$@"
}

if [[ -n "${emoji_python:-}" ]]; then
    # An explicit override is authoritative; report errors instead of silently
    # choosing a different installation.
    run_python "$emoji_python" "$@"
else
    candidates=(
        "$(command -v python3 || true)"
        /opt/homebrew/bin/python3
        /usr/local/bin/python3
        /opt/homebrew/opt/python@3.*/bin/python3.*
        /usr/local/opt/python@3.*/bin/python3.*
        /Library/Frameworks/Python.framework/Versions/3.*/bin/python3
    )
    for candidate in "${candidates[@]}"; do
        run_python "$candidate" "$@"
    done
fi

# The Script Filter needs valid JSON even when no supported runtime is present.
printf '%s\n' '{"items":[{"title":"Python 3.12 or newer is required","subtitle":"Install Python 3.12+ or set emoji_python to its executable path in workflow configuration.","valid":false}]}'
printf '%s\n' 'Emoji Search: Python 3.12+ was not found. Install it or set emoji_python to an absolute executable path.' >&2
exit 1
