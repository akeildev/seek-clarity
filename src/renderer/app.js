class ClarityApp {
    constructor() {
        this.elements = {
            voiceButton: document.getElementById('voiceButton'),
            muteButton: document.getElementById('muteButton'),
            closeButton: document.getElementById('closeButton'),
            visualizer: document.getElementById('visualizer')
        };

        this.state = {
            isActive: false,
            isMuted: false
        };

        this.visualizer = null;
        this.voiceManager = null;
        this.init();
    }

    async init() {
        console.log('[App] Starting initialization...');
        this.setupEventListeners();
        this.initVisualizer();
        this.initControls();
        await this.initVoice();
        console.log('[App] Initialized with elements:', Object.keys(this.elements).map(k => k + ': ' + !!this.elements[k]).join(', '));
    }

    async initVoice() {
        if (window.VoiceManager) {
            this.voiceManager = new window.VoiceManager();
            await this.voiceManager.initialize();

            if (this.visualizer) {
                this.voiceManager.setVisualizer(this.visualizer);
            }

            this.voiceManager.on('connected', () => {
                this.updateUI(true, false);
            });

            this.voiceManager.on('disconnected', () => {
                this.updateUI(false, false);
            });

            this.voiceManager.on('muteChanged', (data) => {
                this.updateUI(this.state.isActive, data.isMuted);
            });

            this.voiceManager.on('error', (error) => {
                console.error('[App] Voice error:', error);
                this.updateUI(false, false);
            });
        }
    }

    initControls() {
        if (window.ControlsManager) {
            this.controls = new window.ControlsManager();
        }
    }

    setupEventListeners() {
        console.log('[App] Setting up event listeners');
        if (this.elements.voiceButton) {
            this.elements.voiceButton.addEventListener('click', () => {
                console.log('[App] Voice button clicked');
                this.toggleVoice();
            });
            console.log('[App] Voice button listener attached');
        } else {
            console.warn('[App] Voice button not found!');
        }

        if (this.elements.muteButton) {
            this.elements.muteButton.addEventListener('click', () => this.toggleMute());
        }

        if (this.elements.closeButton) {
            this.elements.closeButton.addEventListener('click', () => {
                console.log('[App] Close button clicked');
                this.close();
            });
            console.log('[App] Close button listener attached');
        } else {
            console.warn('[App] Close button not found!');
        }
    }

    initVisualizer() {
        if (window.LiquidVisualizer && this.elements.visualizer) {
            const canvas = document.getElementById('waveCanvas');
            if (canvas) {
                this.visualizer = new window.LiquidVisualizer('waveCanvas');
            }
        }
    }

    async toggleVoice() {
        this.state.isActive = !this.state.isActive;

        if (this.state.isActive) {
            await this.startVoiceSession();
        } else {
            await this.stopVoiceSession();
        }
    }

    async toggleMute() {
        if (this.voiceManager && this.state.isActive) {
            const isMuted = await this.voiceManager.toggleMute();
            this.updateUI(this.state.isActive, isMuted);
        }
    }

    async startVoiceSession() {
        console.log('[App] Starting voice session');

        if (this.visualizer) {
            this.visualizer.start();
        }

        if (this.voiceManager) {
            const success = await this.voiceManager.start();
            if (success) {
                this.updateUI(true, false);
            } else {
                this.updateUI(false, false);
            }
        } else {
            this.simulateAudioLevels();
        }
    }

    async stopVoiceSession() {
        console.log('[App] Stopping voice session');

        if (this.visualizer) {
            this.visualizer.stop();
        }

        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }

        if (this.voiceManager) {
            await this.voiceManager.stop();
        }

        this.updateUI(false, false);
    }

    updateUI(isActive, isMuted) {
        this.state.isActive = isActive;
        this.state.isMuted = isMuted;

        if (isActive) {
            this.elements.voiceButton.classList.add('active');
        } else {
            this.elements.voiceButton.classList.remove('active');
        }

        if (isMuted) {
            this.elements.muteButton.classList.add('muted');
        } else {
            this.elements.muteButton.classList.remove('muted');
        }
    }

    simulateAudioLevels() {
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
        }

        this.animationInterval = setInterval(() => {
            if (this.visualizer && this.state.isActive) {
                const level = Math.random() * 0.5 + 0.1;
                this.visualizer.updateAudioLevel(level);
            }
        }, 100);
    }

    close() {
        console.log('[App] Closing');

        if (window.electron?.app) {
            window.electron.app.close();
        } else if (window.close) {
            window.close();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[App] DOMContentLoaded - Starting ClarityApp');
    window.clarityApp = new ClarityApp();
    console.log('[App] Window size:', window.innerWidth, 'x', window.innerHeight);
    console.log('[App] Window location:', window.location.href);
});