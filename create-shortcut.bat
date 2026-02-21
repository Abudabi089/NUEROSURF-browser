@echo off
REM NeuroSurf Desktop Shortcut Creator
REM Creates a shortcut on the desktop to launch NeuroSurf

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_NAME=NeuroSurf.lnk

echo Creating NeuroSurf desktop shortcut...

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%SCRIPT_DIR%run.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = '%SCRIPT_DIR%public\icon.png'; $Shortcut.Description = 'NeuroSurf - Agentic 3D Browser'; $Shortcut.Save()"

if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo.
    echo ✅ Desktop shortcut created successfully!
    echo    Location: %DESKTOP%\%SHORTCUT_NAME%
) else (
    echo.
    echo ❌ Failed to create shortcut
)

pause
