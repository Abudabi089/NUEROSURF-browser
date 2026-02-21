# NeuroSurf

A local-first, agentic web browser with a high-fidelity 3D spatial interface, powered by a local LLM swarm via Ollama.

![NeuroSurf](./public/neuro.svg)

## Features

- **3D Spatial Interface**: Navigate tabs as orbiting objects in 3D space
- **Neural Halo**: Visual feedback ring showing agent state (Blue=Idle, Gold=Planning, Red=Acting, Purple=Listening)
- **LLM Swarm**: Dynamic model management with Executive, Navigator, Eye, and Clerk models
- **Vision-Augmented Browsing**: Falls back to LLaVA screenshot analysis when DOM fails
- **Gesture Control**: Pinch to rotate, Palm to halt, Point to highlight
- **Voice Commands**: Say "Neuro" followed by your command

## Prerequisites

1. **Ollama** - Install from [ollama.ai](https://ollama.ai)
2. **Node.js 18+** and npm
3. **Python 3.10+**

## Setup

### 1. Install Ollama Models

```bash
ollama pull llama3.1:8b
ollama pull deepseek-coder-v2:16b
ollama pull llava:latest
ollama pull llama3.2:3b
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r ../requirements.txt
playwright install chromium
```

### 4. Start NeuroSurf

**Windows:**
```bash
run.bat
```

**Unix/Mac:**
```bash
chmod +x run.sh
./run.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
npm run dev
```

## Usage

### Voice Commands
- Say **"Neuro"** to activate voice listening
- Then speak your command: *"Search for AI news"*, *"Go to GitHub"*, etc.

### Gestures
- **Pinch** (👌): Rotate the 3D scene
- **Open Palm** (✋): Emergency HALT - stops all agent processes
- **Point** (☝️): Highlight elements on page

### Keyboard Shortcuts
- `Ctrl+Shift+V`: Toggle voice listening
- `Escape`: Halt agent

## Architecture

```
├── electron/          # Electron main process
├── src/               # React frontend
│   ├── components/    # 3D Scene, Neural Halo, etc.
│   ├── input/         # Gesture & Voice controllers
│   ├── services/      # Socket connection
│   └── store/         # Zustand state management
├── backend/           # Python FastAPI + Socket.IO
│   ├── main.py        # Server entry
│   ├── swarm_router.py # Model management
│   └── memory.py      # ChromaDB integration
└── agent/             # Browser automation
    ├── browser_agent.py
    ├── vision_helper.py
    └── task_planner.py
```

## Configuration

Edit model assignments in `backend/swarm_router.py`:

```python
DEFAULT_MODELS = {
    ModelRole.EXECUTIVE: ModelConfig(
        name="llama3.1:8b",  # Change to 70b if you have VRAM
        ...
    ),
    ...
}
```

## License

MIT
