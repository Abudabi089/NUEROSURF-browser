# NeuroSurf Browser

**NeuroSurf** is a local-first, agentic web browser with a high-fidelity 3D spatial interface. It features a powerful autonomous agent designed to handle research, navigation, and system tasks locally.

![NeuroSurf](./public/neuro.svg)

## 🧠 Intelligence Engine

The browser is powered by a high-performance, local LLM optimized for consumer-grade hardware (ideal for Intel Core i5/i7/i9 systems):

- **Primary Engine**: `qwen2.5:3b` via Ollama.
- **Reasoning**: Focused on fast, concise tool-calling and agentic loops.
- **Optimization**: Configured for low-latency response times on CPU (Intel Iris Xe / i5-13th gen compatible).

## ✨ Features

- **Autonomous Agent**: A continuous reasoning loop with access to the following tools:
  - **Terminal**: Run shell commands directly from the browser.
  - **File System**: Read, write, and modify local files.
  - **Web Research**: Automated searching and scraping with structured reporting.
  - **PDF Generation**: Automatically compile research findings into formatted PDF documents.
  - **Browser Automation**: Control tabs, navigate the web, and interact with page content.
- **3D Spatial Interface**: 
  - **Spatial Tabs**: Navigate open pages in a 3D planetary system layout.
  - **Holo-History Tunnel**: A spiral visualization of your browsing history in 3D.
  - **Thought Stream**: Energy beams that visually connect agent thoughts to their actions.
  - **Neural Halo**: A reactive UI ring indicating the agent's current state (Idle, Planning, Acting, etc.).
- **Immersive Modes**:
  - **Zen Mode**: A focused environment with an integrated lo-fi music engine.
  - **Phase 12**: Advanced 3D visualization and "glitch" aesthetic enhancements.
- **Privacy & Memory**: 
  - Local **ChromaDB** episodic memory.
  - Optional **Supermemory.ai** integration for extended semantic context.

## 🚀 Setup

### 1. Prerequisites
- **Ollama**: Download from [ollama.com](https://ollama.com)
- **Node.js**: 18+
- **Python**: 3.10+

### 2. Pull Intelligence Model
```bash
ollama pull qwen2.5:3b
```

### 3. Installation
```bash
# Install Frontend
npm install

# Install Backend
pip install -r requirements.txt
playwright install chromium
```

### 4. Running
- **Windows**: Run `run.bat` or `NeuroSurf_Launcher.bat`.
- **Manual**: 
  - Terminal 1: `python backend/main.py`
  - Terminal 2: `npm run dev`

## 📂 Project Structure
- `src/`: React + Three.js interface and components.
- `backend/`: FastAPI agent server and tool implementations.
- `agent/`: Specialized automation scripts and Chrome MCP.
- `data/`: Local storage for memory and generated reports.

## 📝 License
MIT
