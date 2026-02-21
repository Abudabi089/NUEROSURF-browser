---
description: How to run and develop NeuroSurf
---

# Running NeuroSurf

## Prerequisites

1. Install Ollama from https://ollama.ai
2. Pull required models:
   ```bash
   ollama pull qwen2.5:3b
   ollama pull llava:latest
   ```

## Quick Start (Windows)

// turbo-all
```bash
run.bat
```

## Manual Start

### Step 1: Start Ollama
```bash
ollama serve
```

### Step 2: Start Backend
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

### Step 3: Start Frontend
```bash
npm install
npm run dev
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F2 | Toggle 3D/Browser View |
| F3 | Toggle Terminal |
| F4 | Toggle File Manager |
| F8 | Toggle Zen Focus Mode |
| F12 | Toggle Phase 12 |
| Escape | Halt Agent |

## Development

### Frontend (React + Three.js)
- Edit components in `src/components/`
- 3D scene in `src/components/Scene3D.jsx`
- State management in `src/store/useStore.js`

### Backend (Python FastAPI)
- Autonomous Agent in `backend/autonomous_agent.py`
- Agent Tools in `backend/agent_tools.py`
- Socket handlers in `backend/main.py`

### Agent (Browser Automation)
- Playwright actions in `agent/browser_agent.py`
- Vision fallback in `agent/vision_helper.py`
