@echo off
setlocal

set CHANGCODE_DIR=%~dp0
set PYTHONPATH=%CHANGCODE_DIR%;%PYTHONPATH%

if "%1"=="" (
    python "%CHANGCODE_DIR%changcode.py"
) else (
    python "%CHANGCODE_DIR%changcode.py" %*
)
