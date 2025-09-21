require('dotenv').config();
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const LiveKitService = require('./services/livekit');
const settingsService = require('./services/settings');
const DesktopCaptureService = require('./services/capture');
const ScreenshotWebSocketServer = require('./services/websocket');
const AppleScriptService = require('./services/applescript');
const IPCManager = require('../shared/ipc');
const { IPC_CHANNELS } = require('../shared/constants');

let mainWindow;
let services = {};
let ipcManager;

async function initializeServices() {
    try {
        console.log('[App] Initializing services...');

        // Run debug diagnostics first
        const DebugService = require('./services/debug-network');
        const debugService = new DebugService();
        await debugService.runFullDiagnostics();

        services.settings = settingsService;
        await services.settings.initialize();

        const config = services.settings.getLiveKitConfig();
        services.livekit = new LiveKitService();
        const livekitReady = await services.livekit.initialize();

        if (!livekitReady) {
            console.warn('[App] LiveKit service not fully configured');
        }

        // Initialize screenshot services
        services.capture = new DesktopCaptureService();

        // Initialize AppleScript service
        services.applescript = new AppleScriptService();
        await services.applescript.initialize();

        // Initialize WebSocket with both services
        services.websocket = new ScreenshotWebSocketServer(services.capture, services.applescript);

        services.mainWindow = mainWindow;

        // Start WebSocket server for screenshot bridge
        try {
            services.websocket.start();
            console.log('[App] Screenshot WebSocket server started');
        } catch (error) {
            console.error('[App] Failed to start screenshot WebSocket server:', error);
        }

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
    console.log('[Window] Creating main window...');
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
    console.log('[Window] Loading HTML from:', path.join(__dirname, '../renderer/index.html'));

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
        console.log('[Window] Main window closed');
        mainWindow = null;
    });

    mainWindow.on('ready-to-show', () => {
        console.log('[Window] Ready to show');
        const bounds = mainWindow.getBounds();
        console.log('[Window] Position:', bounds.x, bounds.y, 'Size:', bounds.width, 'x', bounds.height);
    });

    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    }

    mainWindow.webContents.on('did-finish-load', () => {
        console.log('[Window] Page loaded successfully');
    });

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('[Window] Failed to load:', errorCode, errorDescription);
    });

    mainWindow.webContents.on('console-message', (event, level, message) => {
        console.log('[Renderer]', message);
    });
}

app.whenReady().then(async () => {
    console.log('[App] Electron ready');
    const initialized = await initializeServices();
    console.log('[App] Services initialized:', initialized);
    createWindow();
    console.log('[App] Window created');

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('before-quit', () => {
    console.log('[App] Cleaning up services...');
    if (services.websocket) {
        try {
            services.websocket.stop();
            console.log('[App] Screenshot WebSocket server stopped');
        } catch (error) {
            console.error('[App] Error stopping WebSocket server:', error);
        }
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

module.exports = { mainWindow };