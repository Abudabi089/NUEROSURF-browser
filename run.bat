@echo off
setlocal enabledelayedexpansion

title NeuroSurf Launcher
echo ========================================
echo    NeuroSurf - Agentic 3D Browser
echo ========================================
echo.

REM --- System Requirements Check ---
echo [1/6] Checking system requirements...

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install it from https://nodejs.org/
    pause
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install it from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Node.js and Python found.

REM --- Node Dependencies ---
echo.
echo [2/6] Checking Node.js dependencies...
if not exist "node_modules" (
    echo [SETUP] Installing npm dependencies (this may take a minute)...
    call npm install
) else (
    echo [OK] Node modules already installed.
)

REM --- Python Dependencies ---
echo.
echo [3/6] Checking Python dependencies...
if not exist "backend\.dependencies_installed" (
    echo [SETUP] Installing Python requirements...
    pip install -r requirements.txt
    if !errorlevel! equ 0 (
        echo Done > "backend\.dependencies_installed"
    ) else (
        echo [ERROR] pip install failed.
    )
) else (
    echo [OK] Python dependencies already installed.
)

REM --- Ollama Check & Setup ---
echo.
echo [4/6] Checking Ollama service...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama command not found. Make sure Ollama is installed.
) else (
    ollama list >nul 2>&1
    if !errorlevel! neq 0 (
        echo [STATUS] Starting Ollama service...
        start /min "" ollama serve
        timeout /t 5 /nobreak >nul
    )
    
    REM Check for default model
    echo [STATUS] Verifying models...
    ollama list | findstr "llama3" >nul
    if !errorlevel! neq 0 (
        echo [SETUP] Pulling llama3 (one-time setup)...
        ollama pull llama3
    )
)

REM --- Backend Launch ---
echo.
echo [5/6] Starting Neural Backend...
if exist "backend\neuro_backend.log" del "backend\neuro_backend.log"
start "NeuroSurf Backend" /min cmd /c "cd backend && python main.py > neuro_backend.log 2>&1"

REM Wait for backend to bind to port 8000
echo Waiting for backend to initialize...
:wait_loop
timeout /t 2 /nobreak >nul
netstat -ano | findstr :8000 >nul
if %errorlevel% neq 0 (
    set /a retry+=1
    if !retry! gtr 15 (
        echo [ERROR] Backend failed to start. Check backend/neuro_backend.log
        pause
        exit /b 1
    )
    goto wait_loop
)
echo [OK] Backend is ready.

REM --- Frontend Launch ---
echo.
echo [6/6] Launching NeuroSurf Desktop App...
echo ========================================
echo NEUROSURF IS NOW ACTIVE
echo ========================================
call npm run dev

pause
