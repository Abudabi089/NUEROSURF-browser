@echo off
echo ============================================
echo  NeuroSurf - Ollama Ngrok Tunnel Setup
echo ============================================
echo.
echo This script exposes your local Ollama (port 11434) to the web
echo so that Google Opal can send requests to it.
echo.
echo PREREQUISITES:
echo   1. Install Ngrok: https://ngrok.com/download
echo   2. Authenticate: ngrok config add-authtoken YOUR_TOKEN
echo   3. Ollama must be running: ollama serve
echo.
echo ============================================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is not running!
    echo Please start Ollama first: ollama serve
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama is running on port 11434
echo.
echo Starting Ngrok tunnel...
echo.
echo ============================================
echo  IMPORTANT: Copy the "Forwarding" URL below
echo  Example: https://abc123.ngrok-free.app
echo  Use this URL in your Google Opal app!
echo ============================================
echo.

ngrok http 11434 --log=stdout
