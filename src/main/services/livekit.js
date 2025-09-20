const { AccessToken } = require('livekit-server-sdk');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class LiveKitService extends EventEmitter {
    constructor() {
        super();
        this.currentRoom = null;
        this.isConnected = false;
        this.agentProcess = null;
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

            // Start Python agent for this room
            await this.startPythonAgent(this.currentRoom);

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

    async startPythonAgent(roomName) {
        try {
            // If an agent is already running, don't start another
            if (this.agentProcess) {
                console.log('[LiveKit] Python agent already running');
                return true;
            }

            console.log('[LiveKit] Starting Python agent...');

            const agentDir = path.join(__dirname, '../../agent');
            const agentPath = path.join(agentDir, 'voice_agent.py');

            if (!fs.existsSync(agentPath)) {
                console.error('[LiveKit] Agent file not found:', agentPath);
                return false;
            }

            // Prefer venv Python if available
            const venvPython = path.join(agentDir, process.platform === 'win32' ? 'venv/Scripts/python.exe' : 'venv/bin/python3');
            let pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python3';
            if (process.platform === 'darwin' && pythonCmd === 'python3') {
                if (fs.existsSync('/opt/homebrew/bin/python3')) pythonCmd = '/opt/homebrew/bin/python3';
                else if (fs.existsSync('/usr/bin/python3')) pythonCmd = '/usr/bin/python3';
            }

            // Build environment for the agent process
            const env = {
                ...process.env,
                LIVEKIT_URL: this.config.url || process.env.LIVEKIT_URL,
                LIVEKIT_API_KEY: this.config.apiKey || process.env.LIVEKIT_API_KEY,
                LIVEKIT_API_SECRET: this.config.apiSecret || process.env.LIVEKIT_API_SECRET,
                OPENAI_API_KEY: process.env.OPENAI_API_KEY,
                ELEVEN_API_KEY: process.env.ELEVEN_API_KEY || process.env.ELEVENLABS_API_KEY,
                ELEVEN_VOICE_ID: process.env.ELEVEN_VOICE_ID || process.env.ELEVENLABS_VOICE_ID,
                LIVEKIT_WORKER_PORT: process.env.LIVEKIT_WORKER_PORT || '0',
                ROOM_NAME: roomName,
                PYTHONUNBUFFERED: '1',
                PYTHONPATH: agentDir,
            };

            console.log('[LiveKit] Agent env:');
            console.log('  LIVEKIT_URL:', env.LIVEKIT_URL ? 'Set' : 'Missing');
            console.log('  LIVEKIT_API_KEY:', env.LIVEKIT_API_KEY ? 'Set' : 'Missing');
            console.log('  LIVEKIT_API_SECRET:', env.LIVEKIT_API_SECRET ? 'Set' : 'Missing');
            console.log('  OPENAI_API_KEY:', env.OPENAI_API_KEY ? 'Set' : 'Missing');
            console.log('  ELEVEN_API_KEY present:', env.ELEVEN_API_KEY ? 'Yes' : 'No');
            console.log('  LIVEKIT_WORKER_PORT:', env.LIVEKIT_WORKER_PORT);
            console.log('  ROOM_NAME:', env.ROOM_NAME);

            // Launch the agent as a worker
            const args = [agentPath, 'dev'];
            console.log('[LiveKit] Spawning agent:', pythonCmd, agentPath, 'dev');

            this.agentProcess = spawn(pythonCmd, args, {
                env,
                cwd: agentDir,
            });

            // Wire stdout/stderr for visibility
            this.agentProcess.stdout.on('data', (data) => {
                const line = data.toString().trim();
                if (line) console.log('[Agent]:', line);
            });

            this.agentProcess.stderr.on('data', (data) => {
                const line = data.toString().trim();
                if (line) console.error('[Agent Error]:', line);
            });

            this.agentProcess.on('exit', (code, signal) => {
                console.log(`[LiveKit] Agent exited with code ${code} (signal: ${signal})`);
                this.agentProcess = null;
            });

            // Don't block start; allow the worker to come up asynchronously
            return true;
        } catch (error) {
            console.error('[LiveKit] Failed to start Python agent:', error);
            return false;
        }
    }

    async stopPythonAgent() {
        if (this.agentProcess) {
            console.log('[LiveKit] Stopping Python agent...');
            this.agentProcess.kill('SIGTERM');

            // Give it 2 seconds to gracefully shutdown
            setTimeout(() => {
                if (this.agentProcess && !this.agentProcess.killed) {
                    this.agentProcess.kill('SIGKILL');
                }
            }, 2000);

            this.agentProcess = null;
        }
    }

    async stopSession() {
        try {
            if (!this.isConnected) {
                console.warn('[LiveKit] Not connected');
                return;
            }

            console.log('[LiveKit] Stopping session...');

            // Stop the Python agent
            await this.stopPythonAgent();

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