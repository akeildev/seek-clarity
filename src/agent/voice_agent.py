#!/usr/bin/env python3
"""
Clarity Voice Agent - LiveKit integration with OpenAI Realtime and ElevenLabs
"""

import asyncio
import logging
import os
import json
import uuid
import websockets
import base64
from typing import Optional, Dict, Any
from datetime import datetime
import sys

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    RunContext,
    Agent,
    JobRequest,
)
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, elevenlabs, silero
from openai.types.beta.realtime.session import InputAudioTranscription
from dotenv import load_dotenv
from pathlib import Path
from mcp_router import McpToolRouter
# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('clarity_agent.log')
    ]
)
logger = logging.getLogger("clarity-agent")

# Also configure LiveKit logging
lk_logger = logging.getLogger("livekit")
lk_logger.setLevel(logging.INFO)

# Import reading environment after logger is configured
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reading_environmnet'))

try:
    from reading_agent import ReadingAgent, QueryData
    READING_ENABLED = True
    logger.info("Reading environment integration enabled")
except ImportError as e:
    READING_ENABLED = False
    logger.warning(f"Reading environment not available: {e}")
    ReadingAgent = None
    QueryData = None


class ClarityVoiceAgent:
    """Voice agent for Clarity assistant"""

    def __init__(self):
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.room_name: Optional[str] = None
        self.participant_identity: Optional[str] = None

        # Initialize MCP router for tool access
        config_path = Path(__file__).parent / "mcp.config.json"
        logger.info(f"Attempting to load MCP config from: {config_path}")
        try:
            self.mcp_router = McpToolRouter(config_path)
            tools = self.mcp_router.list_tools()
            logger.info(f"Loaded {len(tools)} MCP tools")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP router: {e}")
            self.mcp_router = McpToolRouter()  # Initialize empty router
            logger.warning("Continuing with empty MCP router")

        # Initialize reading agent if available
        self.reading_agent = None
        if READING_ENABLED and ReadingAgent:
            try:
                self.reading_agent = ReadingAgent()
                logger.info("Reading agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize reading agent: {e}")
                self.reading_agent = None

        # WebSocket connection for screen capture
        self.screenshot_ws = None
        self.screenshot_ws_url = "ws://localhost:8765"

    async def start(self, ctx: JobContext):
        """Initialize and start the agent session"""
        logger.info("="*50)
        logger.info("Starting Clarity voice agent")
        logger.info("="*50)
        self.context = ctx

        # Extract room and participant info
        self.room_name = ctx.room.name
        logger.info(f"Room name: {self.room_name}")

        participants = list(ctx.room.remote_participants.values())
        logger.info(f"Participants in room: {len(participants)}")
        if participants:
            self.participant_identity = participants[0].identity
            logger.info(f"Participant joined: {self.participant_identity}")
        else:
            logger.warning("No participants found in room yet")

        # Connect to room
        logger.info("Connecting to LiveKit room...")
        try:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
            logger.info(f"✓ Connected to room: {self.room_name}")
            logger.info(f"Room connection state: {ctx.room.connection_state}")
            logger.info(f"Number of participants: {len(list(ctx.room.remote_participants.values()))}")

            # Check if this is our target room (rooms starting with "clarity-")
            if self.room_name.startswith("clarity-"):
                logger.info(f"✓ Detected target room: {self.room_name}")
            else:
                logger.info(f"Room {self.room_name} is not a target room, waiting for target room...")

        except Exception as e:
            logger.error(f"Failed to connect to room: {e}")
            raise

        # Get API keys from environment
        logger.info("Loading API keys from environment...")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        eleven_api_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        eleven_voice_id = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

        # Log API key status (masked)
        if openai_api_key:
            logger.info(f"✓ OpenAI API key found: sk-...{openai_api_key[-4:]}")
        else:
            logger.error("✗ OPENAI_API_KEY not set")
            return

        if eleven_api_key:
            logger.info(f"✓ ElevenLabs API key found: ...{eleven_api_key[-4:]}")
            logger.info(f"  Voice ID: {eleven_voice_id}")
        else:
            logger.warning("⚠ ElevenLabs API key not set - TTS will be disabled")

        # Create voice session with OpenAI Realtime
        logger.info("="*50)
        logger.info("Creating voice session with OpenAI Realtime")
        logger.info("Configuration:")
        logger.info("  Model: gpt-4o-realtime-preview")
        logger.info(f"  TTS: {'ElevenLabs' if eleven_api_key else 'Disabled'}")
        logger.info("  VAD: Silero")
        logger.info("="*50)

        try:
            logger.info("Creating AgentSession with OpenAI Realtime...")
            self.session = AgentSession(
                llm=openai.realtime.RealtimeModel(
                    model="gpt-4o-realtime-preview",
                    modalities=["text", "audio"],
                    input_audio_transcription=InputAudioTranscription(
                        model="whisper-1",
                        language="en",
                    ),
                ),
                tts=elevenlabs.TTS(
                    voice_id=eleven_voice_id,
                    model="eleven_turbo_v2_5",
                    api_key=eleven_api_key,
                ) if eleven_api_key else None,
                vad=silero.VAD.load(
                    min_speech_duration=0.2,
                    min_silence_duration=0.5,
                    activation_threshold=0.5,
                ),
            )
            logger.info("✓ AgentSession created successfully")

            # Create basic Agent with system instructions
            logger.info("Creating Agent with instructions...")
            agent = Agent(
                instructions=self._get_instructions(),
            )
            logger.info("✓ Agent created successfully")

            # Start the session
            logger.info("Starting agent session...")
            try:
                await self.session.start(agent=agent, room=ctx.room)
                logger.info("✓ Voice session started successfully")
                logger.info("Agent is now listening for speech...")

                # Send greeting
                await self._send_greeting()
            except Exception as session_error:
                logger.error(f"Failed to start session: {session_error}")
                logger.error(f"Session error type: {type(session_error)}")
                raise

        except Exception as e:
            logger.error(f"Failed to create/start session: {e}")
            raise

    async def _send_greeting(self):
        """Send initial greeting"""
        greeting = "Hello! I'm Clarity, your AI assistant. I can help you create notes, search information, and manage tasks. How can I help you today?"
        if self.session:
            logger.info("Sending greeting message...")
            try:
                await self.session.say(greeting)
                logger.info("✓ Greeting sent successfully")
            except Exception as e:
                logger.error(f"Failed to send greeting: {e}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result"""
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            # Handle screenshot tools directly
            if tool_name == "capture_screenshot":
                return await self.capture_screenshot(arguments.get('options', {}))
            elif tool_name == "analyze_screenshot":
                return await self.analyze_screenshot(arguments.get('dataUrl'), arguments.get('prompt', 'What is in this image?'))

            # Execute the tool through MCP router
            result = await self.mcp_router.execute_tool(tool_name, arguments)
            logger.info(f"Tool execution result: {result}")
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"I encountered an error: {str(e)}"

    async def connect_to_screenshot_service(self):
        """Connect to the screenshot WebSocket service"""
        try:
            if self.screenshot_ws is None or self.screenshot_ws.closed:
                self.screenshot_ws = await websockets.connect(self.screenshot_ws_url)
                logger.info("Connected to screenshot WebSocket service")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to screenshot service: {e}")
            return False

    async def capture_screenshot(self, options: Dict[str, Any] = None) -> str:
        """Capture a screenshot using the WebSocket bridge"""
        try:
            if not await self.connect_to_screenshot_service():
                return "Screenshot service not available"

            # Send capture request
            request = {
                "action": "capture_screenshot",
                "requestId": str(uuid.uuid4()),
                "options": options or {}
            }

            await self.screenshot_ws.send(json.dumps(request))

            # Wait for response
            response_text = await self.screenshot_ws.recv()
            response = json.loads(response_text)

            if response.get('success'):
                base64_data = response.get('base64', '')
                if base64_data:
                    return f"Screenshot captured successfully. Base64 length: {len(base64_data)} characters"
                else:
                    return "Screenshot captured but no image data received"
            else:
                return f"Screenshot failed: {response.get('error', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return f"Screenshot capture failed: {str(e)}"

    async def analyze_screenshot(self, data_url: str = None, prompt: str = "What is in this image?") -> str:
        """Analyze a screenshot with AI"""
        try:
            if not data_url:
                # Capture a new screenshot first
                screenshot_result = await self.capture_screenshot()
                if "failed" in screenshot_result.lower():
                    return screenshot_result

            # For now, return a placeholder - this would normally call OpenAI Vision API
            return f"Screenshot analysis: {prompt} - Analysis functionality would be implemented here with OpenAI Vision API"

        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return f"Screenshot analysis failed: {str(e)}"

    async def get_reading_recommendations(self, text_content: str, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get reading recommendations from the A2C agent"""
        if not self.reading_agent or not READING_ENABLED:
            logger.warning("Reading agent not available")
            return None

        try:
            # Create query data with safe defaults
            query_data = QueryData(
                # Text Analysis
                text_difficulty=user_context.get('text_difficulty', 0.5),
                text_type=user_context.get('text_type', 0.5),
                text_length=min(1.0, len(text_content) / 1000.0),  # Normalize by 1000 chars

                # User Behavior
                user_engagement=user_context.get('user_engagement', 0.7),
                user_comprehension=user_context.get('user_comprehension', 0.7),
                recent_commands=user_context.get('recent_commands', []),
                text_progress=user_context.get('text_progress', 0.0),

                # Session Data
                current_reading_speed=user_context.get('current_reading_speed', 1.0),
                current_pause_frequency=user_context.get('current_pause_frequency', 0.3),
                current_highlight_intensity=user_context.get('current_highlight_intensity', 0.5),
                current_chunk_size=user_context.get('current_chunk_size', 0.5),

                # Optional
                session_duration=user_context.get('session_duration', 0.0),
                action_count=user_context.get('action_count', 0),
                preferred_speed=user_context.get('preferred_speed'),
                preferred_pauses=user_context.get('preferred_pauses'),
                preferred_highlighting=user_context.get('preferred_highlighting')
            )

            # Process query safely
            result = await self.reading_agent.process_query(query_data)
            logger.info(f"Reading recommendations generated: {result['recommendations']}")
            return result

        except Exception as e:
            logger.error(f"Failed to get reading recommendations: {e}")
            return None

    def analyze_text_difficulty(self, text_content: str) -> float:
        """Simple text difficulty analysis"""
        try:
            # Basic heuristics for text difficulty
            words = text_content.split()
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            sentence_count = text_content.count('.') + text_content.count('!') + text_content.count('?')
            avg_sentence_length = len(words) / sentence_count if sentence_count > 0 else len(words)

            # Normalize to 0-1 scale
            difficulty = min(1.0, (avg_word_length / 8.0 + avg_sentence_length / 20.0) / 2.0)
            return difficulty
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return 0.5  # Default difficulty

    def _get_instructions(self) -> str:
        """Get system instructions for the AI"""
        tools_list = "\n".join([f"- {tool.name}: {tool.description}"
                                for tool in self.mcp_router.list_tools()[:5]])

        reading_capabilities = ""
        if self.reading_agent and READING_ENABLED:
            reading_capabilities = """
- Provide intelligent reading assistance with adaptive speed, pausing, and highlighting
- Analyze text difficulty and recommend optimal reading settings
- Learn from user preferences to improve reading experience"""

        return f"""You are Clarity, a helpful and friendly AI assistant with access to tools.

Your personality:
- Be conversational and natural
- Be helpful and proactive
- Keep responses concise and clear
- Be empathetic and understanding

Your capabilities:
- Answer questions on any topic
- Help with analysis and problem-solving
- Provide creative assistance
- Engage in natural conversation
- Create and manage notes in the database
- Search for information you've stored
- Track tasks and conversations{reading_capabilities}

Available tools:
{tools_list}

When users ask you to remember something, create a note, or search for information,
use the appropriate tool to help them. Always confirm when you've successfully
completed an action.

When users need help with reading text, you can analyze the content and provide
personalized recommendations for reading speed, pause frequency, and highlighting.

Always maintain a warm, professional tone while being genuinely helpful."""

    async def cleanup(self):
        """Cleanup on disconnect"""
        logger.info("Cleaning up voice agent...")
        if self.session:
            try:
                await self.session.end()
                logger.info("✓ Session closed")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
        self.session = None

        # Close WebSocket connection
        if self.screenshot_ws and not self.screenshot_ws.closed:
            try:
                await self.screenshot_ws.close()
                logger.info("✓ Screenshot WebSocket closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.screenshot_ws = None

        logger.info("Cleanup complete")


async def request_all_jobs(req: JobRequest) -> bool:
    """Accept all jobs"""
    logger.info(f"Received job request for room: {req.room.name}")
    return True


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent"""
    logger.info("\n" + "="*50)
    logger.info("CLARITY AGENT ENTRYPOINT")
    logger.info("="*50)

    agent = ClarityVoiceAgent()

    try:
        logger.info("Starting ClarityVoiceAgent...")
        await agent.start(ctx)
        logger.info("✓ Agent started successfully")

        # Keep the agent running
        logger.info("Agent running - waiting for speech input...")
        logger.info(f"Room connection state: {ctx.room.connection_state}")
        iteration = 0
        while ctx.room:
            iteration += 1
            logger.info(f"Agent loop iteration {iteration}, room: {agent.room_name}, state: {ctx.room.connection_state}")

            # Check if this is our target room
            if agent.room_name and agent.room_name.startswith("clarity-"):
                logger.info(f"✓ Processing target room: {agent.room_name}")
                break
            else:
                logger.info(f"Waiting for target room, current room: {agent.room_name}")
                await asyncio.sleep(1)
                continue

            # Check if room is still connected
            if ctx.room.connection_state == "disconnected":
                logger.info("Room disconnected, breaking loop")
                break

        logger.info("Agent main loop ended")

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down agent...")
        await agent.cleanup()
        logger.info("Agent shutdown complete")


if __name__ == "__main__":
    logger.info("\n" + "#"*50)
    logger.info("# CLARITY VOICE AGENT STARTING")
    logger.info("#"*50)

    # Verify environment (same as Cassette)
    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_key = os.getenv("LIVEKIT_API_KEY")
    livekit_secret = os.getenv("LIVEKIT_API_SECRET")

    logger.info("Environment check:")
    logger.info(f"  LiveKit URL: {livekit_url or 'NOT SET'}")
    logger.info(f"  LiveKit API Key: {'SET' if livekit_key else 'NOT SET'}")
    logger.info(f"  LiveKit Secret: {'SET' if livekit_secret else 'NOT SET'}")

    if not all([livekit_url, livekit_key, livekit_secret]):
        logger.error("Missing LiveKit configuration! Check .env file")
        sys.exit(1)

    # Map ELEVENLABS_API_KEY to ELEVEN_API_KEY for ElevenLabs plugin compatibility (same as Cassette)
    if os.getenv("ELEVENLABS_API_KEY") and not os.getenv("ELEVEN_API_KEY"):
        os.environ["ELEVEN_API_KEY"] = os.getenv("ELEVENLABS_API_KEY")
        logger.info("Mapped ELEVENLABS_API_KEY to ELEVEN_API_KEY for ElevenLabs plugin")

    logger.info("Starting LiveKit worker...")

    # Run the agent worker with job request function to accept all jobs (like Cassette)
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_all_jobs,
        )
    )