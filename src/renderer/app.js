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
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initVisualizer();
        this.initControls();
        console.log('[App] Initialized');
    }

    initControls() {
        if (window.ControlsManager) {
            this.controls = new window.ControlsManager();
        }
    }

    setupEventListeners() {
        if (this.elements.voiceButton) {
            this.elements.voiceButton.addEventListener('click', () => this.toggleVoice());
        }

        if (this.elements.muteButton) {
            this.elements.muteButton.addEventListener('click', () => this.toggleMute());
        }

        if (this.elements.closeButton) {
            this.elements.closeButton.addEventListener('click', () => this.close());
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

    toggleVoice() {
        this.state.isActive = !this.state.isActive;

        if (this.state.isActive) {
            this.elements.voiceButton.classList.add('active');
            this.startVoiceSession();
        } else {
            this.elements.voiceButton.classList.remove('active');
            this.stopVoiceSession();
        }
    }

    toggleMute() {
        this.state.isMuted = !this.state.isMuted;

        if (this.state.isMuted) {
            this.elements.muteButton.classList.add('muted');
        } else {
            this.elements.muteButton.classList.remove('muted');
        }

        console.log('[App] Mute:', this.state.isMuted);
    }

    startVoiceSession() {
        console.log('[App] Starting voice session');

        if (this.visualizer) {
            this.visualizer.start();
            this.simulateAudioLevels();
        }

        if (window.electron?.voice) {
            window.electron.voice.start();
        }
    }

    stopVoiceSession() {
        console.log('[App] Stopping voice session');

        if (this.visualizer) {
            this.visualizer.stop();
        }

        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }

        if (window.electron?.voice) {
            window.electron.voice.stop();
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
    window.clarityApp = new ClarityApp();
});