const Store = require('electron-store').default || require('electron-store');

class SettingsService {
    constructor() {
        this.store = null;
        this.initialized = false;
    }

    getDefaults() {
        return {
            livekitUrl: process.env.LIVEKIT_URL || '',
            livekitApiKey: process.env.LIVEKIT_API_KEY || '',
            livekitApiSecret: process.env.LIVEKIT_API_SECRET || '',

            windowPosition: null,
            windowSize: { width: 240, height: 60 },
            alwaysOnTop: true,

            inputDevice: 'default',
            outputDevice: 'default',
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,

            theme: 'dark',
            showNotifications: true,

            settingsVersion: 1
        };
    }

    async initialize() {
        if (this.initialized) {
            return;
        }

        try {
            this.initializeStore();
            this.migrateSettings();
            this.validateSettings();

            this.initialized = true;
            console.log('[Settings] Service initialized');
        } catch (error) {
            console.error('[Settings] Initialization failed:', error);
            this.store = null;
        }
    }

    initializeStore() {
        const defaults = this.getDefaults();

        this.store = new Store({
            name: 'clarity-settings',
            defaults,
            encryptionKey: 'clarity-secure-key',
            clearInvalidConfig: true,
            migrations: {
                '1.0.0': (store) => {
                    console.log('[Settings] Migrating to v1.0.0');
                }
            }
        });
    }

    migrateSettings() {
        const version = this.get('settingsVersion', 0);

        if (version < 1) {
            console.log('[Settings] Migrating from version', version, 'to 1');
            this.set('settingsVersion', 1);
        }
    }

    validateSettings() {
        const settings = this.getAll();
        const defaults = this.getDefaults();

        for (const key in defaults) {
            if (settings[key] === undefined) {
                this.set(key, defaults[key]);
            }
        }
    }

    get(key, defaultValue) {
        if (!this.store) {
            const defaults = this.getDefaults();
            return defaultValue !== undefined ? defaultValue : defaults[key];
        }

        try {
            return this.store.get(key, defaultValue);
        } catch (error) {
            console.error('[Settings] Failed to get:', key, error);
            return defaultValue;
        }
    }

    set(key, value) {
        if (!this.store) {
            console.warn('[Settings] Cannot set - store not initialized');
            return false;
        }

        try {
            this.store.set(key, value);
            return true;
        } catch (error) {
            console.error('[Settings] Failed to set:', key, error);
            return false;
        }
    }

    getAll() {
        if (!this.store) {
            return this.getDefaults();
        }

        try {
            return this.store.store;
        } catch (error) {
            console.error('[Settings] Failed to get all settings:', error);
            return this.getDefaults();
        }
    }

    reset() {
        if (!this.store) {
            console.warn('[Settings] Cannot reset - store not initialized');
            return;
        }

        try {
            this.store.clear();
            const defaults = this.getDefaults();
            for (const key in defaults) {
                this.store.set(key, defaults[key]);
            }
            console.log('[Settings] Reset to defaults');
        } catch (error) {
            console.error('[Settings] Failed to reset:', error);
        }
    }

    getLiveKitConfig() {
        return {
            url: this.get('livekitUrl'),
            apiKey: this.get('livekitApiKey'),
            apiSecret: this.get('livekitApiSecret')
        };
    }

    getAudioConfig() {
        return {
            inputDevice: this.get('inputDevice'),
            outputDevice: this.get('outputDevice'),
            echoCancellation: this.get('echoCancellation'),
            noiseSuppression: this.get('noiseSuppression'),
            autoGainControl: this.get('autoGainControl')
        };
    }

    getWindowConfig() {
        return {
            position: this.get('windowPosition'),
            size: this.get('windowSize'),
            alwaysOnTop: this.get('alwaysOnTop')
        };
    }

    saveWindowState(bounds) {
        if (bounds) {
            this.set('windowPosition', { x: bounds.x, y: bounds.y });
            this.set('windowSize', { width: bounds.width, height: bounds.height });
        }
    }
}

module.exports = new SettingsService();