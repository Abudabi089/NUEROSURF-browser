import React, { useState, useEffect } from 'react';

/**
 * FileManager - File System Access UI
 * Connects to the backend fs_list, fs_read, fs_write socket events.
 */
function FileManager({ socket }) {
    const [currentPath, setCurrentPath] = useState('.');
    const [items, setItems] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!socket) {
            setError('Not connected to backend');
            return;
        }

        const handleList = (data) => {
            console.log('FS List Result:', data);
            setCurrentPath(data.path);
            setItems(data.items || []);
        };
        const handleRead = (data) => {
            setFileContent(data.content);
            setSelectedFile(data.path);
        };
        const handleError = (data) => {
            setError(data.message);
            setTimeout(() => setError(null), 3000);
        };

        socket.on('fs:list_result', handleList);
        socket.on('fs:read_result', handleRead);
        socket.on('fs:error', handleError);

        // Initial load - use full path to ensure it works
        if (socket.connected) {
            socket.emit('fs_list', { path: 'C:\\Users\\Abhyudaya saxena\\Downloads\\Antigravity Nuerosurf' });
        }

        return () => {
            socket.off('fs:list_result', handleList);
            socket.off('fs:read_result', handleRead);
            socket.off('fs:error', handleError);
        };
    }, [socket]);

    const navigateTo = (item) => {
        if (item.isDir) {
            socket.emit('fs_list', { path: `${currentPath}/${item.name}` });
        } else {
            socket.emit('fs_read', { path: `${currentPath}/${item.name}` });
        }
    };

    const goUp = () => {
        const parent = currentPath.split('/').slice(0, -1).join('/') || '.';
        socket.emit('fs_list', { path: parent });
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <span style={styles.title}>📁 FILE MANAGER</span>
                <span style={styles.path}>{currentPath}</span>
            </div>

            {error && <div style={styles.error}>{error}</div>}

            <div style={styles.fileList}>
                <div style={styles.item} onClick={goUp}>📂 ..</div>
                {items.map((item, i) => (
                    <div key={i} style={styles.item} onClick={() => navigateTo(item)}>
                        {item.isDir ? '📁' : '📄'} {item.name}
                        {!item.isDir && <span style={styles.size}>{(item.size / 1024).toFixed(1)}KB</span>}
                    </div>
                ))}
            </div>

            {selectedFile && (
                <div style={styles.preview}>
                    <div style={styles.previewHeader}>{selectedFile}</div>
                    <pre style={styles.previewContent}>{fileContent.slice(0, 2000)}</pre>
                </div>
            )}
        </div>
    );
}

const styles = {
    container: {
        position: 'fixed',
        bottom: 100,
        right: 370,
        width: 400,
        height: 350,
        background: 'rgba(10, 10, 20, 0.95)',
        border: '1px solid #ffd700',
        borderRadius: 12,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 9000,
        fontFamily: 'Consolas, monospace',
        fontSize: 12,
        boxShadow: '0 0 30px rgba(255, 215, 0, 0.2)'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255, 215, 0, 0.3)',
        background: 'rgba(0, 0, 0, 0.5)'
    },
    title: {
        color: '#ffd700',
        fontWeight: 'bold'
    },
    path: {
        color: 'rgba(255,255,255,0.5)',
        fontSize: 10,
        maxWidth: 200,
        overflow: 'hidden',
        textOverflow: 'ellipsis'
    },
    error: {
        background: 'rgba(255, 0, 0, 0.2)',
        color: '#ff6666',
        padding: '8px 12px',
        textAlign: 'center'
    },
    fileList: {
        flex: 1,
        overflowY: 'auto',
        padding: 8
    },
    item: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '6px 10px',
        cursor: 'pointer',
        borderRadius: 4,
        color: '#ffffff',
        transition: 'background 0.2s'
    },
    size: {
        color: 'rgba(255,255,255,0.4)',
        marginLeft: 10
    },
    preview: {
        borderTop: '1px solid rgba(255, 215, 0, 0.3)',
        maxHeight: 150,
        overflow: 'hidden'
    },
    previewHeader: {
        padding: '6px 12px',
        background: 'rgba(0,0,0,0.5)',
        color: '#ffd700',
        fontSize: 10
    },
    previewContent: {
        padding: 12,
        margin: 0,
        color: '#aaaaaa',
        fontSize: 10,
        overflowY: 'auto',
        maxHeight: 100
    }
};

export default FileManager;
