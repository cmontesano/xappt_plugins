@ECHO OFF
SET ROOT_PATH=%cd%
SET INIT_PATH=%ROOT_PATH%\venv\Lib\site-packages\PyQt5\__init__.py

IF EXIST "%INIT_PATH%.bak" (
    DEL "%INIT_PATH%"
    RENAME "%INIT_PATH%.bak" __init__.py
) ELSE (
    ECHO %INIT_PATH%.bak not found
)
