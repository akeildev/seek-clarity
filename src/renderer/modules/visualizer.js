class LiquidVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas?.getContext('2d');
        this.animationId = null;
        this.isActive = false;

        this.waves = [];
        this.particles = [];
        this.audioLevel = 0;
        this.targetAudioLevel = 0;
        this.smoothingFactor = 0.15;

        this.colors = {
            primary: 'rgba(147, 197, 253, 0.6)',
            secondary: 'rgba(255, 255, 255, 0.3)',
            glow: 'rgba(147, 197, 253, 0.2)'
        };

        this.init();
    }

    init() {
        if (!this.canvas) return;

        this.resize();
        window.addEventListener('resize', () => this.resize());

        for (let i = 0; i < 3; i++) {
            this.waves.push({
                amplitude: 5 + i * 2,
                frequency: 0.02 - i * 0.005,
                phase: i * Math.PI / 3,
                speed: 0.02 - i * 0.005,
                opacity: 0.6 - i * 0.2
            });
        }
    }

    resize() {
        const rect = this.canvas.parentElement?.getBoundingClientRect();
        if (rect) {
            this.canvas.width = rect.width;
            this.canvas.height = rect.height;
        }
    }

    updateAudioLevel(level) {
        this.targetAudioLevel = Math.min(1, Math.max(0, level));

        if (level > 0.3 && Math.random() > 0.7) {
            this.createParticle();
        }
    }

    createParticle() {
        if (this.particles.length < 10) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: this.canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: -Math.random() * 3 - 1,
                size: Math.random() * 3 + 1,
                life: 1,
                decay: 0.02
            });
        }
    }

    drawWave(wave, time) {
        const { amplitude, frequency, phase, opacity } = wave;
        const width = this.canvas.width;
        const height = this.canvas.height;
        const centerY = height / 2;

        this.ctx.beginPath();
        this.ctx.moveTo(0, centerY);

        for (let x = 0; x <= width; x += 2) {
            const relativeX = x / width;
            const dampening = Math.sin(relativeX * Math.PI);
            const y = centerY + Math.sin(x * frequency + phase + time) *
                      amplitude * dampening * (1 + this.audioLevel * 2);

            if (x === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }

        this.ctx.lineTo(width, height);
        this.ctx.lineTo(0, height);
        this.ctx.closePath();

        const gradient = this.ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, `rgba(147, 197, 253, ${opacity * 0.3})`);
        gradient.addColorStop(0.5, `rgba(147, 197, 253, ${opacity * 0.6})`);
        gradient.addColorStop(1, `rgba(147, 197, 253, ${opacity * 0.1})`);

        this.ctx.fillStyle = gradient;
        this.ctx.fill();
    }

    drawParticles() {
        this.particles = this.particles.filter(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += 0.1;
            particle.life -= particle.decay;

            if (particle.life > 0) {
                const gradient = this.ctx.createRadialGradient(
                    particle.x, particle.y, 0,
                    particle.x, particle.y, particle.size
                );
                gradient.addColorStop(0, `rgba(255, 255, 255, ${particle.life * 0.8})`);
                gradient.addColorStop(1, `rgba(147, 197, 253, ${particle.life * 0.3})`);

                this.ctx.beginPath();
                this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.ctx.fillStyle = gradient;
                this.ctx.fill();

                return true;
            }
            return false;
        });
    }

    drawGlow() {
        if (this.audioLevel > 0.1) {
            const gradient = this.ctx.createRadialGradient(
                this.canvas.width / 2, this.canvas.height / 2, 0,
                this.canvas.width / 2, this.canvas.height / 2, this.canvas.width / 2
            );
            gradient.addColorStop(0, `rgba(147, 197, 253, ${this.audioLevel * 0.3})`);
            gradient.addColorStop(1, 'transparent');

            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    draw() {
        if (!this.isActive || !this.ctx) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.audioLevel += (this.targetAudioLevel - this.audioLevel) * this.smoothingFactor;

        const time = Date.now() * 0.001;

        this.waves.forEach((wave, index) => {
            wave.phase += wave.speed;
            this.drawWave(wave, time);
        });

        this.drawParticles();
        this.drawGlow();

        this.animationId = requestAnimationFrame(() => this.draw());
    }

    start() {
        if (this.isActive) return;
        this.isActive = true;
        this.draw();
    }

    stop() {
        this.isActive = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    setActive(active) {
        if (active) {
            this.start();
        } else {
            this.stop();
        }
    }
}

if (typeof window !== 'undefined') {
    window.LiquidVisualizer = LiquidVisualizer;
}