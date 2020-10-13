@ECHO OFF

SET OLD_CWD=%cd%
SET OLD_PATH=%PATH%

SET SCRIPT_PATH=%~dp0
SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

cd ..
SET ROOT_PATH=%cd%

cd %ROOT_PATH%

CALL %ROOT_PATH%\venv\Scripts\activate.bat

pip install nuitka

CALL %SCRIPT_PATH%\tasks\patch_pyqt5.bat
CALL %SCRIPT_PATH%\tasks\build_nuitka.bat
CALL %SCRIPT_PATH%\tasks\copy_templates.bat
CALL %SCRIPT_PATH%\tasks\unpatch_pyqt5.bat

cd %OLD_CWD%

deactivate

SET PATH=%OLD_PATH%
