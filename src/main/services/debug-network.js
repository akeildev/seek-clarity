const https = require('https');
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

class DebugService {
    constructor() {
        this.results = [];
    }

    async checkEnvironmentFolder() {
        console.log('\n[DEBUG] ========== ENVIRONMENT FOLDER CHECK ==========');

        const folders = [
            process.cwd(),
            path.join(process.cwd(), 'src'),
            path.join(process.cwd(), 'src/agent'),
            path.join(process.cwd(), 'src/main'),
            path.join(process.cwd(), 'src/renderer'),
            path.join(process.cwd(), 'src/automation'),
            path.join(process.cwd(), '.env'),
            path.join(process.cwd(), 'node_modules'),
        ];

        for (const folder of folders) {
            try {
                const exists = fs.existsSync(folder);
                const stats = exists ? fs.statSync(folder) : null;

                console.log(`[DEBUG] Path: ${folder}`);
                console.log(`  Exists: ${exists ? '✓' : '✗'}`);

                if (stats) {
                    console.log(`  Type: ${stats.isDirectory() ? 'Directory' : stats.isFile() ? 'File' : 'Other'}`);
                    console.log(`  Readable: ${fs.constants.R_OK ? '✓' : '✗'}`);
                    console.log(`  Size: ${stats.size} bytes`);

                    if (stats.isDirectory()) {
                        const files = fs.readdirSync(folder);
                        console.log(`  Files: ${files.length} items`);
                        if (files.length <= 10) {
                            console.log(`  Contents: ${files.join(', ')}`);
                        } else {
                            console.log(`  Sample: ${files.slice(0, 5).join(', ')}...`);
                        }
                    }
                }
            } catch (error) {
                console.log(`[DEBUG] Error checking ${folder}: ${error.message}`);
            }
        }

        console.log('[DEBUG] ================================================\n');
    }

    async checkNetworkConnectivity() {
        console.log('\n[DEBUG] ========== NETWORK CONNECTIVITY CHECK ==========');

        const endpoints = [
            { name: 'LiveKit Cloud', url: 'wss://halo-ecujaon7.livekit.cloud', type: 'websocket' },
            { name: 'OpenAI API', url: 'https://api.openai.com/v1/models', type: 'https' },
            { name: 'ElevenLabs API', url: 'https://api.elevenlabs.io/v1/voices', type: 'https' },
            { name: 'Supabase', url: 'https://ydfqrsyqoywwmwysdypy.supabase.co', type: 'https' },
            { name: 'Local WebSocket', url: 'ws://localhost:8765', type: 'websocket' },
            { name: 'DNS Check', url: 'https://dns.google', type: 'https' },
        ];

        for (const endpoint of endpoints) {
            console.log(`\n[DEBUG] Testing: ${endpoint.name}`);
            console.log(`  URL: ${endpoint.url}`);

            if (endpoint.type === 'websocket') {
                await this.testWebSocket(endpoint.url, endpoint.name);
            } else {
                await this.testHTTPS(endpoint.url, endpoint.name);
            }
        }

        // Check system network info
        await this.checkSystemNetwork();

        console.log('[DEBUG] ================================================\n');
    }

    async testWebSocket(url, name) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            let ws;

            const timeout = setTimeout(() => {
                console.log(`  ✗ Timeout after 5s`);
                if (ws) ws.close();
                resolve(false);
            }, 5000);

