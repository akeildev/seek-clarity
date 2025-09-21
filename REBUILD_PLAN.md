# Cassette → Clarity: Complete 4-Hour Progressive Rebuild Plan

## Overview
Transform the retro cassette tape UI into a modern, glassy liquid overlay with pill design. This comprehensive plan includes ALL components: AI agent, MCP server, AppleScript automation, and voice capabilities.

## Complete System Architecture (from /Users/akeilsmith/cassette)

### Complete Component Inventory:

1. **ELECTRON CORE**
   - Main Process (`src/main/main.js`)
   - Window Service (`src/main/services/WindowService.js`)
   - Settings Service (`src/main/services/SettingsService.js`)
   - Config Service (`src/main/services/ConfigService.js`)

2. **AI VOICE AGENT** (`src/agent/`)
   - **voice_agent.py**: OpenAI Realtime + ElevenLabs TTS + Silero VAD
   - **mcp_router.py**: MCP tool routing and execution
   - **mcp_utils.py**: Voice interaction helpers
   - **mcp_logger.py**: Error logging system
   - Python requirements: livekit, openai, elevenlabs

3. **MCP SERVER** (`src/mcp-server/`)
   - Course navigation tools
   - Supabase integration
   - Tool definitions and handlers
   - STDIO transport for agent communication

4. **LIVEKIT VOICE SYSTEM**
   - LiveKitService.js: Token generation, room management
   - livekitClient.js: WebRTC audio streaming
   - Voice agent spawning (Python subprocess)
   - Real-time audio level monitoring

5. **DESKTOP CAPTURE & AUTOMATION**
   - **desktopCaptureService.js**: Screen capture API
   - **screenshotWebSocketServer.js**: WebSocket bridge (port 8765)
   - **AppleScript Integration**: Calendar events, Notes creation
   - Screenshot analysis via OpenAI Vision API

6. **UI COMPONENTS** (`src/renderer/`)
   - Cassette tape visualization → Glass pill
   - Audio visualizer (LED → liquid waves)
   - Voice controls (REC/MUTE buttons)
   - Draggable transparent window

7. **TRADING/MONEYFI MODULE**
   - **moneyfi_trading_algorithm.py**: Options trading logic
   - AppleScript calendar scheduling
   - Educational course integration

## Complete Folder Structure

```
/Users/akeilsmith/Clarity/
├── package.json                 # Node dependencies
├── .env                         # API keys (LiveKit, OpenAI, ElevenLabs)
├── requirements.txt             # Python dependencies
├──
├── /src/
│   ├── /main/                  # Electron main process
│   │   ├── index.js            # Main entry point
│   │   ├── window.js           # Window management
│   │   └── /services/
│   │       ├── livekit.js     # LiveKit service
│   │       ├── settings.js    # Settings management
│   │       ├── capture.js     # Desktop capture
│   │       └── websocket.js   # Screenshot WebSocket
│   │
│   ├── /renderer/              # Glass pill UI
│   │   ├── index.html         # Main UI
│   │   ├── app.js             # Core app logic
│   │   ├── /styles/
│   │   │   ├── glass.css     # Glassmorphism
│   │   │   └── liquid.css    # Liquid animations
│   │   └── /modules/
│   │       ├── voice.js       # Voice controls
│   │       ├── visualizer.js  # Audio waves
│   │       └── livekit.js     # LiveKit client
│   │
│   ├── /agent/                 # Python AI agent
│   │   ├── main.py            # Agent entry point
│   │   ├── voice.py           # Voice processing
│   │   ├── mcp.py             # MCP integration
│   │   ├── tools.py           # Tool definitions
│   │   └── config.json        # Agent config
│   │
│   ├── /mcp/                   # MCP server
│   │   ├── server.js          # MCP server
│   │   ├── tools.js           # Tool handlers
│   │   └── database.js        # Supabase client
│   │
│   ├── /automation/            # System automation
│   │   ├── screenshot.js      # Screenshot handler
│   │   ├── calendar.applescript
│   │   └── notes.applescript
│   │
│   └── /shared/                # Shared code
│       ├── constants.js
│       ├── ipc.js             # IPC events
│       └── utils.js
```

## UI Design Specifications

### Glassy Pill Design (Replacing Cassette Tape)
**Reference:** `src/renderer/styles.css:41-53` (current container)

```css
/* New Glass Morphism Pill */
.clarity-pill {
  /* Dimensions */
  width: 320px;
  height: 80px;

  /* Glass effect */
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);

  /* Borders & shadows */
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 40px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.12),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}
```

### Liquid Overlay Animation
**Inspired by:** `src/renderer/audioVisualizer.js` LED visualization
- Transform discrete LEDs into fluid wave animation
- Use canvas for smooth liquid effect
- Respond to audio levels with ripple effects

