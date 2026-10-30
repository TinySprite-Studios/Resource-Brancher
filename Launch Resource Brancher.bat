@echo off
setlocal
cd /d "%~dp0"

where python.exe >nul 2>&1
if errorlevel 1 (
    echo Python 3.10 or newer is required. Install it from python.org and add it to PATH.
    pause
    exit /b 1
)

python.exe -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo Setting up the desktop interface for the first launch...
    python.exe -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Setup failed. Please check the message above.
        pause
        exit /b 1
    )
)

python.exe -c "import pathlib, subprocess, sys; executable = pathlib.Path(sys.executable).with_name('pythonw.exe'); subprocess.Popen([str(executable), str(pathlib.Path.cwd() / 'resource_brancher.py')])"
if errorlevel 1 pause