            try {
                ws = new WebSocket(url);

                ws.on('open', () => {
                    const latency = Date.now() - startTime;
                    console.log(`  ✓ Connected in ${latency}ms`);
                    clearTimeout(timeout);
                    ws.close();
                    resolve(true);
                });

                ws.on('error', (error) => {
                    console.log(`  ✗ Error: ${error.message}`);
                    clearTimeout(timeout);
                    resolve(false);
                });
            } catch (error) {
                console.log(`  ✗ Exception: ${error.message}`);
                clearTimeout(timeout);
                resolve(false);
            }
        });
    }

    async testHTTPS(url, name) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const urlObj = new URL(url);

            const options = {
                hostname: urlObj.hostname,
                port: urlObj.port || 443,
                path: urlObj.pathname,
                method: 'GET',
                timeout: 5000,
                headers: {
                    'User-Agent': 'Clarity-Debug/1.0'
                }
            };

            const req = https.request(options, (res) => {
                const latency = Date.now() - startTime;
                console.log(`  ✓ Response: ${res.statusCode} in ${latency}ms`);
                res.on('data', () => {}); // Consume response
                resolve(true);
            });

            req.on('error', (error) => {
                console.log(`  ✗ Error: ${error.message}`);
                resolve(false);
            });

            req.on('timeout', () => {
                console.log(`  ✗ Timeout after 5s`);
                req.destroy();
                resolve(false);
            });

            req.end();
        });
    }

    async checkSystemNetwork() {
        console.log('\n[DEBUG] System Network Info:');

        try {
            // Check network interfaces
            const os = require('os');
            const interfaces = os.networkInterfaces();

            for (const [name, addresses] of Object.entries(interfaces)) {
                const ipv4 = addresses.find(addr => addr.family === 'IPv4' && !addr.internal);
                if (ipv4) {
                    console.log(`  ${name}: ${ipv4.address}`);
                }
            }

            // Check DNS resolution
            const dns = require('dns').promises;
            try {
                const addresses = await dns.resolve4('google.com');
                console.log(`  DNS Resolution: ✓ (google.com -> ${addresses[0]})`);
            } catch (error) {
                console.log(`  DNS Resolution: ✗ (${error.message})`);
            }

            // Check ping to common endpoints
            if (process.platform !== 'win32') {
                try {
                    const { stdout } = await execAsync('ping -c 1 -W 1 8.8.8.8');
                    const match = stdout.match(/time=(\d+\.?\d*)/);
                    if (match) {
                        console.log(`  Internet Ping: ✓ (${match[1]}ms to 8.8.8.8)`);
                    }
                } catch (error) {
                    console.log(`  Internet Ping: ✗`);
                }
            }

        } catch (error) {
            console.log(`  System info error: ${error.message}`);
        }
    }

    async checkAPIKeys() {
        console.log('\n[DEBUG] ========== API KEY VALIDATION ==========');

        const keys = {
            LIVEKIT_API_KEY: process.env.LIVEKIT_API_KEY,
            LIVEKIT_API_SECRET: process.env.LIVEKIT_API_SECRET,
            OPENAI_API_KEY: process.env.OPENAI_API_KEY,
            ELEVENLABS_API_KEY: process.env.ELEVENLABS_API_KEY || process.env.ELEVEN_API_KEY,
            SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY
        };

        for (const [name, value] of Object.entries(keys)) {
            if (value) {
                console.log(`  ${name}: ✓ Set (${value.substring(0, 10)}...)`);

                // Validate format
                if (name === 'OPENAI_API_KEY' && !value.startsWith('sk-')) {
                    console.log(`    ⚠️  Warning: OpenAI key should start with 'sk-'`);
                }
                if (name === 'LIVEKIT_API_KEY' && !value.startsWith('API')) {
                    console.log(`    ⚠️  Warning: LiveKit key usually starts with 'API'`);
                }
            } else {
                console.log(`  ${name}: ✗ Not set`);
            }
        }

        console.log('[DEBUG] =========================================\n');
    }

    async runFullDiagnostics() {
        console.log('\n🔍 RUNNING FULL DIAGNOSTICS FOR CLARITY\n');

        await this.checkEnvironmentFolder();
        await this.checkAPIKeys();
        await this.checkNetworkConnectivity();

        console.log('✅ DIAGNOSTICS COMPLETE\n');
    }
}

module.exports = DebugService;