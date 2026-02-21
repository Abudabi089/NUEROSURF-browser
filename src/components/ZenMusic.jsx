import React, { useState, useEffect } from 'react';
import useStore from '../store/useStore';
import useDraggable from '../hooks/useDraggable';

const ZenMusic = () => {
    const zenMode = useStore((state) => state.zenMode);
    const playlist = useStore((state) => state.zenPlaylist);
    const [randomIndex, setRandomIndex] = useState(0);
    const [isEditing, setIsEditing] = useState(false);
    const [tempPlaylist, setTempPlaylist] = useState(playlist.join('\n'));

    // Handle initial shuffle on mount and when zenMode is toggled
    useEffect(() => {
        if (zenMode) {
            handleShuffle();
        }
    }, [zenMode]);

    const { position, onMouseDown } = useDraggable({ x: 20, y: window.innerHeight - 320 }, 'neuro_zen_pos');

    const handleShuffle = () => {
        // Pick a random index between 1 and 100 for the playlist start
        setRandomIndex(Math.floor(Math.random() * 100) + 1);
    };

    const handleSave = () => {
        const newPlaylist = tempPlaylist.split('\n').map(s => s.trim()).filter(s => s.length > 0);
        useStore.getState().setZenPlaylist(newPlaylist);
        setIsEditing(false);
    };

    if (!zenMode) return null;

    const currentId = playlist[0]; // Currently just taking the first one if it's a playlist list

    return (
        <div style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            width: 340,
            background: 'rgba(5, 5, 10, 0.7)',
            border: '1px solid rgba(157, 78, 221, 0.4)',
            borderRadius: 20,
            padding: '20px',
            zIndex: 10000,
            backdropFilter: 'blur(15px) saturate(180%)',
            boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(157, 78, 221, 0.1)',
            color: 'white',
            fontFamily: "'Rajdhani', sans-serif",
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
            {/* Header / Handle */}
            <div
                onMouseDown={onMouseDown}
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 15,
                    alignItems: 'center',
                    cursor: 'move',
                    userSelect: 'none'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                        width: 8,
                        height: 8,
                        background: 'var(--neural-purple)',
                        borderRadius: '50%',
                        boxShadow: '0 0 10px var(--neural-purple)',
                        animation: 'pulse 2s infinite'
                    }} />
                    <span style={{
                        fontSize: 14,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 2,
                        color: 'rgba(255,255,255,0.9)',
                        textShadow: '0 0 10px rgba(157, 78, 221, 0.5)'
                    }}>
                        Zen Stream
                    </span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    <button
                        onClick={() => setIsEditing(!isEditing)}
                        style={{
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: '#aaa',
                            cursor: 'pointer',
                            fontSize: 10,
                            padding: '4px 8px',
                            borderRadius: 6,
                            transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => { e.target.style.background = 'rgba(255,255,255,0.1)'; e.target.style.color = 'white'; }}
                        onMouseOut={(e) => { e.target.style.background = 'rgba(255,255,255,0.05)'; e.target.style.color = '#aaa'; }}
                    >
                        {isEditing ? 'EXIT' : 'CONFIG'}
                    </button>
                </div>
            </div>

            {isEditing ? (
                <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                    <textarea
                        value={tempPlaylist}
                        onChange={(e) => setTempPlaylist(e.target.value)}
                        placeholder="Youtube ID or Playlist ID..."
                        style={{
                            width: '100%',
                            height: 120,
                            background: 'rgba(0, 0, 0, 0.4)',
                            border: '1px solid rgba(157, 78, 221, 0.3)',
                            borderRadius: 12,
                            color: 'var(--neural-green)',
                            fontSize: 13,
                            padding: 12,
                            fontFamily: 'monospace',
                            outline: 'none',
                            resize: 'none'
                        }}
                    />
                    <button
                        onClick={handleSave}
                        style={{
                            width: '100%',
                            marginTop: 12,
                            padding: '10px',
                            background: 'linear-gradient(45deg, var(--neural-purple), #7b2cbf)',
                            border: 'none',
                            color: 'white',
                            borderRadius: 10,
                            cursor: 'pointer',
                            fontWeight: 600,
                            letterSpacing: 1,
                            boxShadow: '0 4px 15px rgba(123, 44, 191, 0.4)'
                        }}
                    >
                        SYNC NEURAL LINK
                    </button>
                </div>
            ) : (
                <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                    <div style={{
                        width: '100%',
                        height: 180,
                        borderRadius: 15,
                        overflow: 'hidden',
                        marginBottom: 15,
                        background: '#000',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                        border: '1px solid rgba(255,255,255,0.05)'
                    }}>
                        <iframe
                            width="100%"
                            height="100%"
                            src={currentId.startsWith('PL')
                                ? `https://www.youtube.com/embed/videoseries?list=${currentId}&autoplay=1&index=${randomIndex}`
                                : `https://www.youtube.com/embed/${currentId}?autoplay=1`
                            }
                            title="Zen Player"
                            frameBorder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                        />
                    </div>

                    <div style={{ display: 'flex', gap: 10 }}>
                        <button
                            onClick={handleShuffle}
                            style={{
                                flex: 1,
                                background: 'rgba(157, 78, 221, 0.1)',
                                border: '1px solid rgba(157, 78, 221, 0.3)',
                                color: 'white',
                                padding: '10px',
                                borderRadius: 12,
                                cursor: 'pointer',
                                fontSize: 13,
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 8,
                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.background = 'rgba(157, 78, 221, 0.2)';
                                e.currentTarget.style.borderColor = 'var(--neural-purple)';
                                e.currentTarget.style.transform = 'translateY(-2px)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.background = 'rgba(157, 78, 221, 0.1)';
                                e.currentTarget.style.borderColor = 'rgba(157, 78, 221, 0.3)';
                                e.currentTarget.style.transform = 'translateY(0)';
                            }}
                        >
                            <span>🔀</span> SHUFFLE FLOW
                        </button>
                    </div>
                </div>
            )}

            <style>{`
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 0.8; }
                    50% { transform: scale(1.2); opacity: 1; }
                    100% { transform: scale(1); opacity: 0.8; }
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default ZenMusic;
