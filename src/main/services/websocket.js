const WebSocket = require('ws');
const { ipcMain } = require('electron');
const EventEmitter = require('events');

class ScreenshotWebSocketServer extends EventEmitter {
  constructor(captureService) {
    super();
    this.captureService = captureService;
    this.wss = null;
    this.clients = new Set();
    this.port = process.env.SCREENSHOT_WS_PORT || 8765;
    this.isRunning = false;

    console.log('[WebSocket] Screenshot WebSocket server initialized');
  }

  start() {
    if (this.isRunning) {
      console.log('[WebSocket] Server already running');
      return;
    }

    try {
      this.wss = new WebSocket.Server({ port: this.port });
      this.isRunning = true;

      this.wss.on('connection', (ws, req) => {
        const clientId = this.generateClientId();
        const clientIp = req.socket.remoteAddress;

        console.log(`[WebSocket] Client connected: ${clientId} from ${clientIp}`);

        ws.clientId = clientId;
        this.clients.add(ws);

        // Don't send welcome message to avoid confusion with screenshot responses
        // The client can send a ping if it wants to test the connection

        // Handle messages from client
        ws.on('message', async (data) => {
          try {
            console.log(`[WebSocket] Raw message from ${clientId}:`, data.toString());
            const message = JSON.parse(data.toString());
            console.log(`[WebSocket] Parsed message from ${clientId}:`, JSON.stringify(message, null, 2));
            await this.handleMessage(ws, message);
          } catch (error) {
            console.error('[WebSocket] Error processing message:', error);
            console.error('[WebSocket] Raw data that failed to parse:', data.toString());
            this.sendError(ws, 'Invalid message format');
          }
        });

        // Handle client disconnect
        ws.on('close', () => {
          console.log(`[WebSocket] Client disconnected: ${clientId}`);
          this.clients.delete(ws);
        });

        // Handle errors
        ws.on('error', (error) => {
          console.error(`[WebSocket] Client error ${clientId}:`, error);
          this.clients.delete(ws);
        });

        // Setup heartbeat
        ws.isAlive = true;
        ws.on('pong', () => {
          ws.isAlive = true;
        });
      });

      // Start heartbeat interval
      this.startHeartbeat();

      console.log(`[WebSocket] Server started on port ${this.port}`);
      this.emit('started', { port: this.port });

    } catch (error) {
      console.error('[WebSocket] Failed to start server:', error);
      this.isRunning = false;
      throw error;
    }
  }

  async handleMessage(ws, message) {
    const { action, type, payload = {} } = message;

    // Handle cassette-style action messages
    if (action) {
      switch (action) {
        case 'capture_screenshot':
          await this.handleScreenshotRequest(ws, message);
          break;

        case 'ping':
          this.sendMessage(ws, { success: true, action: 'pong' });
          break;

        default:
          this.sendMessage(ws, { success: false, error: `Unknown action: ${action}` });
      }
      return;
    }

    // Handle original type-based messages
    switch (type) {
      case 'capture':
        await this.handleCaptureRequest(ws, payload);
        break;

      case 'analyze':
        await this.handleAnalyzeRequest(ws, payload);
        break;

      case 'sources':
        await this.handleSourcesRequest(ws);
        break;

      case 'save':
        await this.handleSaveRequest(ws, payload);
        break;

      case 'ping':
        this.sendMessage(ws, { type: 'pong', timestamp: Date.now() });
        break;

      default:
        this.sendError(ws, `Unknown message type: ${type}`);
    }
  }

  async handleScreenshotRequest(ws, request) {
    try {
      console.log('[WebSocket] Processing screenshot request (cassette format):', request);

      // Validate capture service
      if (!this.captureService) {
        throw new Error('Capture service not available');
      }

      // Capture screenshot using the capture service
      console.log('[WebSocket] Calling captureService.captureScreen...');
      const screenshot = await this.captureService.captureScreen({
        type: 'screen',
        quality: 'high'
      });

      console.log('[WebSocket] Screenshot captured, processing response...');
      console.log('[WebSocket] Screenshot object keys:', Object.keys(screenshot || {}));

      if (!screenshot || !screenshot.dataUrl) {
        throw new Error('Screenshot capture returned invalid data');
      }

      // Extract base64 from dataURL (remove data:image/png;base64, prefix)
      const base64Data = screenshot.dataUrl.replace(/^data:image\/\w+;base64,/, '');

      // Send cassette-style response
      const response = {
        success: true,
        base64: base64Data,
        requestId: request.requestId,
        timestamp: new Date().toISOString()
      };

      console.log('[WebSocket] Sending response with base64 length:', base64Data.length);
      this.sendMessage(ws, response);

      console.log('[WebSocket] Screenshot sent to client (cassette format)');

    } catch (error) {
      console.error('[WebSocket] Screenshot capture failed:', error);
      console.error('[WebSocket] Error stack:', error.stack);
      this.sendMessage(ws, {
        success: false,
        error: error.message,
        requestId: request.requestId
      });
    }
  }

