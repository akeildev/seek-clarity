const { contextBridge, ipcRenderer } = require('electron');

const IPC_CHANNELS = {
    APP_CLOSE: 'app:close',
    VOICE_START: 'voice:start',
    VOICE_STOP: 'voice:stop',
    VOICE_STATUS: 'voice:status',
    VOICE_ERROR: 'voice:error',
    AUDIO_LEVEL: 'audio:level'
};

contextBridge.exposeInMainWorld('electron', {
    app: {
        close: () => ipcRenderer.invoke(IPC_CHANNELS.APP_CLOSE)
    },
    voice: {
        start: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_START),
        stop: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_STOP),
        getStatus: () => ipcRenderer.invoke(IPC_CHANNELS.VOICE_STATUS)
    }
});