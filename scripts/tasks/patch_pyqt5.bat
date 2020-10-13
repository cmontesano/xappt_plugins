rem https://github.com/Nuitka/Nuitka/issues/453
@ECHO OFF
SET ROOT_PATH=%cd%
SET TEMPLATE_PATH=%ROOT_PATH%\scripts\tasks\pyqt5_init_windows.txt
SET INIT_PATH=%ROOT_PATH%\venv\Lib\site-packages\PyQt5\__init__.py

RENAME "%INIT_PATH%" "__init__.py.bak"
COPY "%TEMPLATE_PATH%" "%INIT_PATH%" > NUL
