const { desktopCapturer, ipcMain, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const { app } = require('electron');

class DesktopCaptureService {
  constructor() {
    this.captureWindow = null;
    this.initializeHandlers();
    console.log('[Capture] Desktop capture service initialized');
  }

  initializeHandlers() {
    // Handle screenshot requests
    ipcMain.handle('capture-screenshot', async (event, options = {}) => {
      console.log('[Capture] Screenshot requested with options:', options);

      try {
        const screenshot = await this.captureScreen(options);
        console.log('[Capture] Screenshot captured successfully');
        return screenshot;
      } catch (error) {
        console.error('[Capture] Failed to capture screenshot:', error);
        throw error;
      }
    });

    // Get available sources
    ipcMain.handle('get-capture-sources', async () => {
      try {
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
        console.error('[Capture] Failed to get sources:', error);
        throw error;
      }
    });

    // Capture specific window
    ipcMain.handle('capture-window', async (event, windowId) => {
      try {
        const sources = await desktopCapturer.getSources({
          types: ['window'],
          thumbnailSize: { width: 1920, height: 1080 }
        });

        const source = sources.find(s => s.id === windowId);
        if (!source) {
          throw new Error(`Window with ID ${windowId} not found`);
        }

        return {
          dataUrl: source.thumbnail.toDataURL(),
          name: source.name,
          id: source.id
        };
      } catch (error) {
        console.error('[Capture] Failed to capture window:', error);
        throw error;
      }
    });

    // Save screenshot to file
    ipcMain.handle('save-screenshot', async (event, dataUrl, filename) => {
      try {
        const screenshotsDir = path.join(app.getPath('userData'), 'screenshots');
        await fs.mkdir(screenshotsDir, { recursive: true });

        const filePath = path.join(
          screenshotsDir,
          filename || `screenshot-${Date.now()}.png`
        );

        // Convert data URL to buffer
        const base64Data = dataUrl.replace(/^data:image\/\w+;base64,/, '');
        const buffer = Buffer.from(base64Data, 'base64');

        await fs.writeFile(filePath, buffer);
        console.log(`[Capture] Screenshot saved to: ${filePath}`);

        return filePath;
      } catch (error) {
        console.error('[Capture] Failed to save screenshot:', error);
        throw error;
      }
    });
  }

  async captureScreen(options = {}) {
    const {
      type = 'screen', // 'screen', 'window', or 'selection'
      sourceId = null,
      saveToFile = false,
      filename = null,
      quality = 'high'
    } = options;

    try {
      let sources = [];

      if (type === 'screen' || !sourceId) {
        // Capture entire screen
        sources = await desktopCapturer.getSources({
          types: ['screen'],
          thumbnailSize: quality === 'high'
            ? { width: 3840, height: 2160 }
            : { width: 1920, height: 1080 }
        });
      } else if (type === 'window' && sourceId) {
        // Capture specific window
        sources = await desktopCapturer.getSources({
          types: ['window'],
          thumbnailSize: quality === 'high'
            ? { width: 3840, height: 2160 }
            : { width: 1920, height: 1080 }
        });
        sources = sources.filter(s => s.id === sourceId);
      }

      if (sources.length === 0) {
        throw new Error('No capture sources available');
      }

      const source = sources[0];
      const screenshot = {
        dataUrl: source.thumbnail.toDataURL(),
        size: source.thumbnail.getSize(),
        name: source.name,
        id: source.id,
        timestamp: new Date().toISOString()
      };

      // Save to file if requested
      if (saveToFile) {
        const savedPath = await this.saveScreenshot(
          screenshot.dataUrl,
          filename
        );
        screenshot.filePath = savedPath;
      }

      return screenshot;
    } catch (error) {
      console.error('[Capture] Error capturing screen:', error);
      throw error;
    }
  }

  async saveScreenshot(dataUrl, filename) {
    const screenshotsDir = path.join(app.getPath('userData'), 'screenshots');
    await fs.mkdir(screenshotsDir, { recursive: true });

    const filePath = path.join(
      screenshotsDir,
      filename || `screenshot-${Date.now()}.png`
    );

    const base64Data = dataUrl.replace(/^data:image\/\w+;base64,/, '');
    const buffer = Buffer.from(base64Data, 'base64');

    await fs.writeFile(filePath, buffer);
    return filePath;
  }

  // Create a hidden window for advanced capture operations
  async createCaptureWindow() {
    if (this.captureWindow) return this.captureWindow;

    this.captureWindow = new BrowserWindow({
      show: false,
      width: 1,
      height: 1,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false
      }
    });

    return this.captureWindow;
  }

  // Analyze screenshot with OpenAI Vision API
  async analyzeScreenshot(dataUrl, prompt = 'What is in this image?') {
    try {
      const openaiApiKey = process.env.OPENAI_API_KEY;
      if (!openaiApiKey) {
        throw new Error('OpenAI API key not configured');
      }

      // Prepare the image for OpenAI Vision API
      const base64Image = dataUrl.replace(/^data:image\/\w+;base64,/, '');

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openaiApiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-4-vision-preview',
          messages: [
            {
              role: 'user',
              content: [
                { type: 'text', text: prompt },
                {
                  type: 'image_url',
                  image_url: {
                    url: `data:image/png;base64,${base64Image}`,
                    detail: 'auto'
                  }
                }
              ]
            }
          ],
          max_tokens: 500
        })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error.message);
      }

      return data.choices[0].message.content;
    } catch (error) {
      console.error('[Capture] Failed to analyze screenshot:', error);
      throw error;
    }
  }

  // Clean up
  destroy() {
    if (this.captureWindow) {
      this.captureWindow.destroy();
      this.captureWindow = null;
    }
  }
}

module.exports = DesktopCaptureService;