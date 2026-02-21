import React, { useState, useEffect, useRef } from 'react';

/**
 * TerminalView - Interactive Terminal Component
 * Connects to the backend terminal_command socket event.
 */
function TerminalView({ socket }) {
    const [input, setInput] = useState('');
    const [output, setOutput] = useState([
        { type: 'system', text: '🐚 NeuroSurf Terminal Ready. Type commands below.' }
    ]);
    const outputRef = useRef(null);

    useEffect(() => {
        if (!socket) return;

        const handleOutput = (data) => {
            setOutput(prev => [...prev, { type: 'output', text: data.output }]);
        };

        socket.on('terminal:output', handleOutput);
        return () => socket.off('terminal:output', handleOutput);
    }, [socket]);

    useEffect(() => {
        // Auto-scroll to bottom
        if (outputRef.current) {
            outputRef.current.scrollTop = outputRef.current.scrollHeight;
        }
    }, [output]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        if (!socket || !socket.connected) {
            setOutput(prev => [...prev, { type: 'error', text: 'Error: Not connected to backend' }]);
            return;
        }

        setOutput(prev => [...prev, { type: 'command', text: `> ${input}` }]);
        socket.emit('terminal_command', { command: input });
        setInput('');
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <span style={styles.title}>🖥️ TERMINAL</span>
                <span style={styles.hint}>Ctrl+Shift+T to toggle</span>
            </div>
            <div ref={outputRef} style={styles.output}>
                {output.map((line, i) => (
                    <div key={i} style={{
                        ...styles.line,
                        color: line.type === 'command' ? '#00ff88' :
                            line.type === 'system' ? '#ffd700' : '#ffffff'
                    }}>
                        {line.text}
                    </div>
                ))}
            </div>
            <form onSubmit={handleSubmit} style={styles.inputForm}>
                <span style={styles.prompt}>❯</span>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter command..."
                    style={styles.input}
                    autoFocus
                />
            </form>
        </div>
    );
}

const styles = {
    container: {
        position: 'fixed',
        bottom: 100,
        left: 20,
        width: 500,
        height: 300,
        background: 'rgba(10, 10, 20, 0.95)',
        border: '1px solid #00d4ff',
        borderRadius: 12,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 9000,
        fontFamily: 'Consolas, monospace',
        fontSize: 13,
        boxShadow: '0 0 30px rgba(0, 212, 255, 0.3)'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid rgba(0, 212, 255, 0.3)',
        background: 'rgba(0, 0, 0, 0.5)'
    },
    title: {
        color: '#00d4ff',
        fontWeight: 'bold',
        letterSpacing: 1
    },
    hint: {
        color: 'rgba(255,255,255,0.3)',
        fontSize: 10
    },
    output: {
        flex: 1,
        overflowY: 'auto',
        padding: 12,
        color: '#ffffff'
    },
    line: {
        marginBottom: 4,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all'
    },
    inputForm: {
        display: 'flex',
        alignItems: 'center',
        padding: '8px 12px',
        borderTop: '1px solid rgba(0, 212, 255, 0.3)',
        background: 'rgba(0, 0, 0, 0.5)'
    },
    prompt: {
        color: '#00ff88',
        marginRight: 8
    },
    input: {
        flex: 1,
        background: 'transparent',
        border: 'none',
        outline: 'none',
        color: '#ffffff',
        fontFamily: 'inherit',
        fontSize: 'inherit'
    }
};

export default TerminalView;
