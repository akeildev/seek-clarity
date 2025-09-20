class ControlsManager {
    constructor() {
        this.ripples = [];
        this.init();
    }

    init() {
        this.attachRippleEffects();
        this.attachHoverEffects();
        this.attachKeyboardShortcuts();
    }

    attachRippleEffects() {
        const buttons = document.querySelectorAll('button');

        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.createRipple(e, button);
            });
        });
    }

    createRipple(event, button) {
        const ripple = document.createElement('span');
        ripple.className = 'ripple-effect';

        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        button.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    attachHoverEffects() {
        const glassPanel = document.querySelector('.glass-pill');

        if (glassPanel) {
            glassPanel.addEventListener('mouseenter', () => {
                glassPanel.classList.add('hover');
                this.createGlowEffect();
            });

            glassPanel.addEventListener('mouseleave', () => {
                glassPanel.classList.remove('hover');
                this.removeGlowEffect();
            });
        }
    }

    createGlowEffect() {
        const glow = document.querySelector('.wave-glow');
        if (glow) {
            glow.classList.add('active');
        }
    }

    removeGlowEffect() {
        const glow = document.querySelector('.wave-glow');
        if (glow) {
            glow.classList.remove('active');
        }
    }

    attachKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case ' ':
                        e.preventDefault();
                        this.triggerVoice();
                        break;
                    case 'm':
                        e.preventDefault();
                        this.triggerMute();
                        break;
                    case 'Escape':
                        this.triggerClose();
                        break;
                }
            }
        });
    }

    triggerVoice() {
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            voiceButton.click();
        }
    }

    triggerMute() {
        const muteButton = document.getElementById('muteButton');
        if (muteButton) {
            muteButton.click();
        }
    }

    triggerClose() {
        const closeButton = document.getElementById('closeButton');
        if (closeButton) {
            closeButton.click();
        }
    }

    animateButtonPress(button) {
        button.classList.add('pressed');
        setTimeout(() => {
            button.classList.remove('pressed');
        }, 200);
    }
}

if (typeof window !== 'undefined') {
    window.ControlsManager = ControlsManager;
}