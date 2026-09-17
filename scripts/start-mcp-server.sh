#!/usr/bin/env sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
VIRTUAL_ENVIRONMENT="$PROJECT_ROOT/.venv"
PYTHON="$VIRTUAL_ENVIRONMENT/bin/python"
REQUIREMENTS="$PROJECT_ROOT/requirements-mcp.txt"
REQUIREMENTS_STAMP="$VIRTUAL_ENVIRONMENT/.mcp-requirements.sha256"

if [ ! -x "$PYTHON" ]; then
    PYTHON_LAUNCHER=""
    for CANDIDATE in python3 python; do
        if command -v "$CANDIDATE" >/dev/null 2>&1; then
            CANDIDATE_PATH=$(command -v "$CANDIDATE")
            if "$CANDIDATE_PATH" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
                PYTHON_LAUNCHER=$CANDIDATE_PATH
                break
            fi
        fi
    done
    if [ -z "$PYTHON_LAUNCHER" ]; then
        echo "Python 3.10 or newer is required." >&2
        exit 1
    fi

    "$PYTHON_LAUNCHER" -m venv "$VIRTUAL_ENVIRONMENT" 1>&2
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "The project virtual environment must use Python 3.10 or newer." >&2
    exit 1
fi

CURRENT_REQUIREMENTS_HASH=$(
    "$PYTHON" -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$REQUIREMENTS"
)
INSTALLED_REQUIREMENTS_HASH=""
if [ -f "$REQUIREMENTS_STAMP" ]; then
    INSTALLED_REQUIREMENTS_HASH=$(tr -d '\r\n' < "$REQUIREMENTS_STAMP")
fi

if [ "$CURRENT_REQUIREMENTS_HASH" != "$INSTALLED_REQUIREMENTS_HASH" ]; then
    "$PYTHON" -m pip install --disable-pip-version-check -r "$REQUIREMENTS" 1>&2
    printf '%s\n' "$CURRENT_REQUIREMENTS_HASH" > "$REQUIREMENTS_STAMP"
fi

cd "$PROJECT_ROOT"
exec "$PYTHON" -m FPGA_Agent.mcp_server "$@"
