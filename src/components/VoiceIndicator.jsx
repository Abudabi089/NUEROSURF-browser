import React from 'react';

function VoiceIndicator({ active }) {
    return (
        <div className={`voice-indicator ${active ? 'voice-indicator--active' : ''}`}>
            <div className="voice-indicator__waves">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="voice-indicator__wave" />
                ))}
            </div>
            <div className="voice-indicator__text">Listening...</div>
        </div>
    );
}

export default VoiceIndicator;
