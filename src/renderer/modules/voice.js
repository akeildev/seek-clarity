class VoiceManager {
    constructor() {
        this.livekitClient = null;
        this.isActive = false;
        this.connectionInfo = null;
        this.visualizer = null;
        this.callbacks = {};
    }

    async initialize() {
        if (window.LiveKitClient) {
            this.livekitClient = new window.LiveKitClient();
            this.setupEventListeners();
            console.log('[Voice] Manager initialized');
        } else {
            console.error('[Voice] LiveKit client not available');
        }
    }

    setupEventListeners() {
        if (!this.livekitClient) return;

        this.livekitClient.on('connected', (data) => {
            console.log('[Voice] Connected:', data);
            this.isActive = true;
            this.trigger('connected', data);
        });

        this.livekitClient.on('disconnected', () => {
            console.log('[Voice] Disconnected');
            this.isActive = false;
            this.trigger('disconnected');
        });

        this.livekitClient.on('error', (error) => {
            console.error('[Voice] Error:', error);
            this.trigger('error', error);
        });

        this.livekitClient.on('audioLevelChanged', (data) => {
            if (this.visualizer && this.visualizer.updateAudioLevel) {
                this.visualizer.updateAudioLevel(data.level);
            }
            this.trigger('audioLevel', data);
        });

        this.livekitClient.on('muteChanged', (data) => {
            this.trigger('muteChanged', data);
        });

        this.livekitClient.on('reconnecting', () => {
            console.log('[Voice] Reconnecting...');
            this.trigger('reconnecting');
        });

        this.livekitClient.on('reconnected', () => {
            console.log('[Voice] Reconnected');
            this.trigger('reconnected');
        });
    }

    async start() {
        if (this.isActive) {
            console.warn('[Voice] Already active');
            return false;
        }

        try {
            console.log('[Voice] Starting session...');
            console.log('[Voice] Electron API available:', !!window.electron);
            console.log('[Voice] Voice API available:', !!window.electron?.voice);

            const response = await window.electron.voice.start();
            console.log('[Voice] Start response:', response);

            if (response.success) {
                this.connectionInfo = response;
                console.log('[Voice] Connecting LiveKit with:', { url: response.url, room: response.roomName });
                await this.livekitClient.connect(response);
                console.log('[Voice] LiveKit connected successfully');
                return true;
            } else {
                console.error('[Voice] Failed to start:', response.error);
                return false;
            }
        } catch (error) {
            console.error('[Voice] Start failed:', error);
            return false;
        }
    }

    async stop() {
        if (!this.isActive) {
            console.warn('[Voice] Not active');
            return;
        }

        try {
            console.log('[Voice] Stopping session...');

            if (this.livekitClient) {
                await this.livekitClient.disconnect();
            }

            await window.electron.voice.stop();

            this.isActive = false;
            this.connectionInfo = null;

            console.log('[Voice] Session stopped');
        } catch (error) {
            console.error('[Voice] Stop failed:', error);
        }
    }

    async toggleMute() {
        if (this.livekitClient && this.isActive) {
            return await this.livekitClient.toggleMute();
        }
        return false;
    }

    async getStatus() {
        const status = await window.electron.voice.getStatus();
        return {
            ...status,
            clientConnected: this.isActive,
            hasMicrophone: this.livekitClient?.audioTrack !== null
        };
    }

    setVisualizer(visualizer) {
        this.visualizer = visualizer;
    }

    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }

    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(cb => cb(data));
        }
    }
}

if (typeof window !== 'undefined') {
    window.VoiceManager = VoiceManager;
}