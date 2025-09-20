const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    app: {
        close: () => ipcRenderer.invoke('app:close')
    },
    voice: {
        start: () => ipcRenderer.invoke('voice:start'),
        stop: () => ipcRenderer.invoke('voice:stop')
    }
});