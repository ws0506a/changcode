@echo off
setlocal

set QINGCODE_DIR=%~dp0
set PYTHONPATH=%QINGCODE_DIR%;%PYTHONPATH%

if "%1"=="" (
    python "%QINGCODE_DIR%qingcode.py"
) else (
    python "%QINGCODE_DIR%qingcode.py" %*
)
