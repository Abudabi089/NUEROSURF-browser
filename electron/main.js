const electron = require('electron');
if (typeof electron === 'string') {
    console.error('FATAL ERROR: [main.js] require("electron") returned a string instead of an object.');
    console.error('Path returned:', electron);
    console.error('This usually happens when ELECTRON_RUN_AS_NODE is set.');
    console.error('Check your launch environment.');
    process.exit(1);
}
const { app, BrowserWindow, ipcMain, session } = electron;
const path = require('path');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow = null;

// Safely determine dev mode
let isDev = false;
try {
    isDev = process.env.NODE_ENV !== 'production' && !fs.existsSync(path.join(__dirname, '../dist/index.html'));
} catch (e) {
    console.warn('Could not determine dev mode, defaulting to production:', e.message);
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1600,
        height: 900,
        minWidth: 1280,
        minHeight: 720,
        frame: false,
        backgroundColor: '#0a0a0f',
        webPreferences: {
            nodeIntegration: false, // Security: keep false
            contextIsolation: true,  // Security: keep true
            preload: path.join(__dirname, 'preload.js'),
            webviewTag: true,        // Required for <webview>
            sandbox: false           // Required for some media access in older Electron
        },
        icon: path.join(__dirname, '../public/icon.png'),
        title: 'NeuroSurf',
        show: false
    });

    // --- CRITICAL: Grant Camera & Microphone Permissions ---
    mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
        if (permission === 'media' || permission === 'video_capture' || permission === 'audio_capture') {
            return true;
        }
        return false;
    });

    mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
        if (permission === 'media' || permission === 'video_capture' || permission === 'audio_capture') {
            callback(true);
        } else {
            callback(false);
        }
    });

    if (isDev) {
        console.log('Loading dev URL: http://localhost:3333');
        mainWindow.loadURL('http://localhost:3333');
        // mainWindow.webContents.openDevTools({ mode: 'detach' });
    } else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        mainWindow.focus();
    });

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error(`Failed to load: ${errorDescription} (${errorCode})`);
        if (isDev && (errorCode === -102 || errorCode === -105)) {
            console.log('Retrying load in 2s...');
            setTimeout(() => {
                mainWindow.loadURL('http://localhost:3333');
            }, 2000);
        }
    });

    // Handle new window requests (open in default browser or webview logic)
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        return { action: 'allow' };
    });
}

app.whenReady().then(() => {
    // Also set permissions on default session just in case
    session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
        return (permission === 'media' || permission === 'video_capture' || permission === 'audio_capture');
    });

    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
        if (permission === 'media' || permission === 'video_capture' || permission === 'audio_capture') {
            callback(true);
        } else {
            callback(false);
        }
    });

    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Window controls
ipcMain.on('window-minimize', () => mainWindow?.minimize());
ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize();
    else mainWindow?.maximize();
});
ipcMain.on('window-close', () => mainWindow?.close());
