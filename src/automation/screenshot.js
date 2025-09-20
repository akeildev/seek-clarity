const WebSocket = require('ws');
const { ipcRenderer } = require('electron');
const EventEmitter = require('events');

/**
 * Screenshot automation module
 * Integrates capture service with WebSocket bridge
 */
class ScreenshotAutomation extends EventEmitter {
  constructor() {
    super();
    this.ws = null;
    this.wsUrl = `ws://localhost:${process.env.SCREENSHOT_WS_PORT || 8765}`;
    this.reconnectInterval = 5000;
    this.isConnected = false;
    this.pendingRequests = new Map();
    this.requestId = 0;
  }

  /**
   * Connect to WebSocket server
   */
  async connect() {
    return new Promise((resolve, reject) => {
      try {
        console.log(`[ScreenshotAutomation] Connecting to ${this.wsUrl}`);

        this.ws = new WebSocket(this.wsUrl);

        this.ws.on('open', () => {
          console.log('[ScreenshotAutomation] Connected to WebSocket server');
          this.isConnected = true;
          this.emit('connected');
          resolve();
        });

        this.ws.on('message', (data) => {
          this.handleMessage(JSON.parse(data.toString()));
        });

        this.ws.on('close', () => {
          console.log('[ScreenshotAutomation] Disconnected from WebSocket server');
          this.isConnected = false;
          this.emit('disconnected');
          this.scheduleReconnect();
        });

        this.ws.on('error', (error) => {
          console.error('[ScreenshotAutomation] WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        });

      } catch (error) {
        console.error('[ScreenshotAutomation] Connection failed:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(message) {
    const { type, requestId, data, error } = message;

    // Handle responses to requests
    if (requestId && this.pendingRequests.has(requestId)) {
      const { resolve, reject } = this.pendingRequests.get(requestId);
      this.pendingRequests.delete(requestId);

      if (error) {
        reject(new Error(error));
      } else {
        resolve(data);
      }
      return;
    }

    // Handle server messages
    switch (type) {
      case 'connected':
        console.log('[ScreenshotAutomation] Server acknowledged connection');
        break;

      case 'screenshot':
        this.emit('screenshot', message.data);
        break;

      case 'analysis':
        this.emit('analysis', message.result);
        break;

      case 'status':
        this.emit('status', message.message);
        break;

      case 'error':
        console.error('[ScreenshotAutomation] Server error:', message.error);
        this.emit('error', message.error);
        break;

      default:
        console.log('[ScreenshotAutomation] Unknown message type:', type);
    }
  }

  /**
   * Send a request to the WebSocket server
   */
  async sendRequest(type, payload = {}) {
    if (!this.isConnected) {
      throw new Error('Not connected to WebSocket server');
    }

    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;

      this.pendingRequests.set(requestId, { resolve, reject });

      const message = {
        type,
        payload,
        requestId,
        timestamp: new Date().toISOString()
      };

      this.ws.send(JSON.stringify(message));

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Request timed out'));
        }
      }, 30000);
    });
  }

  /**
   * Capture a screenshot
   */
  async captureScreenshot(options = {}) {
    console.log('[ScreenshotAutomation] Capturing screenshot with options:', options);

    try {
      const result = await this.sendRequest('capture', options);
      console.log('[ScreenshotAutomation] Screenshot captured successfully');
      return result;
    } catch (error) {
      console.error('[ScreenshotAutomation] Capture failed:', error);
      throw error;
    }
  }

  /**
   * Analyze a screenshot with AI
   */
  async analyzeScreenshot(dataUrl, prompt = 'What is in this image?') {
    console.log('[ScreenshotAutomation] Analyzing screenshot with prompt:', prompt);

    try {
      const result = await this.sendRequest('analyze', { dataUrl, prompt });
      console.log('[ScreenshotAutomation] Analysis complete');
      return result;
    } catch (error) {
      console.error('[ScreenshotAutomation] Analysis failed:', error);
      throw error;
    }
  }

  /**
   * Capture and analyze in one step
   */
  async captureAndAnalyze(captureOptions = {}, prompt = 'What is in this image?') {
    try {
      // Capture screenshot
      const screenshot = await this.captureScreenshot(captureOptions);

      // Analyze it
      const analysis = await this.analyzeScreenshot(screenshot.dataUrl, prompt);

      return {
        screenshot,
        analysis
      };
    } catch (error) {
      console.error('[ScreenshotAutomation] Capture and analyze failed:', error);
      throw error;
    }
  }

  /**
   * Get available capture sources
   */
  async getSources() {
    try {
      const result = await this.sendRequest('sources');
      return result;
    } catch (error) {
      console.error('[ScreenshotAutomation] Failed to get sources:', error);
      throw error;
    }
  }

  /**
   * Save screenshot to file
   */
  async saveScreenshot(dataUrl, filename) {
    try {
      const result = await this.sendRequest('save', { dataUrl, filename });
      console.log('[ScreenshotAutomation] Screenshot saved:', result.path);
      return result.path;
    } catch (error) {
      console.error('[ScreenshotAutomation] Save failed:', error);
      throw error;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      console.log('[ScreenshotAutomation] Attempting to reconnect...');
      this.connect().catch(err => {
        console.error('[ScreenshotAutomation] Reconnection failed:', err);
      });
    }, this.reconnectInterval);
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
    this.pendingRequests.clear();
  }

  /**
   * Automated screenshot workflow for voice commands
   */
  async voiceTriggeredCapture(command) {
    console.log('[ScreenshotAutomation] Voice triggered capture:', command);

    try {
      // Parse voice command for context
      const captureOptions = this.parseVoiceCommand(command);

      // Determine analysis prompt based on command
      const prompt = this.generateAnalysisPrompt(command);

      // Execute capture and analysis
      const result = await this.captureAndAnalyze(captureOptions, prompt);

      // Emit result for voice agent to speak
      this.emit('voice-result', {
        command,
        analysis: result.analysis,
        screenshot: result.screenshot
      });

      return result;
    } catch (error) {
      console.error('[ScreenshotAutomation] Voice capture failed:', error);
      this.emit('voice-error', error);
      throw error;
    }
  }

  /**
   * Parse voice command to determine capture options
   */
  parseVoiceCommand(command) {
    const options = {
      type: 'screen',
      quality: 'high'
    };

    // Check for window capture
    if (command.toLowerCase().includes('window')) {
      options.type = 'window';
    }

    // Check for save request
    if (command.toLowerCase().includes('save')) {
      options.saveToFile = true;
      options.filename = `voice-capture-${Date.now()}.png`;
    }

    return options;
  }

  /**
   * Generate analysis prompt based on voice command
   */
  generateAnalysisPrompt(command) {
    const lowerCommand = command.toLowerCase();

    if (lowerCommand.includes('read')) {
      return 'Please read and summarize the text content in this screenshot.';
    } else if (lowerCommand.includes('describe')) {
      return 'Please describe what you see in this screenshot in detail.';
    } else if (lowerCommand.includes('code')) {
      return 'Please analyze any code visible in this screenshot and explain what it does.';
    } else if (lowerCommand.includes('error')) {
      return 'Please identify and explain any errors or issues visible in this screenshot.';
    } else if (lowerCommand.includes('ui') || lowerCommand.includes('design')) {
      return 'Please analyze the UI/design elements in this screenshot.';
    } else {
      return 'What is shown in this screenshot? Please provide a helpful analysis.';
    }
  }

  /**
   * Batch capture multiple screenshots
   */
  async batchCapture(sources, options = {}) {
    const results = [];

    for (const source of sources) {
      try {
        const screenshot = await this.captureScreenshot({
          ...options,
          sourceId: source.id
        });
        results.push({
          source,
          screenshot,
          success: true
        });
      } catch (error) {
        results.push({
          source,
          error: error.message,
          success: false
        });
      }
    }

    return results;
  }
}

module.exports = ScreenshotAutomation;