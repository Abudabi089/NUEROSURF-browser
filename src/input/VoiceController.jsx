import React, { useEffect, useState, useCallback } from 'react';
import socketManager from '../services/socketManager';
import useStore from '../store/useStore';

/**
 * VoiceController - Triggers backend speech recognition
 * No longer uses browser Web Speech API directly to avoid network errors
 */
function VoiceController({ enabled = true }) {
    const isListening = useStore((state) => state.isListening);
    const setListening = useStore((state) => state.setListening);

    // Update state from socket events
    useEffect(() => {
        const socket = socketManager.socket;
        if (!socket) return;

        const onVoiceStop = () => {
            setListening(false);
        };

        socket.on('voice:stop', onVoiceStop);
        return () => socket.off('voice:stop', onVoiceStop);
    }, [setListening]);

    const toggleListening = useCallback(() => {
        if (isListening) {
            socketManager.stopVoice();
        } else {
            socketManager.startVoice();
        }
    }, [isListening]);

    // Keyboard shortcut: Ctrl+Shift+T
    useEffect(() => {
        const handleKey = (e) => {
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 't') {
                e.preventDefault();
                toggleListening();
            }
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [toggleListening]);

    return (
        <>
            <button
                onClick={toggleListening}
                style={{
                    position: 'fixed',
                    bottom: 100,
                    right: 20,
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                    border: `2px solid ${isListening ? 'var(--neural-purple)' : 'var(--neural-blue)'}`,
                    background: isListening ? 'rgba(157, 78, 221, 0.3)' : 'rgba(0, 212, 255, 0.1)',
                    color: isListening ? 'var(--neural-purple)' : 'var(--neural-blue)',
                    fontSize: 20,
                    cursor: 'pointer',
                    zIndex: 9000,
                    animation: isListening ? 'pulse 1s infinite' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}
                title="Ctrl+Shift+T to toggle voice"
            >
                🎤
            </button>

            {isListening && (
                <div style={{
                    position: 'fixed',
                    bottom: 55,
                    right: 20,
                    fontSize: 10,
                    color: 'var(--neural-purple)',
                    zIndex: 9000
                }}>
                    Backend Listening...
                </div>
            )}
        </>
    );
}

export default VoiceController;
