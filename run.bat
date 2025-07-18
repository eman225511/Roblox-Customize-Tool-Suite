@echo off
title CustomizeRoblox Launcher
color 0B

REM Enable delayed expansion for better variable handling
setlocal enabledelayedexpansion

REM Get current script directory for safe path handling
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:start
cls
echo.
echo +============================================================+
echo ^|                    CUSTOMIZEROBLOX LAUNCHER                ^|
echo ^|                     Choose Your Tool                      ^|
echo +============================================================+
echo.
echo  [1] FastFlag Applier    - Fast Flags
echo  [2] CDBL-Lite           - Custom Debloated Blox Launcher
echo  [3] Fleasion Backend    - Fleasion
echo  [4] Install Python      - Auto install Python with PATH
echo  [5] Exit
echo.
set /p choice="Select option (1-5): "

if "%choice%"=="1" goto fastflags
if "%choice%"=="2" goto cdbl
if "%choice%"=="3" goto fleasion
if "%choice%"=="4" goto installpython
if "%choice%"=="5" goto exit
echo Invalid choice. Please select 1-5.
pause
goto start

:fastflags
cls
echo Starting FastFlag Applier...
if exist "%SCRIPT_DIR%ApplyFastFlags.ps1" (
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%ApplyFastFlags.ps1"
) else (
    echo [ERROR] ApplyFastFlags.ps1 not found in: %SCRIPT_DIR%
    pause
)
pause
goto start

:cdbl
cls
echo Starting CDBL-Lite...
if exist "%SCRIPT_DIR%CDBL-Lite.exe" (
    start "" "%SCRIPT_DIR%CDBL-Lite.exe"
) else (
    echo [ERROR] CDBL-Lite.exe not found in: %SCRIPT_DIR%
    pause
)
goto start

:fleasion
cls
echo Starting Fleasion Backend...

REM Check if Python is installed
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Python is not installed or not in PATH!
    echo Fleasion Backend requires Python to run.
    echo.
    echo Would you like to install Python automatically? (Y/N)
    set /p installpy="Choice: "
    if /i "!installpy!"=="Y" (
        if exist "%SCRIPT_DIR%install_python.bat" (
            call "%SCRIPT_DIR%install_python.bat"
        ) else (
            echo [ERROR] install_python.bat not found!
        )
        echo.
        echo Python installation completed. Continuing with Fleasion...
        timeout /t 3 >nul
    ) else (
        echo Please install Python manually and try again.
        pause
        goto start
    )
)

if exist "%SCRIPT_DIR%Fleasion-Backend-main\run.bat" (
    cd /d "%SCRIPT_DIR%Fleasion-Backend-main"
    call "run.bat"
    cd /d "%SCRIPT_DIR%"
) else (
    echo [ERROR] Fleasion-Backend-main\run.bat not found in: %SCRIPT_DIR%
    pause
)
goto start

:installpython
cls
echo Starting Python Auto Installer...
if exist "%SCRIPT_DIR%install_python.bat" (
    call "%SCRIPT_DIR%install_python.bat"
) else (
    echo [ERROR] install_python.bat not found in: %SCRIPT_DIR%
    pause
)
goto start

:exit
exit
