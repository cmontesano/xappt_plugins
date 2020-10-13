@ECHO OFF
SET ROOT_PATH=%cd%
python -m nuitka --standalone --remove-output --recurse-all --windows-icon="%ROOT_PATH%\resources\icons\appicon.ico" --plugin-enable=qt-plugins xp.py
