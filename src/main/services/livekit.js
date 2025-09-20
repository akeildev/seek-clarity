const { AccessToken } = require('livekit-server-sdk');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');

class LiveKitService extends EventEmitter {
    constructor() {
        super();
        this.currentRoom = null;
        this.isConnected = false;
        this.config = {
            url: process.env.LIVEKIT_URL,
            apiKey: process.env.LIVEKIT_API_KEY,
            apiSecret: process.env.LIVEKIT_API_SECRET
        };
    }

    async initialize() {
        try {
            if (!this.config.url || !this.config.apiKey || !this.config.apiSecret) {
                console.warn('[LiveKit] Missing configuration');
                console.log('  URL:', this.config.url ? 'Set' : 'Missing');
                console.log('  API Key:', this.config.apiKey ? 'Set' : 'Missing');
                console.log('  API Secret:', this.config.apiSecret ? 'Set' : 'Missing');
                return false;
            }

            console.log('[LiveKit] Service initialized');
            console.log('  LiveKit URL:', this.config.url);
            return true;
        } catch (error) {
            console.error('[LiveKit] Initialization failed:', error);
            return false;
        }
    }

    async generateToken(roomName, participantName = 'user', metadata = {}) {
        if (!this.config.apiKey || !this.config.apiSecret) {
            throw new Error('LiveKit API credentials not configured');
        }

        console.log('[LiveKit] Generating token for room:', roomName);

        try {
            const token = new AccessToken(this.config.apiKey, this.config.apiSecret, {
                identity: participantName,
                ttl: '10h',
                metadata: JSON.stringify(metadata)
            });

            token.addGrant({
                roomJoin: true,
                room: roomName,
                canPublish: true,
                canSubscribe: true,
                canPublishData: true,
                canUpdateOwnMetadata: true,
                hidden: false
            });

            const jwt = await token.toJwt();
            console.log('[LiveKit] Token generated successfully');
            return jwt;
        } catch (error) {
            console.error('[LiveKit] Token generation failed:', error);
            throw error;
        }
    }

    async startSession(options = {}) {
        try {
            if (this.isConnected) {
                console.warn('[LiveKit] Already connected');
                return {
                    success: false,
                    error: 'Already connected to a session'
                };
            }

            console.log('[LiveKit] Starting session...');

            this.currentRoom = `clarity-${uuidv4().slice(0, 8)}`;
            console.log('[LiveKit] Room name:', this.currentRoom);

            if (!this.config.url) {
                throw new Error('LiveKit URL not configured');
            }

            const token = await this.generateToken(this.currentRoom, 'user', {
                role: 'user',
                timestamp: Date.now()
            });

            this.isConnected = true;
            this.emit('connected', { room: this.currentRoom });

            return {
                success: true,
                url: this.config.url,
                token: token,
                roomName: this.currentRoom
            };
        } catch (error) {
            console.error('[LiveKit] Failed to start session:', error);
            this.emit('error', error);

            return {
                success: false,
                error: error.message
            };
        }
    }

    async stopSession() {
        try {
            if (!this.isConnected) {
                console.warn('[LiveKit] Not connected');
                return;
            }

            console.log('[LiveKit] Stopping session...');

            this.isConnected = false;
            this.currentRoom = null;
            this.emit('disconnected');

            console.log('[LiveKit] Session stopped');
        } catch (error) {
            console.error('[LiveKit] Failed to stop session:', error);
        }
    }

    getRoomInfo() {
        return {
            isConnected: this.isConnected,
            roomName: this.currentRoom,
            url: this.config.url
        };
    }
}

module.exports = LiveKitService;