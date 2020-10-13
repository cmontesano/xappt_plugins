@ECHO OFF
SET ROOT_PATH=%cd%
SET TEMPLATE_DST=%ROOT_PATH%\xp.dist\xappt_plugins\plugins\godot\templates
SET TEMPLATE_SRC=%ROOT_PATH%\xappt_plugins\plugins\godot\templates

MKDIR "%TEMPLATE_DST%"

FOR /f %%i IN ('DIR /b /ad %TEMPLATE_SRC% ^| FINDSTR /v __') DO (
    MKDIR "%TEMPLATE_DST%\%%i"
    XCOPY "%TEMPLATE_SRC%\%%i" "%TEMPLATE_DST%\%%i" /E > NUL
)
