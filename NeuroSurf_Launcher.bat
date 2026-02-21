@echo off
title NeuroSurf Launcher
echo ==================================================
echo      NEUROSURF - AI COMPANION LAUNCHER
echo ==================================================

echo.
echo [1/2] Starting Neural Backend (Python)...
cd backend
start /B python main.py > neuro_backend.log 2>&1
cd ..

echo.
echo [2/2] Launching Interface...
echo.
echo NeuroSurf is starting. Please wait for the window...
echo.
call npm run dev

pause
