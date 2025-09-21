const WebSocket = require('ws');
const { ipcMain } = require('electron');
const EventEmitter = require('events');

class ScreenshotWebSocketServer extends EventEmitter {
  constructor(captureService, applescriptService = null) {
    super();
    this.captureService = captureService;
    this.applescriptService = applescriptService;
    this.wss = null;
    this.clients = new Set();
    this.port = process.env.SCREENSHOT_WS_PORT || 8765;
    this.isRunning = false;

    console.log('[WebSocket] Screenshot WebSocket server initialized');
  }

  setAppleScriptService(service) {
    this.applescriptService = service;
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
    const { action, type, payload = {}, params = {} } = message;

    // Handle cassette-style action messages
    if (action) {
      switch (action) {
        case 'capture_screenshot':
          await this.handleScreenshotRequest(ws, message);
          break;

        case 'applescript_execute':
          await this.handleAppleScriptRequest(ws, params);
          break;

        case 'create_calendar_event':
          await this.handleCalendarRequest(ws, params);
          break;

        case 'create_note':
          await this.handleNoteRequest(ws, params);
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

      // Capture screenshot using the capture service with optimized settings
      console.log('[WebSocket] Calling captureService.captureScreen...');
      const screenshot = await this.captureService.captureScreen({
        type: 'screen',
        quality: 'low', // Use low quality for smaller size (1280x720)
        compress: true   // Enable JPEG compression
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

  async handleAppleScriptRequest(ws, params) {
    try {
      console.log('[WebSocket-AppleScript] ========================================');
      console.log('[WebSocket-AppleScript] Processing AppleScript request');
      console.log('[WebSocket-AppleScript]   Code length:', params.code_snippet ? params.code_snippet.length : 0, 'characters');
      console.log('[WebSocket-AppleScript]   Code preview:', params.code_snippet ? params.code_snippet.substring(0, 200) : 'No code');
      console.log('[WebSocket-AppleScript] ========================================');

      if (!this.applescriptService) {
        console.error('[WebSocket-AppleScript] ✗ AppleScript service not available');
        throw new Error('AppleScript service not available');
      }

      if (!params.code_snippet) {
        throw new Error('No AppleScript code provided');
      }

      // Execute the AppleScript directly
      console.log('[WebSocket-AppleScript] Executing AppleScript...');
      const result = await this.applescriptService.executeScript(params.code_snippet);

      console.log('[WebSocket-AppleScript] Result:', result);

      // Send response
      const response = {
        success: result.success,
        output: result.output || '',
        error: result.error
      };

      console.log('[WebSocket-AppleScript] Sending response:', response);
      this.sendMessage(ws, response);

      console.log('[WebSocket-AppleScript] ✓ Request completed');

    } catch (error) {
      console.error('[WebSocket-AppleScript] AppleScript execution failed:', error);
      this.sendMessage(ws, {
        success: false,
        error: error.message
      });
    }
  }

  async handleCalendarRequest(ws, params) {
    try {
      console.log('[WebSocket-Calendar] ========================================');
      console.log('[WebSocket-Calendar] Processing request');
      console.log('[WebSocket-Calendar]   Title:', params.title);
      console.log('[WebSocket-Calendar]   Calendar:', params.calendar);
      console.log('[WebSocket-Calendar]   Start time:', params.start_time);
      console.log('[WebSocket-Calendar]   Duration:', params.duration, 'minutes');
      console.log('[WebSocket-Calendar] ========================================');

      if (!this.applescriptService) {
        console.error('[WebSocket-Calendar] ✗ AppleScript service not available');
        throw new Error('AppleScript service not available');
      }

      // Create calendar event using AppleScript service
      const eventOptions = {
        title: params.title,
        description: params.description || '',
        calendar: params.calendar || 'Work',
        startDate: params.start_time === 'now' ? new Date() : new Date(params.start_time),
        endDate: params.duration ? new Date(Date.now() + params.duration * 60000) : null
      };

      console.log('[WebSocket-Calendar] Calling AppleScript service with:', eventOptions);
      const result = await this.applescriptService.createCalendarEvent(eventOptions);

      console.log('[WebSocket-Calendar] AppleScript result:', result);

      // Send response
      const response = {
        success: result.success,
        message: result.output || 'Calendar event created',
        error: result.error
      };

      console.log('[WebSocket-Calendar] Sending response:', response);
      this.sendMessage(ws, response);

      console.log('[WebSocket-Calendar] ✓ Request completed');

    } catch (error) {
      console.error('[WebSocket] Calendar event creation failed:', error);
      this.sendMessage(ws, {
        success: false,
        error: error.message
      });
    }
  }

  async handleNoteRequest(ws, params) {
    try {
      console.log('[WebSocket] Processing note creation request:', params);

      if (!this.applescriptService) {
        throw new Error('AppleScript service not available');
      }

      // Create note using AppleScript service
      const result = await this.applescriptService.createNote({
        title: params.title,
        body: params.body || params.content || '',
        folder: 'Notes'
      });

      // Send response
      this.sendMessage(ws, {
        success: result.success,
        message: result.output || 'Note created',
        error: result.error
      });

      console.log('[WebSocket] Note created');

    } catch (error) {
      console.error('[WebSocket] Note creation failed:', error);
      this.sendMessage(ws, {
        success: false,
        error: error.message
      });
    }
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