## 4-HOUR PROGRESSIVE REBUILD PHASES

### HOUR 1: Foundation & Glass UI (Commits every 15min)

#### Phase 1.1: Project Setup (0-15 min)
**Actions:**
1. Initialize Clarity project structure
2. Copy core dependencies
3. Set up Electron main process

**Files to create:**
- `package.json` (from cassette/package.json)
- `src/main/index.js` (from cassette/src/main/main.js:1-100)
- `src/main/window.js` (from cassette/src/main/services/WindowService.js)
- `.env` template

**Commit 1:** "Initialize Clarity project with Electron foundation"

#### Phase 1.2: Glass Pill UI Base (15-30 min)
**Actions:**
1. Create glass morphism HTML structure
2. Implement transparent pill container
3. Add draggable window region

**Files to create:**
- `src/renderer/index.html` (transform from cassette/src/renderer/index.html)
- `src/renderer/styles/glass.css` (new glass design)

**Reference:** cassette/src/renderer/styles.css:41-73 for container structure

**Commit 2:** "Add glass pill UI with transparent overlay"

#### Phase 1.3: Liquid Animations (30-45 min)
**Actions:**
1. Create liquid wave animations
2. Add glass refraction effects
3. Implement smooth transitions

**Files to create:**
- `src/renderer/styles/liquid.css`
- `src/renderer/modules/visualizer.js` (base structure)

**Reference:** cassette/src/renderer/audioVisualizer.js

**Commit 3:** "Implement liquid wave animations and glass effects"

#### Phase 1.4: UI Controls & Interactions (45-60 min)
**Actions:**
1. Add voice/mute buttons with glass style
2. Implement hover effects and ripples
3. Window controls (close/minimize)

**Files to create:**
- `src/renderer/app.js` (from cassette/src/renderer/index.js:1-100)
- `src/renderer/modules/controls.js`

**Commit 4:** "Add interactive controls with glass styling"

---

### HOUR 2: Voice & LiveKit Integration (Commits every 15min)

#### Phase 2.1: LiveKit Service Setup (60-75 min)
**Actions:**
1. Port LiveKit service from cassette
2. Set up token generation
3. Configure room management

**Files to create:**
- `src/main/services/livekit.js` (from cassette/src/main/services/LiveKitService.js:1-150)
- `src/shared/constants.js`

**Commit 5:** "Integrate LiveKit voice service"

#### Phase 2.2: Voice Client Implementation (75-90 min)
**Actions:**
1. Create LiveKit client module
2. Connect WebRTC audio streaming
3. Handle connection states

**Files to create:**
- `src/renderer/modules/livekit.js` (from cassette/src/renderer/livekitClient.js)
- `src/renderer/modules/voice.js`

**Reference:** cassette/src/renderer/index.js:73-140

**Commit 6:** "Implement LiveKit client for voice streaming"

#### Phase 2.3: Audio Visualization Integration (90-105 min)
**Actions:**
1. Connect audio levels to visualizer
2. Implement real-time wave updates
3. Add smooth interpolation

**Files to update:**
- `src/renderer/modules/visualizer.js` (complete implementation)

**Reference:** cassette/src/renderer/audioVisualizer.js:50-150

**Commit 7:** "Connect audio levels to liquid visualization"

#### Phase 2.4: IPC Communication (105-120 min)
**Actions:**
1. Set up IPC events for voice control
2. Handle settings and state management
3. Error handling and reconnection

**Files to create:**
- `src/shared/ipc.js` (from cassette/src/main/main.js:159-300)
- `src/main/services/settings.js` (from cassette/src/main/services/SettingsService.js)

**Commit 8:** "Implement IPC communication layer"

---

### HOUR 3: AI Agent & MCP Integration (Commits every 15min)

#### Phase 3.1: Python Agent Setup (120-135 min)
**Actions:**
1. Create Python agent structure
2. Port voice agent from cassette
3. Set up OpenAI/ElevenLabs integration

**Files to create:**
- `src/agent/main.py` (from cassette/src/agent/voice_agent.py:1-100)
- `src/agent/voice.py` (core voice logic)
- `requirements.txt`

**Commit 9:** "Add Python AI voice agent foundation"

#### Phase 3.2: MCP Router Implementation (135-150 min)
**Actions:**
1. Port MCP router and utilities
2. Set up tool execution framework
3. Configure logging

**Files to create:**
- `src/agent/mcp.py` (from cassette/src/agent/mcp_router.py)
- `src/agent/tools.py` (from cassette/src/agent/mcp_utils.py)
- `src/agent/config.json`

**Commit 10:** "Implement MCP tool routing system"

#### Phase 3.3: MCP Server Setup (150-165 min)
**Actions:**
1. Create MCP server with STDIO transport
2. Port course navigation tools
3. Set up Supabase integration

