const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Window controls
    minimizeWindow: () => ipcRenderer.send('window-minimize'),
    maximizeWindow: () => ipcRenderer.send('window-maximize'),
    closeWindow: () => ipcRenderer.send('window-close'),

    // Platform info
    getPlatform: () => ipcRenderer.invoke('get-platform'),

    // Agent communication
    onAgentMessage: (callback) => {
        ipcRenderer.on('agent-message', (event, data) => callback(data));
    },

    // Voice activation
    onVoiceActivated: (callback) => {
        ipcRenderer.on('voice-activated', (event, data) => callback(data));
    }
});

// Expose versions
contextBridge.exposeInMainWorld('versions', {
    node: () => process.versions.node,
    chrome: () => process.versions.chrome,
    electron: () => process.versions.electron
});
