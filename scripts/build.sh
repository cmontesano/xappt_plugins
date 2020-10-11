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



SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="$(realpath -s "$SCRIPT_PATH/..")"
OLD_CWD=$(pwd)

TMP_DIR=$(mktemp -d -t xp-XXXXXXXXXX)
cd $TMP_DIR

VENV_DIR=$TMP_DIR/venv
REPO_DIR=$TMP_DIR/xp

echo "creating virtual environment: $VENV_DIR"
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
echo "virtualenv activated"

# replace this with a git clone
cp -r $ROOT_PATH $REPO_DIR

cd $REPO_DIR

python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller~=4.0

pyinstaller $SCRIPT_PATH/build.spec --onefile

ls -l $TMP_DIR/xp



cd $OLD_CWD

echo "cleaning up"
rm -rf $TMP_DIR

echo "complete"