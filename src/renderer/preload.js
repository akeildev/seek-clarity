const { contextBridge, ipcRenderer } = require('electron');

const IPC_CHANNELS = {
    APP_CLOSE: 'app:close',
    VOICE_START: 'voice:start',
    VOICE_STOP: 'voice:stop',
    VOICE_STATUS: 'voice:status',
    VOICE_ERROR: 'voice:error',
    SETTINGS_GET: 'settings:get',
    SETTINGS_SET: 'settings:set'
};

contextBridge.exposeInMainWorld('electron', {
    app: {
        close: () => ipcRenderer.invoke(IPC_CHANNELS.APP_CLOSE)
    },
    voice: {
        start: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_START),
        stop: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_STOP),
        getStatus: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_STATUS),
        onStatus: (callback) => {
            ipcRenderer.on(IPC_CHANNELS.VOICE_STATUS, (event, data) => callback(data));
        },
        onError: (callback) => {
            ipcRenderer.on(IPC_CHANNELS.VOICE_ERROR, (event, data) => callback(data));
        }
    },
    settings: {
        get: (key) => ipcRenderer.invoke(IPC_CHANNELS.SETTINGS_GET, key),
        set: (key, value) => ipcRenderer.invoke(IPC_CHANNELS.SETTINGS_SET, key, value),
        getAll: () => ipcRenderer.invoke(IPC_CHANNELS.SETTINGS_GET)
    },
    window: {
        minimize: () => ipcRenderer.invoke('window:minimize'),
        maximize: () => ipcRenderer.invoke('window:maximize'),
        getBounds: () => ipcRenderer.invoke('window:getBounds'),
        setBounds: (bounds) => ipcRenderer.invoke('window:setBounds', bounds)
    }
});