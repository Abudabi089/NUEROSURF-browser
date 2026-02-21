import React, { useEffect, useState, useCallback, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import Scene3D from './components/Scene3D';
import TitleBar from './components/TitleBar';
import BrowserView from './components/BrowserView';
import ThoughtStream from './components/ThoughtStream';
import CommandInput from './components/CommandInput';
import StatusBar from './components/StatusBar';
import GestureController from './input/GestureController';
import VoiceController from './input/VoiceController';
import WebcamController from './input/WebcamController';
import TerminalView from './components/TerminalView';
import FileManager from './components/FileManager';
import socketManager from './services/socketManager';
import useStore from './store/useStore';
import ZenMusic from './components/ZenMusic';
import { useOpalAgent } from './hooks/useOpalAgent';

function App() {
    const viewMode = useStore((state) => state.viewMode);
    const setViewMode = useStore((state) => state.setViewMode);
    const [zoom, setZoom] = useState(1);
    const isConnected = useStore((state) => state.isConnected);
    const setCommandInput = useStore((state) => state.setCommandInput);
    const commandInput = useStore((state) => state.commandInput);
    const addThought = useStore((state) => state.addThought);

    // Research Agent Hook
    const { sendQuery: sendResearchQuery } = useOpalAgent();

    // Connect to backend
    useEffect(() => {
        socketManager.connect();
        return () => socketManager.disconnect();
    }, []);

    // Command submission - handles /research commands and regular commands
    const handleCommandSubmit = useCallback((command) => {
        if (!command.trim()) return;
        setCommandInput('');

        // Handle /research command for 3D holographic cards
        if (command.trim().toLowerCase().startsWith('/research ')) {
            const query = command.trim().slice(10);
            addThought({ text: `🔬 Researching: ${query} — document will open in browser`, type: 'user' });
            sendResearchQuery(query);
            setViewMode('3d');
            return;
        }

        // Handle /analyze manual trigger
        if (command.trim().toLowerCase() === '/analyze') {
            addThought({ text: '🧠 Analyzing current page...', type: 'user' });
            window.dispatchEvent(new CustomEvent('neuro:analyze_page'));
            return;
        }

        // Send to backend - socketManager now handles adding the user thought to the UI
        socketManager.sendCommand(command.trim());
    }, [setCommandInput, addThought, sendResearchQuery, setViewMode]);

    // Gesture handler - do visible actions
    const handleGesture = useCallback((gesture) => {
        const type = gesture.type;

        switch (type) {
            case 'pinch':
                // Zoom in
                setZoom(z => Math.min(z + 0.1, 2));
                addThought({ text: '🔍 Zoom in', type: 'action' });
                break;
            case 'fist':
                // Zoom out
                setZoom(z => Math.max(z - 0.1, 0.5));
                addThought({ text: '🔍 Zoom out', type: 'action' });
                break;
            case 'palm':
                // Stop/Reset
                setZoom(1);
                socketManager.haltAgent();
                addThought({ text: '✋ Reset', type: 'action' });
                break;
            case 'point':
                // Toggle view
                setViewMode(v => v === 'browser' ? '3d' : 'browser');
                addThought({ text: '👆 View toggled', type: 'action' });
                break;
            case 'thumbs_up':
                // Confirm action
                addThought({ text: '👍 Confirmed!', type: 'action' });
                break;
        }
    }, [addThought]);

    const zenMode = useStore((state) => state.zenMode);
    const setZenMode = useStore((state) => state.setZenMode);
    const phase12 = useStore((state) => state.phase12);
    const setPhase12 = useStore((state) => state.setPhase12);
    const webcamEnabled = useStore((state) => state.webcamEnabled);
    const setWebcamEnabled = useStore((state) => state.setWebcamEnabled);
    const gesturesEnabled = useStore((state) => state.gesturesEnabled);
    const setGesturesEnabled = useStore((state) => state.setGesturesEnabled);

    // Terminal & File Manager visibility
    const [showTerminal, setShowTerminal] = useState(false);
    const [showFileManager, setShowFileManager] = useState(false);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                socketManager.haltAgent();
            }
            if (e.key === 'F2' || (e.key.toLowerCase() === 't' && !e.ctrlKey && !e.altKey && !e.metaKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
                setViewMode(v => v === 'browser' ? '3d' : 'browser');
            }
            if (e.key === 'F3') {
                setShowTerminal(t => !t);
            }
            if (e.key === 'F4') {
                setShowFileManager(f => !f);
            }
            if (e.key === 'F6') {
                const orbit = useStore.getState().orbitEnabled;
                useStore.getState().setOrbitEnabled(!orbit);
                addThought({ text: orbit ? 'Orbital Rotation Paused' : 'Orbital Rotation Resumed', type: 'system' });
            }
            if (e.key === 'F7') {
                setGesturesEnabled(!gesturesEnabled);
                addThought({ text: gesturesEnabled ? 'Gestures Disabled' : 'Gestures Enabled', type: 'system' });
            }
            if (e.key === 'F8') {
                setZenMode(!zenMode);
            }
            if (e.key === 'F9') {
                setWebcamEnabled(!webcamEnabled);
            }
            if (e.key === 'F12') {
                setPhase12(!phase12);
                addThought({ text: phase12 ? 'Phase 12 Deactivated' : 'Phase 12 Initiated', type: 'system' });
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [zenMode, setZenMode, phase12, setPhase12, addThought, webcamEnabled, setWebcamEnabled, gesturesEnabled, setGesturesEnabled, setViewMode]);

    // DEBUG: Log viewMode changes
    useEffect(() => {
        console.log('👀 VIEW MODE CHANGED:', viewMode);
    }, [viewMode]);

    return (
        <div className="app-main" style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            overflow: 'hidden',
            background: 'var(--bg-primary, #0a0a0f)'
        }}>
            {/* Debug: Visibility Indicator - proves app is rendering */}
            <div style={{
                position: 'fixed',
                top: 40,
                left: 10,
                color: 'lime',
                fontSize: 10,
                fontFamily: 'monospace',
                zIndex: 99998,
                pointerEvents: 'none',
                opacity: 0.6,
                textShadow: '0 0 5px lime'
            }}>
                🟢 NeuroSurf | Mode: {viewMode} | Connected: {isConnected ? '✓' : '✗'}
            </div>

            {/* Zen Mode Music Player */}
            {zenMode && <ZenMusic />}

            {/* --- FIXED UI LAYER (No Zoom) --- */}
            {!zenMode && <TitleBar viewMode={viewMode} onToggleView={() => setViewMode(v => v === 'browser' ? '3d' : 'browser')} />}

            {/* Thought Stream - Force exact position */}
            <ThoughtStream />

            <CommandInput value={commandInput} onChange={setCommandInput} onSubmit={handleCommandSubmit} />
            {!zenMode && <StatusBar connected={isConnected} viewMode={viewMode} />}

            <GestureController enabled={gesturesEnabled} onGesture={handleGesture} />
            <VoiceController enabled={true} />
            <WebcamController enabled={webcamEnabled} />

            {/* Zen Exit Hint */}
            {zenMode && (
                <div style={{
                    position: 'fixed', bottom: 20, left: '50%', transform: 'translateX(-50%)',
                    color: 'rgba(255,255,255,0.3)', fontSize: 12, pointerEvents: 'none', zIndex: 9999
                }}>
                    Press F8 to Exit Focus
                </div>
            )}

            {/* --- 3D VIEW --- */}
            {(viewMode === '3d' || zenMode) && (
                <div style={{
                    position: 'fixed',
                    top: zenMode ? 0 : 32,
                    left: 0,
                    width: zenMode ? '100vw' : 'calc(100vw - 350px)',
                    height: zenMode ? '100vh' : 'calc(100vh - 112px)',
                    zIndex: 500,
                    background: 'radial-gradient(ellipse at center, #0a0a1a 0%, #000000 100%)'
                }}>
                    <Canvas
                        camera={{ position: [0, 2, 12], fov: 50 }}
                        style={{ width: '100%', height: '100%' }}
                        gl={{ antialias: true, alpha: true }}
                        dpr={[1, 2]}
                        onCreated={({ gl }) => {
                            gl.setClearColor('#000000', 1);
                        }}
                    >
                        <Suspense fallback={null}>
                            <Scene3D />
                        </Suspense>
                    </Canvas>

                    {/* 3D Mode Indicator */}
                    <div style={{
                        position: 'absolute',
                        bottom: 10,
                        left: 10,
                        color: 'rgba(0, 212, 255, 0.6)',
                        fontSize: 11,
                        fontFamily: 'Orbitron, monospace',
                        pointerEvents: 'none',
                        textShadow: '0 0 10px rgba(0, 212, 255, 0.5)'
                    }}>
                        🎮 3D VIEW | F2 Toggle | Drag to orbit | Scroll to zoom
                    </div>
                </div>
            )}

            {/* --- ZOOMABLE CONTENT LAYER (Only visible in Browser mode) --- */}
            {viewMode === 'browser' && (
                <div className="content-layer" style={{
                    width: '100%', height: '100%',
                    transform: zoom !== 1 ? `scale(${zoom})` : 'none',
                    transformOrigin: 'center center',
                    transition: 'opacity 1s ease',
                    zIndex: 1
                }}>
                    <BrowserView />
                </div>
            )}

            {/* Terminal View (F3 to toggle) */}
            {showTerminal && <TerminalView socket={socketManager.socket} />}

            {/* File Manager (F4 to toggle) */}
            {showFileManager && <FileManager socket={socketManager.socket} />}

        </div>
    );
}

export default App;