  async handleCaptureRequest(ws, options) {
    try {
      console.log('[WebSocket] Processing capture request:', options);

      // Capture screenshot using the capture service
      const screenshot = await this.captureService.captureScreen(options);

      // Send screenshot back to client
      this.sendMessage(ws, {
        type: 'screenshot',
        data: screenshot,
        timestamp: new Date().toISOString()
      });

      console.log('[WebSocket] Screenshot sent to client');

    } catch (error) {
      console.error('[WebSocket] Capture failed:', error);
      this.sendError(ws, `Capture failed: ${error.message}`);
    }
  }

  async handleAnalyzeRequest(ws, payload) {
    const { dataUrl, prompt = 'What is in this image?' } = payload;

    if (!dataUrl) {
      this.sendError(ws, 'No image data provided for analysis');
      return;
    }

    try {
      console.log('[WebSocket] Analyzing screenshot with prompt:', prompt);

      // Send processing status
      this.sendMessage(ws, {
        type: 'status',
        message: 'Analyzing image...',
        timestamp: new Date().toISOString()
      });

      // Analyze with OpenAI Vision
      const analysis = await this.captureService.analyzeScreenshot(dataUrl, prompt);

      // Send analysis result
      this.sendMessage(ws, {
        type: 'analysis',
        result: analysis,
        prompt: prompt,
        timestamp: new Date().toISOString()
      });

      console.log('[WebSocket] Analysis sent to client');

    } catch (error) {
      console.error('[WebSocket] Analysis failed:', error);
      this.sendError(ws, `Analysis failed: ${error.message}`);
    }
  }

  async handleSourcesRequest(ws) {
    try {
      // Get available capture sources
      const sources = await new Promise((resolve, reject) => {
        ipcMain.handle('get-capture-sources', async () => {
          try {
            const { desktopCapturer } = require('electron');
            const sources = await desktopCapturer.getSources({
              types: ['window', 'screen'],
              thumbnailSize: { width: 320, height: 180 }
            });

            return sources.map(source => ({
              id: source.id,
              name: source.name,
              thumbnail: source.thumbnail.toDataURL(),
              display_id: source.display_id
            }));
          } catch (error) {
            reject(error);
          }
        });

        // Trigger the handler
        ipcMain.emit('get-capture-sources');
      });

      this.sendMessage(ws, {
        type: 'sources',
        data: sources,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('[WebSocket] Failed to get sources:', error);
      this.sendError(ws, `Failed to get sources: ${error.message}`);
    }
  }

  async handleSaveRequest(ws, payload) {
    const { dataUrl, filename } = payload;

    if (!dataUrl) {
      this.sendError(ws, 'No image data provided to save');
      return;
    }

    try {
      const savedPath = await this.captureService.saveScreenshot(dataUrl, filename);

      this.sendMessage(ws, {
        type: 'saved',
        path: savedPath,
        timestamp: new Date().toISOString()
      });

      console.log(`[WebSocket] Screenshot saved: ${savedPath}`);

    } catch (error) {
      console.error('[WebSocket] Save failed:', error);
      this.sendError(ws, `Save failed: ${error.message}`);
    }
  }

  // Broadcast message to all connected clients
  broadcast(message) {
    const messageStr = JSON.stringify(message);

    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(messageStr);
      }
    });
  }

  // Send message to specific client
  sendMessage(ws, message) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  // Send error message to client
  sendError(ws, error) {
    this.sendMessage(ws, {
      type: 'error',
      error: error,
      timestamp: new Date().toISOString()
    });
  }

  // Heartbeat mechanism to detect disconnected clients
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.clients.forEach(ws => {
        if (!ws.isAlive) {
          console.log(`[WebSocket] Client ${ws.clientId} heartbeat failed, terminating`);
          this.clients.delete(ws);
          return ws.terminate();
        }

        ws.isAlive = false;
        ws.ping();
      });
    }, 30000); // 30 seconds
  }

  // Generate unique client ID
  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Stop the WebSocket server
  stop() {
    if (!this.isRunning) return;

    console.log('[WebSocket] Stopping server...');

    // Clear heartbeat interval
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // Close all client connections
    this.clients.forEach(client => {
      this.sendMessage(client, {
        type: 'server_closing',
        message: 'Server is shutting down',
        timestamp: new Date().toISOString()
      });
      client.close();
    });

    this.clients.clear();

    // Close the server
    if (this.wss) {
      this.wss.close(() => {
        console.log('[WebSocket] Server stopped');
        this.emit('stopped');
      });
      this.wss = null;
    }

    this.isRunning = false;
  }

  // Get server status
  getStatus() {
    return {
      isRunning: this.isRunning,
      port: this.port,
      clientCount: this.clients.size,
      clients: Array.from(this.clients).map(ws => ({
        id: ws.clientId,
        readyState: ws.readyState,
        isAlive: ws.isAlive
      }))
    };
  }
}

module.exports = ScreenshotWebSocketServer;