require('dotenv').config();
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');

let mainWindow;
let services = {};

async function initializeServices() {
    try {
        console.log('[App] Initializing services...');
        console.log('[App] Services initialized');
        return true;
    } catch (error) {
        console.error('[App] Failed to initialize services:', error);
        return false;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 240,
        height: 60,
        x: 20,
        y: 20,
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
            webSecurity: true
        },
        frame: false,
        resizable: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        minimizable: false,
        maximizable: false,
        hasShadow: false,
        backgroundColor: '#00000000'
    });

    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

    if (process.platform === 'darwin') {
        mainWindow.setVisibleOnAllWorkspaces(true, {
            visibleOnFullScreen: true
        });
        mainWindow.setAlwaysOnTop(true, 'screen-saver');
    }
    if (process.platform === 'win32' || process.platform === 'linux') {
        setInterval(() => {
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.setAlwaysOnTop(true);
            }
        }, 1000);
    }

    mainWindow.on('show', () => {
        if (process.platform === 'darwin') {
            mainWindow.setAlwaysOnTop(true, 'screen-saver');
        } else {
            mainWindow.setAlwaysOnTop(true);
        }
        mainWindow.focus();
    });

    mainWindow.on('blur', () => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.setAlwaysOnTop(true, process.platform === 'darwin' ? 'screen-saver' : 'normal');
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
}

app.whenReady().then(async () => {
    await initializeServices();
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

ipcMain.handle('app:close', () => {
    if (mainWindow) {
        mainWindow.close();
    }
});

module.exports = { mainWindow };