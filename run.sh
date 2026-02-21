#!/bin/bash

echo "========================================"
echo "   NeuroSurf - Agentic 3D Browser"
echo "========================================"
echo

# Check if Ollama is running
echo "Checking Ollama status..."
if ! ollama list &> /dev/null; then
    echo "[ERROR] Ollama is not running. Please start Ollama first."
    echo "Run: ollama serve"
    exit 1
fi

echo "[OK] Ollama is running"

# Start backend in background
echo
echo "Starting Neural Backend..."
cd backend && python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting 3D Frontend..."
cd .. && npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
