#!/usr/bin/env bash

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="$(realpath -s "$SCRIPT_PATH/..")"

export XAPPT_PLUGIN_PATH="$ROOT_PATH:$XAPPT_PLUGIN_PATH"

source "$ROOT_PATH/venv/bin/activate"
xappt-browser
deactivate
