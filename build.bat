@echo off
cd /d "%~dp0"

echo === Sports Clock - Build Script ===
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH.
    pause & exit /b 1
)

:: Install / upgrade dependencies
echo [1/3] Installing dependencies...
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller

:: Run PyInstaller
echo [2/3] Building executable...
python -m PyInstaller sports_clock.spec --noconfirm --clean

:: Check result
if errorlevel 1 (
    echo.
    echo BUILD FAILED. See errors above.
    pause & exit /b 1
)

:: Create user-facing logos folder next to the .exe
if not exist dist\logos (
    mkdir dist\logos
    echo Place your team logo images (.png .jpg .bmp .ico) in this folder. > dist\logos\README.txt
    echo The app opens this folder when you click "Change Logo...". >> dist\logos\README.txt
)

echo.
echo [3/3] Done!
echo.
echo Output file:  dist\SportsClockApp.exe
echo Run:          dist\SportsClockApp.exe
echo.
echo Drop team logos into:  dist\logos\
echo.
echo To share: copy dist\SportsClockApp.exe and the dist\logos\ folder together.
echo No Python required on the target machine.
echo.
pause
