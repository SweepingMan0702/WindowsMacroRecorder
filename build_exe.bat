@echo off
cd /d "%~dp0"

echo ====================================================
echo   Windows Macro Recorder - PyInstaller Build
echo ====================================================
echo.

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python was not found.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo [3/3] Building EXE...
python -m PyInstaller --noconfirm --onedir --windowed --name "WindowsMacroRecorder" --uac-admin main.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   Build completed successfully.
echo   EXE: dist\WindowsMacroRecorder\WindowsMacroRecorder.exe
echo ====================================================
pause
