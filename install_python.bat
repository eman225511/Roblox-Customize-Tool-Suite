@echo off
title Python Auto Installer
color 0E

REM Enable delayed expansion for better variable handling
setlocal enabledelayedexpansion

echo.
echo +============================================================+
echo ^|                    PYTHON AUTO INSTALLER                  ^|
echo ^|              Installing Python with PATH setup            ^|
echo +============================================================+
echo.

REM Check for admin rights (optional but recommended)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Running without administrator privileges.
    echo [INFO] Installation will proceed for current user only.
    echo.
)

REM Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Python is already installed!
    python --version
    echo.
    echo Do you want to reinstall Python? (Y/N)
    set /p reinstall="Choice: "
    if /i not "%reinstall%"=="Y" (
        echo Installation cancelled.
        pause
        exit /b
    )
)

echo [INFO] Starting Python installation...
echo.

REM Create temp directory for download with space-safe path
set "TEMP_DIR=%TEMP%\python_installer"
if not exist "!TEMP_DIR!" mkdir "!TEMP_DIR!"
cd /d "!TEMP_DIR!"

REM Download Python installer (latest stable version)
echo [DOWNLOAD] Downloading Python installer...
echo This may take a few minutes depending on your internet connection...
echo.

REM Using PowerShell to download Python 3.12.1 (latest stable) with better error handling
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe' -OutFile 'python-installer.exe' -UseBasicParsing } catch { Write-Host 'Download failed. Trying alternative method...'; try { [System.Net.WebClient]::new().DownloadFile('https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe', 'python-installer.exe') } catch { Write-Host 'Both download methods failed.'; exit 1 } }}"

if not exist "python-installer.exe" (
    echo [ERROR] Failed to download Python installer!
    echo Please check your internet connection and try again.
    echo.
    echo Alternative: Download manually from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [SUCCESS] Python installer downloaded successfully!
echo.

REM Install Python with proper handling for paths with spaces
echo [INSTALL] Installing Python with the following options:
echo - Add Python to PATH
echo - Install pip package manager  
echo - Install for current user (safer for paths with spaces)
echo - Associate files with Python
echo.
echo Starting installation...

REM Check admin rights and adjust installation accordingly
net session >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Installing for all users (admin mode)
    "%CD%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1 AssociateFiles=1
) else (
    echo [INFO] Installing for current user only (safer for spaces)
    "%CD%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1 AssociateFiles=1
)

REM Wait for installation to complete
timeout /t 10 /nobreak >nul

echo [INSTALL] Installation completed!
echo.

REM Refresh environment variables
echo [CONFIG] Refreshing environment variables...
setx PATH "%PATH%" >nul 2>&1

REM Test Python installation
echo [TEST] Testing Python installation...
echo.

REM Refresh PATH for current session with proper quoting
call refreshenv >nul 2>&1 || (
    echo [INFO] Refreshing PATH manually...
    REM Add common Python installation paths with quotes
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312"
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"
    set "PATH=%PATH%;C:\Program Files\Python312"
    set "PATH=%PATH%;C:\Program Files\Python312\Scripts"
    set "PATH=%PATH%;%APPDATA%\Python\Python312"
    set "PATH=%PATH%;%APPDATA%\Python\Python312\Scripts"
)

REM Test Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Python installed successfully!
    python --version
    echo.
    
    REM Test pip
    pip --version >nul 2>&1
    if %errorlevel% == 0 (
        echo [SUCCESS] pip installed successfully!
        pip --version
    ) else (
        echo [WARNING] pip might not be available yet. Restart your command prompt.
    )
) else (
    echo [WARNING] Python installation completed but not immediately available.
    echo Please restart your command prompt or computer and try again.
    echo.
    echo If the issue persists, you may need to:
    echo 1. Restart your computer
    echo 2. Manually add Python to PATH
    echo 3. Reinstall Python with administrator privileges
)

echo.
echo [CLEANUP] Cleaning up temporary files...
cd /d "%USERPROFILE%"
if exist "!TEMP_DIR!" (
    rmdir /s /q "!TEMP_DIR!" >nul 2>&1
)

echo.
echo +============================================================+
echo ^|                    INSTALLATION COMPLETE                  ^|
echo +============================================================+
echo.
echo Next steps:
echo 1. Restart your command prompt for PATH changes to take effect
echo 2. You can now use 'python' and 'pip' commands
echo 3. Run 'python --version' to verify installation
echo.
echo Press any key to continue...
pause >nul
