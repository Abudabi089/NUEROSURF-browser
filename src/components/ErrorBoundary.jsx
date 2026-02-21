import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ error, errorInfo });
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            console.error("ErrorBoundary caught error:", this.state.error);
            return (
                <div style={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'linear-gradient(135deg, #0a0a15 0%, #1a0a20 100%)',
                    color: '#ff3366',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'Orbitron, monospace',
                    padding: 40,
                    zIndex: 99999
                }}>
                    <h1 style={{ color: '#00d4ff', marginBottom: 20, fontSize: 24 }}>⚠️ NeuroSurf Error</h1>
                    <p style={{ marginBottom: 20, color: '#aaa' }}>Something went wrong. Check console for details.</p>
                    <pre style={{
                        background: 'rgba(255,51,102,0.1)',
                        padding: 20,
                        borderRadius: 8,
                        maxWidth: '80vw',
                        maxHeight: '40vh',
                        overflow: 'auto',
                        border: '1px solid #ff3366',
                        fontSize: 12,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                    }}>
                        {this.state.error?.toString()}
                        {this.state.errorInfo?.componentStack && (
                            <div style={{ marginTop: 10, color: '#888', fontSize: 10 }}>
                                {this.state.errorInfo.componentStack}
                            </div>
                        )}
                    </pre>
                    <button onClick={() => window.location.reload()} style={{
                        marginTop: 20,
                        padding: '12px 24px',
                        background: '#00d4ff',
                        border: 'none',
                        borderRadius: 8,
                        color: '#000',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        fontSize: 14
                    }}>
                        🔄 Reload App
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