**Files to create:**
- `src/mcp/server.js` (from cassette/src/mcp-server/src/index.js)
- `src/mcp/tools.js` (from cassette/src/mcp-server/src/tools.js)

**Commit 11:** "Add MCP server with tool definitions"

#### Phase 3.4: Agent-Electron Bridge (165-180 min)
**Actions:**
1. Connect Python agent to Electron
2. Handle subprocess spawning
3. Set up bidirectional communication

**Files to update:**
- `src/main/services/livekit.js` (add agent spawning)

**Reference:** cassette/src/main/services/LiveKitService.js:82-180

**Commit 12:** "Bridge Python agent with Electron process"

---

### HOUR 4: Automation & Polish (Commits every 15min)

#### Phase 4.1: Screenshot Service (180-195 min)
**Actions:**
1. Port desktop capture service
2. Set up WebSocket bridge
3. Integrate OpenAI Vision API

**Files to create:**
- `src/main/services/capture.js` (from cassette/src/main/services/desktopCaptureService.js)
- `src/main/services/websocket.js` (from cassette/src/main/services/screenshotWebSocketServer.js)
- `src/automation/screenshot.js`

**Commit 13:** "Add screenshot capture with WebSocket bridge"

#### Phase 4.2: AppleScript Automation (195-210 min)
**Actions:**
1. Port calendar integration
2. Add Notes creation capability
3. Set up automation triggers

**Files to create:**
- `src/automation/calendar.applescript` (from cassette/test-calendar-notes.applescript)
- `src/automation/notes.applescript`

**Reference:** cassette/test-calendar-notes.applescript

**Commit 14:** "Integrate AppleScript automation for calendar/notes"

#### Phase 4.3: Settings & Persistence (210-225 min)
**Actions:**
1. Complete settings service
2. Add window position memory
3. Store user preferences

**Files to update:**
- `src/main/services/settings.js` (complete implementation)

**Reference:** cassette/src/main/services/SettingsService.js

**Commit 15:** "Add settings persistence with electron-store"

#### Phase 4.4: Final Polish & Testing (225-240 min)
**Actions:**
1. Error handling improvements
2. Performance optimizations
3. Add startup/shutdown handlers
4. Final UI tweaks

**Files to update:**
- All core files for error handling
- Add try-catch blocks
- Optimize render loops

**Commit 16:** "Final polish, error handling, and optimizations"

---

## Environment Variables (.env)

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# AI Services
OPENAI_API_KEY=your-openai-key
ELEVEN_API_KEY=your-elevenlabs-key
ELEVEN_VOICE_ID=voice-id
ELEVEN_MODEL_ID=eleven_turbo_v2_5

# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key

# WebSocket
SCREENSHOT_WS_PORT=8765
```

## Key Transformations per Hour

**Hour 1:** Visual transformation (cassette → glass pill)
**Hour 2:** Voice system (LiveKit integration)
**Hour 3:** AI brain (Python agent + MCP)
**Hour 4:** Automation & polish (screenshots, AppleScript)

## Success Checklist
- [ ] 16 commits over 4 hours
- [ ] Glass pill UI with liquid animations
- [ ] Working voice with LiveKit
- [ ] Python AI agent integrated
- [ ] MCP server running
- [ ] Screenshot capture working
- [ ] AppleScript automation
- [ ] Settings persistence
- [ ] Clean folder structure

## Implementation Notes

### Key Transformations:
1. **Visual**: Cassette tape → Glass pill
2. **Colors**: Retro browns/blacks → Transparent whites/glass
3. **Animation**: Discrete LEDs → Fluid waves
4. **Layout**: Complex tape reels → Simple pill with 2 buttons
5. **Textures**: Plastic/mechanical → Glass/liquid

### Dependencies to Keep:
- electron: ^38.1.0
- @supabase/supabase-js: ^2.57.4
- livekit-server-sdk: ^2.13.3
- electron-store: ^10.1.0
- dotenv: ^17.2.2

### Dependencies to Remove:
- Test frameworks
- Python agent requirements
- Unnecessary UI libraries

### Critical Files for Reference:
1. **Window Setup**: `/cassette/src/main/main.js:49-73`
2. **IPC Events**: `/cassette/src/main/main.js:159-300`
3. **Voice Logic**: `/cassette/src/renderer/index.js:146-182`
4. **LiveKit Client**: `/cassette/src/renderer/livekitClient.js`
5. **Current Styles**: `/cassette/src/renderer/styles.css`

## Success Metrics
- [ ] Clean, minimal folder structure
- [ ] Glass morphism UI with liquid animations
- [ ] Working voice recording via LiveKit
- [ ] Smooth audio visualization
- [ ] <500 lines of core code (excluding node_modules)
- [ ] Single HTML, 2 CSS files, 3-4 JS modules