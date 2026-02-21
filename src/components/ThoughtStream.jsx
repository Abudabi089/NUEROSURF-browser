import React from 'react';
import useStore from '../store/useStore';

function ThoughtStream() {
    const activeThreadId = useStore((state) => state.activeThreadId);
    const threads = useStore((state) => state.threads);
    const thoughtsMap = useStore((state) => state.thoughts);
    const addThread = useStore((state) => state.addThread);
    const switchThread = useStore((state) => state.switchThread);
    const removeThread = useStore((state) => state.removeThread);

    const activeThoughts = thoughtsMap[activeThreadId] || [];

    const getTypeStyle = (type) => {
        const colors = {
            user: { bg: 'rgba(0, 212, 255, 0.1)', border: 'var(--neural-blue)' },
            system: { bg: 'rgba(0, 255, 136, 0.1)', border: 'var(--neural-green)' },
            action: { bg: 'rgba(255, 215, 0, 0.1)', border: 'var(--neural-gold)' },
            error: { bg: 'rgba(255, 51, 102, 0.1)', border: 'var(--neural-red)' },
            planning: { bg: 'rgba(157, 78, 221, 0.1)', border: 'var(--neural-purple)' }
        };
        return colors[type] || colors.system;
    };

    return (
        <div style={{
            position: 'fixed',
            top: 32,
            right: 0,
            width: 340,
            bottom: 80,
            background: 'rgba(10, 10, 20, 0.98)',
            borderLeft: '1px solid rgba(0, 212, 255, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 2000,
            overflow: 'hidden',
            boxShadow: '-10px 0 30px rgba(0,0,0,0.5)'
        }}>
            {/* Thread Switcher Bar */}
            <div style={{
                display: 'flex',
                background: 'rgba(0,0,0,0.3)',
                overflowX: 'auto',
                borderBottom: '1px solid rgba(0, 212, 255, 0.1)',
                scrollbarWidth: 'none'
            }}>
                {threads.map(thread => (
                    <div
                        key={thread.id}
                        onClick={() => switchThread(thread.id)}
                        style={{
                            padding: '8px 12px',
                            fontSize: 10,
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            color: activeThreadId === thread.id ? 'var(--neural-blue)' : '#888',
                            borderBottom: activeThreadId === thread.id ? '2px solid var(--neural-blue)' : '2px solid transparent',
                            background: activeThreadId === thread.id ? 'rgba(0, 212, 255, 0.05)' : 'transparent',
                            transition: 'all 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6
                        }}
                    >
                        <span>{thread.name}</span>
                        {thread.id !== 'main' && (
                            <span
                                onClick={(e) => { e.stopPropagation(); removeThread(thread.id); }}
                                style={{ opacity: 0.5, fontSize: 12 }}
                            >×</span>
                        )}
                    </div>
                ))}
                <div
                    onClick={() => addThread()}
                    style={{
                        padding: '8px 15px',
                        cursor: 'pointer',
                        color: 'var(--neural-green)',
                        fontSize: 14,
                        fontWeight: 'bold'
                    }}
                >+</div>
            </div>

            {/* Header */}
            <div style={{
                padding: '10px 14px',
                borderBottom: '1px solid rgba(0, 212, 255, 0.2)',
                fontFamily: 'Orbitron, sans-serif',
                fontSize: 11,
                color: 'var(--neural-blue)',
                textTransform: 'uppercase',
                letterSpacing: 2,
                flexShrink: 0,
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                <span>Neural Feed</span>
                <span style={{ fontSize: 9, opacity: 0.6 }}>ID: {activeThreadId.slice(-4)}</span>
            </div>

            {/* Messages - scrollable */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: 10
            }}>
                {activeThoughts.length === 0 ? (
                    <div style={{ color: '#666', fontSize: 12, textAlign: 'center', padding: 40, fontFamily: 'monospace' }}>
                        &gt; NEURAL_LINK_ESTABLISHED<br />
                        &gt; READY_FOR_COMMAND
                    </div>
                ) : (
                    [...activeThoughts].reverse().map((thought) => {
                        const style = getTypeStyle(thought.type);
                        return (
                            <div
                                key={thought.id}
                                style={{
                                    marginBottom: 10,
                                    padding: '10px 12px',
                                    background: style.bg,
                                    borderLeft: `3px solid ${style.border}`,
                                    borderRadius: '0 4px 4px 0',
                                    fontSize: 12,
                                    color: '#eee',
                                    lineHeight: 1.5,
                                    wordWrap: 'break-word',
                                    boxShadow: '2px 2px 10px rgba(0,0,0,0.2)'
                                }}
                            >
                                {thought.text}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default ThoughtStream;
