# Clarity - Voice Agent with Screen Capture

A real-time voice assistant that captures screen context and provides intelligent responses using OpenAI's Realtime API and Supabase for data management.

## Prerequisites

### All Platforms
- **Node.js** (v18 or higher)
- **Python** (3.8 or higher)
- **Git**
- **Environment file** (`.env` - request from project owner)

### Platform-Specific Requirements

#### macOS
- Homebrew (recommended for package management)
- Xcode Command Line Tools (install with `xcode-select --install`)

#### Windows
- Visual Studio Build Tools or Visual Studio Community
- Windows PowerShell or Git Bash

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/akeildev/seek-clarity.git
cd Clarity
```

### 2. Environment Setup

**Important:** Request the `.env` file from the project owner. This file contains necessary API keys and configuration settings including:
- OpenAI API keys
- Supabase credentials
- Other service configurations

Once received, place the `.env` file in the root directory of the project.

### 3. Install Dependencies

#### Node.js Dependencies
```bash
npm install
```

#### Python Dependencies
```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install these packages:
```bash
pip install openai python-dotenv pyaudio numpy websockets aiohttp
```

### 4. Platform-Specific Setup

#### macOS Setup

1. **Grant Permissions**: The app requires screen recording and microphone permissions
   - Go to System Settings > Privacy & Security
   - Enable permissions for Terminal/IDE for:
     - Screen Recording
     - Microphone

2. **Install Audio Dependencies** (if needed):
   ```bash
   brew install portaudio
   ```

#### Windows Setup

1. **Grant Permissions**:
   - Windows will prompt for microphone access on first run
   - Grant the necessary permissions when prompted

2. **Install Audio Dependencies** (if needed):
   - Download and install PyAudio wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - Or use: `pip install pipwin && pipwin install pyaudio`

### 5. Running the Application

#### Start the Electron App
```bash
npm start
```

#### Run the Python Voice Agent (separate terminal)
```bash
python src/voice_agent.py
```

## Project Structure

```
Clarity/
├── src/
│   ├── main/           # Electron main process
│   │   └── services/   # Core services
│   │       ├── capture.js    # Desktop capture service
│   │       ├── websocket.js  # Screenshot WebSocket server
│   │       └── livekit.js     # Voice streaming service
│   ├── renderer/       # Electron renderer process
│   ├── preload/        # Electron preload scripts
│   ├── agent/          # Python voice agent
│   │   └── voice_agent.py    # OpenAI Realtime integration
│   ├── mcp/            # MCP server
│   │   ├── server.js   # STDIO MCP server
│   │   ├── tools.js    # Tool handlers
│   │   └── database.js # Supabase integration
│   └── automation/     # Automation modules
│       └── screenshot.js     # Screenshot automation
├── .env                # Environment variables (get from owner)
├── package.json        # Node.js dependencies
└── requirements.txt    # Python dependencies
```

## Features

- **Screen Capture**: Desktop capture service with OpenAI Vision API analysis
- **Voice Interaction**: Real-time voice conversations using OpenAI Realtime API
- **WebSocket Server**: Real-time screenshot bridge on port 8765
- **MCP Server Integration**: STDIO-based MCP server for Supabase database operations
- **Automation**: Screenshot automation with voice command support
- **Cross-platform**: Works on both macOS and Windows

## Troubleshooting

### Common Issues

#### macOS
- **"Permission denied" for screen recording**: Restart the app after granting permissions in System Settings
- **PyAudio installation fails**: Install Xcode Command Line Tools and portaudio first

#### Windows
- **PyAudio installation fails**: Use the pre-built wheel file or pipwin
- **Microphone not detected**: Check Windows Sound Settings and ensure default input device is set

### General
- **Missing .env file**: Contact the project owner for the environment configuration
- **Port already in use**: Check if another instance is running or change the port in the configuration
- **API errors**: Verify your API keys in the .env file are valid and have proper permissions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues or questions:
- Check the [Issues](https://github.com/akeildev/seek-clarity/issues) page
- Contact the project owner for .env file and API access

## License

[Include license information here]
