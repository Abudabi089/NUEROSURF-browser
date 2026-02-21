import React from 'react';
import useStore from '../store/useStore';

function StatusBar({ connected, viewMode }) {
    const researchLoading = useStore((state) => state.researchLoading);
    const voiceEnabled = useStore((state) => state.voiceEnabled);
    const setVoiceEnabled = useStore((state) => state.setVoiceEnabled);
    const threads = useStore((state) => state.threads);
    const activeThreadId = useStore((state) => state.activeThreadId);
    const orbitEnabled = useStore((state) => state.orbitEnabled);
    const activeThread = threads.find(t => t.id === activeThreadId);

    return (
        <div className="status-bar">
            <div className="status-bar__left">
                <div className="status-bar__item">
                    <div className={`status-bar__dot ${connected ? '' : 'status-bar__dot--error'}`} />
                    <span>{connected ? 'Neural Link Active' : 'Offline Mode'}</span>
                </div>
                <div className="status-bar__item">
                    <span>Thread: <b style={{ color: 'var(--neural-blue)' }}>{activeThread?.name}</b></span>
                </div>
                <div className="status-bar__item">
                    <span>Mode: {viewMode === 'browser' ? '🌐 Browser' : '🎮 3D'}</span>
                </div>
                <div className="status-bar__item status-bar__item--clickable" onClick={() => setVoiceEnabled(!voiceEnabled)}>
                    <span>Voice: {voiceEnabled ? '🔊 ON' : '🔈 OFF'}</span>
                </div>
                {orbitEnabled === false && (
                    <div className="status-bar__item" style={{ color: 'var(--neural-red)' }}>
                        <span>⏸ Rotation: PAUSED</span>
                    </div>
                )}
                {researchLoading && (
                    <div className="status-bar__item" style={{ color: 'var(--neural-gold)' }}>
                        <span className="status-bar__pulse">🔬 Research Mode Active</span>
                    </div>
                )}
            </div>

            <div className="status-bar__right">
                <div className="status-bar__item">
                    <span>F2: Toggle View</span>
                </div>
                <div className="status-bar__item">
                    <span>F6: Toggle Orbit</span>
                </div>
                <div className="status-bar__item">
                    <span>Ctrl+Shift+T: Command</span>
                </div>
                <div className="status-bar__item">
                    <span>Esc: Halt</span>
                </div>
            </div>
        </div>
    );
}

export default StatusBar;
