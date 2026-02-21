import { io } from 'socket.io-client';
import useStore from '../store/useStore';
import voiceSynth from './voiceSynth';

const BACKEND_URL = 'http://localhost:8000';

class SocketManager {
    constructor() {
        this.socket = null;
    }

    connect() {
        if (this.socket?.connected) return;

        this.socket = io(BACKEND_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true
        });

        // Initialize voice on connect
        voiceSynth.init();

        this.setupEventHandlers();
        return this.socket;
    }

    setupEventHandlers() {
        const store = useStore.getState();

        this.socket.on('connect', () => {
            console.log('[Socket] Connected to Neuro!');
            store.setConnected(true);
            const welcome = 'Connected to Neuro. Neural link active.';
            store.addThought({ text: welcome, type: 'system' });
            voiceSynth.speak(welcome);
        });

        this.socket.on('disconnect', () => {
            store.setConnected(false);
            store.addThought({ text: '❌ Disconnected from Neuro', type: 'error' });
        });

        // Agent thoughts and planning
        this.socket.on('agent:thought', (data) => {
            store.addThought({
                id: data.id,
                text: data.text,
                type: data.type,
                thread_id: data.thread_id
            });
            // Speak only final responses or important updates
            const isVoiceEnabled = useStore.getState().voiceEnabled;
            if (isVoiceEnabled && (data.type === 'system' || data.type === 'action')) {
                voiceSynth.speak(data.text);
            }
        });

        this.socket.on('agent:thought_chunk', (data) => {
            const thoughts = useStore.getState().thoughts;
            const threadThoughts = thoughts[data.thread_id || 'main'] || [];
            const thought = threadThoughts.find(t => t.id === data.id);
            if (thought) {
                store.updateThought(data.id, thought.text + data.chunk, data.thread_id);
            } else {
                // If we missed the initial thought block, create it
                store.addThought({ id: data.id, text: data.chunk, type: data.type, thread_id: data.thread_id });
            }
        });

        // Agent state changes
        this.socket.on('agent:state', (data) => {
            console.log('[Socket] Agent state:', data.state);
            store.setAgentState?.(data.state);
        });

        // Agent actions/tool use
        this.socket.on('agent:actions', (data) => {
            console.log('[Socket] Agent actions:', data.actions);
            store.setAgentActions?.(data.actions);
        });

        // Agent tool results
        this.socket.on('agent:tool_result', (data) => {
            console.log('[Socket] Tool result:', data);
            if (data.error) {
                store.addThought({ text: `❌ Tool error: ${data.error}`, type: 'error' });
            }
        });

        // Browser navigation from Neuro
        this.socket.on('browser_navigate', (data) => {
            console.log('[Socket] Navigating to:', data.url);
            store.setBrowserUrl(data.url);
        });

        this.socket.on('browser:new_tab', (data) => {
            console.log('[Socket] Opening new tab:', data);
            store.addTab?.(data.url);
            store.addThought({ text: `🌐 Opening new tab: ${data.url}`, type: 'action' });
        });



        // Voice events
        this.socket.on('voice:stop', () => {
            store.setListening(false);
        });

        // Terminal output
        this.socket.on('terminal:output', (data) => {
            console.log('[Socket] Terminal output:', data);
            store.addTerminalOutput?.(data.output);
        });

        // File system events
        this.socket.on('fs:list_result', (data) => {
            console.log('[Socket] FS list:', data);
            store.setFileList?.(data);
        });

        this.socket.on('fs:read_result', (data) => {
            console.log('[Socket] FS read:', data);
            store.setFileContent?.(data);
        });

        this.socket.on('fs:write_result', (data) => {
            console.log('[Socket] FS write:', data);
            store.addThought({ text: `✅ File saved: ${data.path}`, type: 'action' });
        });

        this.socket.on('fs:error', (data) => {
            console.error('[Socket] FS error:', data);
            store.addThought({ text: `❌ File error: ${data.message}`, type: 'error' });
        });

        // Screenshot request from agent
        this.socket.on('screenshot:request', async () => {
            console.log('[Socket] Screenshot requested by agent');
            await this.captureAndSendScreenshot();
        });
    }

    // --- Commands ---

    sendCommand(command, silent = false) {
        if (!this.socket?.connected) return false;
        const thread_id = useStore.getState().activeThreadId;
        // Optionally skip adding user thought for internal/automated commands
        if (!silent) {
            useStore.getState().addThought({ text: command, type: 'user', thread_id });
        }
        this.socket.emit('agent_command', { command, thread_id });
        return true;
    }

    sendGesture(gesture) {
        if (!this.socket?.connected) return false;
        this.socket.emit('gesture_event', gesture);
        return true;
    }

    haltAgent() {
        if (!this.socket?.connected) return false;
        const thread_id = useStore.getState().activeThreadId;
        this.socket.emit('agent_command', { command: 'halt', thread_id });
        useStore.getState().addThought({ text: '🛑 Halting agent...', type: 'system', thread_id });
        return true;
    }

    analyzePage(text) {
        if (!this.socket?.connected) return false;
        this.socket.emit('analyze_page', { text });
        return true;
    }

    sendWebcamFrame(frame) {
        if (!this.socket?.connected) return false;
        this.socket.emit('webcam:frame', { frame });
        return true;
    }

    startVoice() {
        if (!this.socket?.connected) return false;
        this.socket.emit('voice_start');
        useStore.getState().setListening(true);
        return true;
    }

    stopVoice() {
        if (!this.socket?.connected) return false;
        this.socket.emit('voice_stop');
        useStore.getState().setListening(false);
        return true;
    }

    // --- Agent Tools ---

    executeTool(toolName, parameters = {}) {
        if (!this.socket?.connected) return false;
        this.socket.emit('agent_tool', { tool: toolName, parameters });
        return true;
    }

    // --- Terminal & File System ---

    sendTerminalCommand(command) {
        if (!this.socket?.connected) return false;
        this.socket.emit('terminal_command', { command });
        return true;
    }

    listDirectory(path) {
        if (!this.socket?.connected) return false;
        this.socket.emit('fs_list', { path });
        return true;
    }

    readFile(path) {
        if (!this.socket?.connected) return false;
        this.socket.emit('fs_read', { path });
        return true;
    }

    writeFile(path, content) {
        if (!this.socket?.connected) return false;
        this.socket.emit('fs_write', { path, content });
        return true;
    }

    // --- Screenshot ---

    async captureAndSendScreenshot() {
        if (!this.socket?.connected) return false;

        try {
            // Use Electron's desktopCapturer if available
            if (window.electronAPI?.captureScreen) {
                const imageData = await window.electronAPI.captureScreen();
                this.socket.emit('screenshot_data', { image: imageData });
                return true;
            }

            // Fallback: capture current webview if possible
            console.log('[Socket] Screenshot capture not available from frontend');
            return false;
        } catch (error) {
            console.error('[Socket] Screenshot capture error:', error);
            return false;
        }
    }

    sendScreenshot(imageData) {
        if (!this.socket?.connected) return false;
        this.socket.emit('screenshot_data', { image: imageData });
        return true;
    }


    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }
}

const socketManager = new SocketManager();
export default socketManager;
