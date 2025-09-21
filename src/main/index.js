require('dotenv').config();
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const LiveKitService = require('./services/livekit');
const settingsService = require('./services/settings');
const DesktopCaptureService = require('./services/capture');
const ScreenshotWebSocketServer = require('./services/websocket');
const IPCManager = require('../shared/ipc');
const { IPC_CHANNELS } = require('../shared/constants');

let mainWindow;
let services = {};
let ipcManager;

async function initializeServices() {
    try {
        console.log('[App] Initializing services...');

        services.settings = settingsService;
        await services.settings.initialize();

        const config = services.settings.getLiveKitConfig();
        services.livekit = new LiveKitService();
        services.livekit.config = config;
        const livekitReady = await services.livekit.initialize();

        if (!livekitReady) {
            console.warn('[App] LiveKit service not fully configured');
        }

        // Initialize screen capture services
        console.log('[App] Initializing desktop capture service...');
        services.capture = new DesktopCaptureService();

        console.log('[App] Initializing screenshot WebSocket server...');
        services.websocketServer = new ScreenshotWebSocketServer(services.capture);
        services.websocketServer.start();

        services.mainWindow = mainWindow;

        ipcManager = new IPCManager(ipcMain, services);
        ipcManager.setupHandlers();

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
            preload: path.join(__dirname, '../renderer/preload.js'),
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

app.on('before-quit', () => {
    console.log('[App] Application shutting down...');

    // Clean up services
    if (services.websocketServer) {
        services.websocketServer.stop();
    }

    if (services.capture) {
        services.capture.destroy();
    }

    if (services.livekit) {
        services.livekit.stopSession();
    }

    if (ipcManager) {
        ipcManager.cleanup();
    }

    console.log('[App] Services cleaned up');
});

module.exports = { mainWindow };