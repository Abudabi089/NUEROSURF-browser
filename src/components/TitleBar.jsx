import React from 'react';

function TitleBar({ viewMode, onToggleView }) {
    const handleMinimize = () => window.electronAPI?.minimizeWindow();
    const handleMaximize = () => window.electronAPI?.maximizeWindow();
    const handleClose = () => window.electronAPI?.closeWindow();

    return (
        <div className="title-bar">
            <div className="title-bar__logo">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                    <circle cx="12" cy="12" r="4" fill="currentColor" />
                </svg>
                <span>NeuroSurf</span>
            </div>

            {/* View Toggle Button */}
            <button
                onClick={onToggleView}
                style={{
                    marginLeft: 'auto',
                    marginRight: 16,
                    background: 'rgba(0, 212, 255, 0.1)',
                    border: '1px solid var(--neural-blue)',
                    color: 'var(--neural-blue)',
                    padding: '4px 16px',
                    borderRadius: 4,
                    fontSize: 11,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-display)',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                    WebkitAppRegion: 'no-drag'
                }}
            >
                {viewMode === 'browser' ? '🌐 Browser' : '🎮 3D Mode'} (F2)
            </button>

            <div className="title-bar__controls">
                <button className="title-bar__btn" onClick={handleMinimize} title="Minimize">─</button>
                <button className="title-bar__btn" onClick={handleMaximize} title="Maximize">□</button>
                <button className="title-bar__btn title-bar__btn--close" onClick={handleClose} title="Close">✕</button>
            </div>
        </div>
    );
}

export default TitleBar;
