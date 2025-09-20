const { BrowserWindow, screen } = require('electron');
const path = require('path');

class WindowService {
    constructor() {
        this.windows = new Map();
        this.mainWindowId = null;
    }

    createMainWindow(options = {}) {
        const defaultOptions = {
            width: 320,
            height: 80,
            frame: false,
            transparent: true,
            backgroundColor: '#00000000',
            resizable: false,
            alwaysOnTop: true,
            skipTaskbar: true,
            minimizable: false,
            maximizable: false,
            hasShadow: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                webSecurity: true,
                backgroundThrottling: false
            }
        };

        const windowOptions = { ...defaultOptions, ...options };
        if (!windowOptions.x || !windowOptions.y) {
            windowOptions.x = 20;
            windowOptions.y = 20;
        }

        const window = new BrowserWindow(windowOptions);
        const id = window.id;
        this.windows.set(id, window);
        this.mainWindowId = id;

        if (process.platform === 'darwin') {
            window.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
            window.setAlwaysOnTop(true, 'screen-saver');
        }

        this.setupWindowEventHandlers(window);
        window.on('closed', () => {
            this.windows.delete(id);
            if (this.mainWindowId === id) {
                this.mainWindowId = null;
            }
        });

        console.log(`[WindowService] Created window with ID: ${id}`);
        return window;
    }

    setupWindowEventHandlers(window) {
        let saveTimer = null;

        window.on('moved', () => {
            if (saveTimer) clearTimeout(saveTimer);
            saveTimer = setTimeout(() => {
                const [x, y] = window.getPosition();
                console.log(`[WindowService] Window moved to: ${x}, ${y}`);
            }, 500);
        });

        window.on('blur', () => {
            if (process.platform === 'darwin') {
                window.setAlwaysOnTop(true, 'screen-saver');
            } else {
                window.setAlwaysOnTop(true);
            }
        });

        window.on('show', () => {
            window.focus();
            console.log('[WindowService] Window shown');
        });

        window.on('hide', () => {
            console.log('[WindowService] Window hidden');
        });
    }

    getMainWindow() {
        if (this.mainWindowId) {
            return this.windows.get(this.mainWindowId);
        }
        return null;
    }

    getAllWindows() {
        return Array.from(this.windows.values());
    }

    centerWindow(window) {
        const display = screen.getPrimaryDisplay();
        const { width, height } = display.workAreaSize;
        const [windowWidth, windowHeight] = window.getSize();

        const x = Math.round((width - windowWidth) / 2);
        const y = Math.round((height - windowHeight) / 2);

        window.setPosition(x, y);
    }

    positionInCorner(window, corner = 'top-left') {
        const display = screen.getPrimaryDisplay();
        const { width, height } = display.workAreaSize;
        const [windowWidth, windowHeight] = window.getSize();
        const margin = 20;

        let x, y;

        switch (corner) {
            case 'top-right':
                x = width - windowWidth - margin;
                y = margin;
                break;
            case 'bottom-left':
                x = margin;
                y = height - windowHeight - margin;
                break;
            case 'bottom-right':
                x = width - windowWidth - margin;
                y = height - windowHeight - margin;
                break;
            case 'top-left':
            default:
                x = margin;
                y = margin;
                break;
        }

        window.setPosition(x, y);
    }
}

module.exports = new WindowService();