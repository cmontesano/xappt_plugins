#!/usr/bin/env bash

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="$(realpath -s "$SCRIPT_PATH/..")"
OLD_CWD=$(pwd)

if which python3 &> /dev/null ; then
  if python3 -c "import venv" &> /dev/null ; then
    if python3 -c "import pip" &> /dev/null ; then
      cd $ROOT_PATH
      python3 -m venv venv
      source venv/bin/activate
      python -m pip install -r requirements.txt
    else
      echo "module pip not found"
    fi
  else
    echo "module venv not found"
  fi
else
  echo "python3 not found, please create a virtual environment manually"
fi

cd $OLD_CWD
