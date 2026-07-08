@echo off
echo Copying BasedPlayblast scripts to Flamenco scripts directory...

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

:: Source file paths (current directory)
set SOURCE_FILE=%~dp0BasedPlayblast.js
set SOURCE_FILE2=%~dp0BasedPlayblast_Optix_GPU.js

:: Destination directory
set DEST_DIR=F:\software\Flamenco\scripts

:: Check if destination directory exists
if not exist "%DEST_DIR%" (
    echo ERROR: Destination directory not found: %DEST_DIR%
    goto :end
)

:: Copy BasedPlayblast.js if it exists
if exist "%SOURCE_FILE%" (
    copy /Y "%SOURCE_FILE%" "%DEST_DIR%"
    if %errorlevel% equ 0 (
        echo Successfully copied BasedPlayblast.js to:
        echo %DEST_DIR%
    ) else (
        echo ERROR: Failed to copy BasedPlayblast.js to %DEST_DIR%
    )
) else (
    echo ERROR: Source file not found: %SOURCE_FILE%
)

:: Copy BasedPlayblast_Optix_GPU.js if it exists
if exist "%SOURCE_FILE2%" (
    copy /Y "%SOURCE_FILE2%" "%DEST_DIR%"
    if %errorlevel% equ 0 (
        echo Successfully copied BasedPlayblast_Optix_GPU.js to:
        echo %DEST_DIR%
    ) else (
        echo ERROR: Failed to copy BasedPlayblast_Optix_GPU.js to %DEST_DIR%
    )
) else (
    echo ERROR: Source file not found: %SOURCE_FILE2%
)

:end
echo.
echo Press any key to exit...
pause >nul 