class LiveKitClient {
    constructor() {
        this.room = null;
        this.localParticipant = null;
        this.audioTrack = null;
        this.isConnected = false;
        this.isMuted = false;
        this.eventHandlers = new Map();

        this.audioLevel = 0;
        this.audioLevelInterval = null;
    }

    async connect(connectionInfo) {
        try {
            const { url, token, roomName } = connectionInfo;

            console.log(`[LiveKit] Connecting to room: ${roomName}`);

            if (!window.LivekitClient) {
                await this.loadLiveKitSDK();
            }

            this.room = new window.LivekitClient.Room({
                adaptiveStream: true,
                dynacast: true,
                publishDefaults: {
                    simulcast: false,
                    stopMicTrackOnMute: false
                },
                disconnectOnPageLeave: true
            });

            this.setupRoomEventListeners();

            await this.room.connect(url, token, {
                autoSubscribe: true
            });

            this.isConnected = true;
            console.log('[LiveKit] Successfully connected');

            await this.enableMicrophone();
            this.startAudioLevelMonitoring();

            this.emit('connected', { roomName });

            return true;
        } catch (error) {
            console.error('[LiveKit] Failed to connect:', error);
            this.emit('error', { message: error.message });
            throw error;
        }
    }

    async disconnect() {
        console.log('[LiveKit] Disconnecting');

        try {
            this.stopAudioLevelMonitoring();

            if (this.audioTrack) {
                await this.room?.localParticipant?.unpublishTrack(this.audioTrack);
                this.audioTrack.stop();
                this.audioTrack = null;
            }

            if (this.room) {
                await this.room.disconnect();
                this.room = null;
            }

            this.isConnected = false;
            this.emit('disconnected');

            console.log('[LiveKit] Disconnected');
        } catch (error) {
            console.error('[LiveKit] Error during disconnect:', error);
        }
    }

    async enableMicrophone() {
        if (!this.room || !this.isConnected) {
            throw new Error('Not connected to room');
        }

        try {
            console.log('[LiveKit] Enabling microphone');

            this.audioTrack = await window.LivekitClient.createLocalAudioTrack({
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000,
                channelCount: 1
            });

            await this.room.localParticipant.publishTrack(this.audioTrack);

            console.log('[LiveKit] Microphone enabled');
            this.emit('microphoneEnabled');

            return true;
        } catch (error) {
            console.error('[LiveKit] Failed to enable microphone:', error);
            this.emit('error', { message: 'Microphone access denied' });
            throw error;
        }
    }

    async toggleMute() {
        if (!this.audioTrack) return;

        this.isMuted = !this.isMuted;
        await this.audioTrack.setMuted(this.isMuted);

        console.log('[LiveKit] Mute status:', this.isMuted);
        this.emit('muteChanged', { isMuted: this.isMuted });

        return this.isMuted;
    }

    setupRoomEventListeners() {
        if (!this.room) return;

        this.room.on('participantConnected', (participant) => {
            console.log('[LiveKit] Participant connected:', participant.identity);
            this.emit('participantConnected', { participant });
        });

        this.room.on('participantDisconnected', (participant) => {
            console.log('[LiveKit] Participant disconnected:', participant.identity);
            this.emit('participantDisconnected', { participant });
        });

        this.room.on('trackSubscribed', (track, publication, participant) => {
            console.log('[LiveKit] Track subscribed:', track.kind, 'from', participant.identity);

            if (track.kind === 'audio') {
                const audioElement = track.attach();
                audioElement.play().catch(e => console.error('Audio playback failed:', e));
            }
        });

        this.room.on('disconnected', () => {
            console.log('[LiveKit] Room disconnected');
            this.isConnected = false;
            this.emit('disconnected');
        });

        this.room.on('reconnecting', () => {
            console.log('[LiveKit] Reconnecting...');
            this.emit('reconnecting');
        });

        this.room.on('reconnected', () => {
            console.log('[LiveKit] Reconnected');
            this.emit('reconnected');
        });
    }

    startAudioLevelMonitoring() {
        if (this.audioLevelInterval) return;

        this.audioLevelInterval = setInterval(() => {
            if (this.audioTrack && !this.isMuted) {
                const level = this.getAudioLevel();
                if (level !== this.audioLevel) {
                    this.audioLevel = level;
                    this.emit('audioLevelChanged', { level });
                }
            }
        }, 100);
    }

    stopAudioLevelMonitoring() {
        if (this.audioLevelInterval) {
            clearInterval(this.audioLevelInterval);
            this.audioLevelInterval = null;
        }
    }

    getAudioLevel() {
        if (!this.audioTrack || this.isMuted) return 0;

        const stats = this.audioTrack.getStats();
        if (stats && stats.audioLevel !== undefined) {
            return Math.min(1, stats.audioLevel * 10);
        }

        return Math.random() * 0.3;
    }

    async loadLiveKitSDK() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/livekit-client@2.5.2/dist/livekit-client.umd.min.js';
            script.onload = () => {
                window.LivekitClient = window.LivekitClient || window.LiveKit;
                resolve();
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => handler(data));
        }
    }
}

if (typeof window !== 'undefined') {
    window.LiveKitClient = LiveKitClient;
}