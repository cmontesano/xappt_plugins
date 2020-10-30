#!/usr/bin/env bash

warn () {
  echo "$0:" "$@" >&2
}

die () {
  rc=$1
  shift
  warn "$@"
  exit $rc
}

version_greater_equal() {
  printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# check python version
python_version="$(python3 -c "import platform;print(platform.python_version())")"
version_greater_equal "${python_version}" 3.7 || die 1 "Python 3.7 or higher is required"

# check required modules
python3 -c "import venv" &> /dev/null || die 1 "venv module not found"
python3 -c "import pip" &> /dev/null || die 1 "pip module not found"

TITLE="Xappt Plugins"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="$(realpath -s "$SCRIPT_PATH/..")"
OLD_CWD=$(pwd)

TMP_PATH=$(mktemp -d -t xp-XXXXXXXXXX)
cd $TMP_PATH

VENV_PATH="$TMP_PATH/venv"

echo "creating virtual environment: $VENV_PATH"
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"
echo "virtualenv activated"

python3 -m pip install -r "$ROOT_PATH/requirements.txt"
python3 -m xappt_qt.builder -o "$TMP_PATH/build" -p "$ROOT_PATH" -t "$TITLE"

cp -r "$TMP_PATH/build" "$ROOT_PATH/build"

cd $OLD_CWD

echo "cleaning up"
rm -rf $TMP_PATH

echo "complete"
