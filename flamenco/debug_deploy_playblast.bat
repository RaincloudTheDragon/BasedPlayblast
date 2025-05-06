@echo off
echo Copying BasedPlayblast.js to Flamenco scripts directory...

:: Create a temporary VBS script to request admin privileges
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"

:: Check if running with admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)
del "%temp%\getadmin.vbs"

:: Source file path (current directory)
set SOURCE_FILE=%~dp0BasedPlayblast.js

:: Destination directory
set DEST_DIR=C:\Program Files\Blender Foundation\Flamenco 3.6\scripts

:: Check if source file exists
if not exist "%SOURCE_FILE%" (
    echo ERROR: Source file not found: %SOURCE_FILE%
    goto :end
)

:: Check if destination directory exists
if not exist "%DEST_DIR%" (
    echo ERROR: Destination directory not found: %DEST_DIR%
    goto :end
)

:: Copy the file
copy /Y "%SOURCE_FILE%" "%DEST_DIR%"
if %errorlevel% equ 0 (
    echo Successfully copied BasedPlayblast.js to:
    echo %DEST_DIR%
) else (
    echo ERROR: Failed to copy file to %DEST_DIR%
)

:end
echo.
echo Press any key to exit...
pause >nul 