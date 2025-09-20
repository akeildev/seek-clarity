const { IPC_CHANNELS } = require('./constants');

class IPCManager {
    constructor(ipcMain, services) {
        this.ipcMain = ipcMain;
        this.services = services;
        this.handlers = new Map();
    }

    setupHandlers() {
        this.registerAppHandlers();
        this.registerVoiceHandlers();
        this.registerSettingsHandlers();
        this.registerWindowHandlers();

        console.log('[IPC] Handlers registered');
    }

    registerAppHandlers() {
        this.handle(IPC_CHANNELS.APP_CLOSE, async () => {
            const { app } = require('electron');
            if (this.services.mainWindow) {
                this.services.mainWindow.close();
            }
            app.quit();
        });
    }

    registerVoiceHandlers() {
        this.handle(IPC_CHANNELS.VOICE_START, async () => {
            if (this.services.livekit) {
                return await this.services.livekit.startSession();
            }
            return { success: false, error: 'LiveKit service not available' };
        });

        this.handle(IPC_CHANNELS.VOICE_STOP, async () => {
            if (this.services.livekit) {
                return await this.services.livekit.stopSession();
            }
        });

        this.handle(IPC_CHANNELS.VOICE_STATUS, () => {
            if (this.services.livekit) {
                return this.services.livekit.getRoomInfo();
            }
            return { isConnected: false };
        });

        if (this.services.livekit) {
            this.services.livekit.on('connected', (data) => {
                this.broadcast(IPC_CHANNELS.VOICE_STATUS, {
                    status: 'connected',
                    ...data
                });
            });

            this.services.livekit.on('disconnected', () => {
                this.broadcast(IPC_CHANNELS.VOICE_STATUS, {
                    status: 'disconnected'
                });
            });

            this.services.livekit.on('error', (error) => {
                this.broadcast(IPC_CHANNELS.VOICE_ERROR, error);
            });
        }
    }

    registerSettingsHandlers() {
        this.handle(IPC_CHANNELS.SETTINGS_GET, async (event, key) => {
            if (this.services.settings) {
                if (key) {
                    return this.services.settings.get(key);
                }
                return this.services.settings.getAll();
            }
            return null;
        });

        this.handle(IPC_CHANNELS.SETTINGS_SET, async (event, key, value) => {
            if (this.services.settings) {
                return this.services.settings.set(key, value);
            }
            return false;
        });
    }

    registerWindowHandlers() {
        this.handle('window:minimize', () => {
            if (this.services.mainWindow) {
                this.services.mainWindow.minimize();
            }
        });

        this.handle('window:maximize', () => {
            if (this.services.mainWindow) {
                if (this.services.mainWindow.isMaximized()) {
                    this.services.mainWindow.restore();
                } else {
                    this.services.mainWindow.maximize();
                }
            }
        });

        this.handle('window:getBounds', () => {
            if (this.services.mainWindow) {
                return this.services.mainWindow.getBounds();
            }
            return null;
        });

        this.handle('window:setBounds', (event, bounds) => {
            if (this.services.mainWindow && bounds) {
                this.services.mainWindow.setBounds(bounds);
            }
        });
    }

    handle(channel, handler) {
        if (this.handlers.has(channel)) {
            this.ipcMain.removeHandler(channel);
        }

        this.ipcMain.handle(channel, handler);
        this.handlers.set(channel, handler);
    }

    broadcast(channel, data) {
        const { BrowserWindow } = require('electron');
        const windows = BrowserWindow.getAllWindows();
        windows.forEach(window => {
            window.webContents.send(channel, data);
        });
    }

    cleanup() {
        this.handlers.forEach((handler, channel) => {
            this.ipcMain.removeHandler(channel);
        });
        this.handlers.clear();
        console.log('[IPC] Handlers cleaned up');
    }
}

module.exports = IPCManager;