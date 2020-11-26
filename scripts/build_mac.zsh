#!/bin/zsh
SCRIPT_PATH=${0:a:h}
ROOT_PATH=${SCRIPT_PATH:h}
OLD_CWD=$(pwd)


TMP_DIR=$(mktemp -d -t xp-XXXXXXXXXX)
cd ${TMP_DIR}

VENV_DIR=${TMP_DIR}/venv
REPO_DIR=${TMP_DIR}/xp

echo "creating virtual environment: ${VENV_DIR}"
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate
echo "virtualenv activated"

echo "copying repo..."
cp -r ${ROOT_PATH} ${REPO_DIR}

cd ${REPO_DIR}

python3 -m pip install -r requirements.txt
python3 -m pip install py2app==0.22

py2applet --make-setup xappt_plugins/main.py
python setup.py py2app --packages=PIL,Crypto --iconfile resources/icons/appicon.icns --resources=xappt_plugins/plugins/godot/templates

# Emulate py2exe's `skip_archive`
echo "unzipping python archive..."
unzip dist/main.app/Contents/Resources/lib/python38.zip -d dist/main.app/Contents/Resources/lib/python38
rm dist/main.app/Contents/Resources/lib/python38.zip
mv dist/main.app/Contents/Resources/lib/python38 dist/main.app/Contents/Resources/lib/python38.zip

echo "copying app to project directory..."
cp -r dist ${ROOT_PATH}


cd ${OLD_CWD}

echo "cleaning up"
rm -rf $TMP_DIR

echo "complete"