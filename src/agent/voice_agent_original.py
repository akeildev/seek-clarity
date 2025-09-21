#!/usr/bin/env python3
"""
Clarity Voice Agent - LiveKit integration with OpenAI Realtime and ElevenLabs
"""

import asyncio
import logging
import os
import json
import uuid
import time
import aiohttp
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
    function_tool,
)
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, elevenlabs, silero
from openai.types.beta.realtime.session import InputAudioTranscription
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging (simplified like Cassette)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clarity-agent")


class ClarityVoiceAgent:
    """Voice agent for Clarity assistant"""

    def __init__(self):
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.room_name: Optional[str] = None
        self.participant_identity: Optional[str] = None
        self.screenshot_ws_url = "ws://127.0.0.1:8765"
        self.openai_client = AsyncOpenAI()
        self._screenshot_cache = None
        self._screenshot_cache_time = None

    async def start(self, ctx: JobContext):
        """Initialize and start the agent session - simplified like Cassette"""
        self.context = ctx
        logger.info(f"Starting agent with room: {ctx.room.name}")

        # Connect to room first (like Cassette)
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        # Create agent with instructions and tools (like Cassette)
        tools = [
            self.take_screenshot,
            self.test_screenshot_service,
            self.create_calendar_event,
            self.create_note,
        ]

        # Import Agent locally like Cassette
        from livekit.agents import Agent
        agent = Agent(
            instructions=self._get_instructions(),
            tools=tools
        )

        # Get ElevenLabs configuration (simplified like Cassette)
        eleven_api_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        eleven_voice_id = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

        if not eleven_api_key:
            logger.warning("ELEVEN_API_KEY/ELEVENLABS_API_KEY is not set; TTS will likely fail")
        else:
            logger.info(f"ElevenLabs API key detected")

        # Create agent session (simplified like Cassette)
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

        # Start the session (like Cassette)
        await self.session.start(agent=agent, room=ctx.room)
        logger.info("✓ Voice session started successfully")

        # Send greeting
        await self._send_greeting()

    async def _send_greeting(self):
        """Send initial greeting"""
        greeting = "Hello! I'm Clarity, your AI assistant. I can help you with questions, analysis, and I can see your screen when you ask. How can I help you today?"
        if self.session:
            logger.info("Sending greeting message...")
            try:
                await self.session.say(greeting)
                logger.info("✓ Greeting sent successfully")
            except Exception as e:
                logger.error(f"Failed to send greeting: {e}")


    @function_tool
    async def take_screenshot(
        self,
        context: RunContext,
        query: str = "What do you see on the screen?",
        region: str = "full"
    ) -> str:
        """
        Captures and analyzes a screenshot of the user's screen.

        Args:
            query: What to analyze or look for in the screenshot
            region: Screen region to capture ("full", "window", or "selection")

        Returns:
            Visual analysis of the screenshot
        """
        try:
            # Quick acknowledgment before taking screenshot
            if self.session and context:
                try:
                    await self.session.say("Give me a sec while I take a look.")
                    logger.info("Sent screenshot acknowledgment")
                except Exception as e:
                    logger.warning(f"Could not send acknowledgment: {e}")

            # Check cache (5 second validity) - same as cassette
            current_time = time.time()
            if (self._screenshot_cache and
                self._screenshot_cache_time and
                current_time - self._screenshot_cache_time < 5):
                logger.info("Using cached screenshot")
                screenshot_base64 = self._screenshot_cache
            else:
                # Request new screenshot from Electron via WebSocket
                logger.info(f"Requesting screenshot capture (region: {region})")
                screenshot_base64 = await self._request_screenshot(region)
                # Cache it
                self._screenshot_cache = screenshot_base64
                self._screenshot_cache_time = current_time

            # Analyze with GPT-4o vision
            logger.info(f"Analyzing screenshot with query: {query}")
            analysis = await self._analyze_with_vision(screenshot_base64, query)

            return analysis

        except Exception as e:
            logger.error(f"Screenshot tool error: {e}", exc_info=True)
            return f"I couldn't capture the screen right now. Error: {str(e)}"

    @function_tool
    async def test_screenshot_service(
        self,
        context: RunContext,
    ) -> str:
        """
        Tests if the screenshot service is working properly.

        Returns:
            Status of the screenshot service
        """
        try:
            logger.info("Testing screenshot service connection...")

            # Test WebSocket connection
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(self.screenshot_ws_url) as ws:
                    logger.info("WebSocket connection test successful")

                    # Send a simple ping
                    await ws.send_json({"action": "ping"})
                    response = await ws.receive_json()
                    logger.info(f"Ping response: {response}")

                    return "Screenshot service is working! WebSocket connection successful."

        except Exception as e:
            logger.error(f"Screenshot service test failed: {e}")
            return f"Screenshot service test failed: {str(e)}"

    @function_tool
    async def create_calendar_event(
        self,
        context: RunContext,
        title: str,
        description: str = "",
        calendar: str = "Work",
        start_time: str = "now",
        duration: int = 60
    ) -> str:
        """
        Creates a calendar event in the macOS Calendar app.

        Args:
            title: Event title
            description: Event description
            calendar: Calendar name (default: Work)
            start_time: When the event starts ("now", "tomorrow", or specific time)
            duration: Duration in minutes (default: 60)

        Returns:
            Success message or error
        """
        try:
            logger.info("="*60)
            logger.info("[Calendar] Creating calendar event")
            logger.info(f"  Title: {title}")
            logger.info(f"  Description: {description[:50]}..." if len(description) > 50 else f"  Description: {description}")
            logger.info(f"  Calendar: {calendar}")
            logger.info(f"  Start: {start_time}")
            logger.info(f"  Duration: {duration} minutes")
            logger.info("="*60)

            # Send request to Electron app via WebSocket
            request_data = {
                "action": "create_calendar_event",
                "params": {
                    "title": title,
                    "description": description,
                    "calendar": calendar,
                    "start_time": start_time,
                    "duration": duration
                }
            }

            # Send via WebSocket
            logger.info(f"[Calendar] Connecting to WebSocket at {self.screenshot_ws_url}")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.screenshot_ws_url) as ws:
                    logger.info("[Calendar] WebSocket connected")
                    logger.info(f"[Calendar] Sending request: {request_data}")
                    await ws.send_json(request_data)

                    logger.info("[Calendar] Waiting for response...")
                    response = await ws.receive_json()
                    logger.info(f"[Calendar] Received response: {response}")

                    if response.get("success"):
                        logger.info(f"✓ [Calendar] Event created successfully")
                        return f"Calendar event '{title}' has been created in your {calendar} calendar."
                    else:
                        error_msg = response.get('error', 'Unknown error')
                        logger.error(f"✗ [Calendar] Failed to create event: {error_msg}")
                        return f"I couldn't create the calendar event: {error_msg}"

        except aiohttp.ClientError as e:
            logger.error(f"[Calendar] WebSocket connection error: {e}")
            return f"I couldn't connect to create the calendar event. Please make sure the app is running."
        except Exception as e:
            logger.error(f"[Calendar] Unexpected error: {e}", exc_info=True)
            return f"I couldn't create the calendar event. Error: {str(e)}"

    @function_tool
    async def create_note(
        self,
        context: RunContext,
        content: str,
        title: str = None
    ) -> str:
        """
        Creates a note in the macOS Notes app.

        Args:
            content: The note content
            title: Optional note title (auto-generated if not provided)

        Returns:
            Success message or error
        """
        try:
            # Generate title if not provided
            if not title:
                from datetime import datetime
                title = f"Note - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            logger.info("="*60)
            logger.info("[Notes] Creating note")
            logger.info(f"  Title: {title}")
            logger.info(f"  Content: {content[:100]}..." if len(content) > 100 else f"  Content: {content}")
            logger.info("="*60)

            # Send request to Electron app via WebSocket
            request_data = {
                "action": "create_note",
                "params": {
                    "title": title,
                    "body": content
                }
            }

            # Send via WebSocket
            logger.info(f"[Notes] Connecting to WebSocket at {self.screenshot_ws_url}")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.screenshot_ws_url) as ws:
                    logger.info("[Notes] WebSocket connected")
                    logger.info(f"[Notes] Sending request: {request_data}")
                    await ws.send_json(request_data)

                    logger.info("[Notes] Waiting for response...")
                    response = await ws.receive_json()
                    logger.info(f"[Notes] Received response: {response}")

                    if response.get("success"):
                        logger.info(f"✓ [Notes] Note created successfully")
                        return f"I've created a note titled '{title}' in your Notes app."
                    else:
                        error_msg = response.get('error', 'Unknown error')
                        logger.error(f"✗ [Notes] Failed to create note: {error_msg}")
                        return f"I couldn't create the note: {error_msg}"

        except aiohttp.ClientError as e:
            logger.error(f"[Notes] WebSocket connection error: {e}")
            return f"I couldn't connect to create the note. Please make sure the app is running."
        except Exception as e:
            logger.error(f"[Notes] Unexpected error: {e}", exc_info=True)
            return f"I couldn't create the note. Error: {str(e)}"

    async def _request_screenshot(self, region: str) -> str:
        """Request screenshot from Electron app via WebSocket"""
        try:
            logger.info(f"Attempting to connect to screenshot service at {self.screenshot_ws_url}")
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(self.screenshot_ws_url) as ws:
                    logger.info("WebSocket connection established")

                    # Send screenshot request (cassette format)
                    request_data = {
                        "action": "capture_screenshot",
                        "region": region
                    }
                    logger.info(f"Sending screenshot request: {request_data}")
                    await ws.send_json(request_data)

                    # Wait for response
                    logger.info("Waiting for screenshot response...")
                    msg = await ws.receive_json()
                    logger.info(f"Received response: {type(msg)} with keys: {list(msg.keys()) if isinstance(msg, dict) else 'not a dict'}")

                    if msg.get("success"):
                        logger.info("Screenshot captured successfully")
                        base64_data = msg.get("base64")
                        if base64_data:
                            logger.info(f"Received base64 data, length: {len(base64_data)}")
                            return base64_data
                        else:
                            raise Exception("No base64 data in successful response")
                    else:
                        error_msg = msg.get("error", "Screenshot capture failed - no error message provided")
                        logger.error(f"Screenshot capture failed: {error_msg}")
                        raise Exception(error_msg)

        except aiohttp.ClientError as e:
            logger.error(f"WebSocket connection error: {e}")
            raise Exception(f"Could not connect to screenshot service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in screenshot request: {e}", exc_info=True)
            raise Exception(f"Screenshot request failed: {str(e)}")

    async def _analyze_with_vision(self, image_base64: str, query: str) -> str:
        """Analyze screenshot with GPT-4o vision API"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "auto"
                            }
                        }
                    ]
                }],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"GPT-4o vision analysis error: {e}")
            raise Exception(f"Could not analyze the screenshot: {str(e)}")


    def _get_instructions(self) -> str:
        """Get system instructions for the AI"""
        return f"""You are Clarity, a helpful and friendly AI assistant with screenshot capabilities.

CRITICAL RULE: You MUST ALWAYS respond in English only. Never speak Spanish or any other language. All responses must be in English.

Your personality:
- Be conversational and natural
- Be helpful and proactive
- Keep responses concise and clear
- Be empathetic and understanding
- ALWAYS speak in English only

Your capabilities:
- Answer questions on any topic
- Help with analysis and problem-solving
- Provide creative assistance
- Engage in natural conversation
- Capture screenshots of the user's screen
- Analyze screenshots and describe what you see
- Help with visual content on the screen
- Create calendar events in the macOS Calendar app
- Create notes in the macOS Notes app
- Schedule meetings and reminders
- Take meeting notes and summaries

SCREENSHOT USAGE - BE PROACTIVE:
===============================
You can see the user's screen and should use the take_screenshot tool when:
- They ask "what's on my screen" or "can you see this"
- They need help with something visible on their screen
- They want you to read or analyze visual content
- They ask about errors, UI elements, or applications they're using
- They mention specific content they're looking at
- They ask for help with anything that would benefit from seeing their screen
- When you think seeing their screen would help answer their question better

Screenshot commands you understand:
- "Take a screenshot" - Captures the current screen
- "What's on my screen?" - Captures and analyzes the screen
- "Analyze what I'm looking at" - Takes a screenshot and describes it
- "Describe the screen" - Captures and analyzes visual content
- "Can you see this?" - Takes a screenshot and analyzes it
- "Help me with this" - Often benefits from a screenshot
- "What should I do here?" - Take a screenshot to see what they're referring to
- "Test screenshot" - Tests if the screenshot service is working

CALENDAR & NOTES COMMANDS:
===========================
You can help with scheduling and note-taking:
- "Schedule a meeting" - Creates a calendar event
- "Add to my calendar" - Creates an event with specified details
- "Take a note" - Creates a new note
- "Remember this" - Saves information as a note
- "Schedule for tomorrow" - Creates event for next day
- "Meeting notes" - Creates formatted meeting notes

IMPORTANT: Be proactive about using screenshots. If the user's question would benefit
from seeing their screen, just take a screenshot and analyze it. Don't ask permission.

IMPORTANT: Always respond in English only. Never use Spanish or any other language.
Always maintain a warm, professional tone while being genuinely helpful."""

    async def cleanup(self):
        """Cleanup on disconnect"""
        logger.info("Cleaning up voice agent...")

        # Close session
        if self.session:
            try:
                await self.session.end()
                logger.info("✓ Session closed")
            except Exception as e:
                logger.error(f"Error closing session: {e}")

        self.session = None
        logger.info("Cleanup complete")



async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent worker"""
    logger.info(f"[ENTRYPOINT] Starting for room: {ctx.room.name}")

    # Create and start agent
    agent = ClarityVoiceAgent()

    try:
        await agent.start(ctx)
        logger.info("Agent session started successfully")

        # Keep the agent running (simplified like Cassette)
        await asyncio.sleep(float("inf"))

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
    finally:
        await agent.cleanup()
        logger.info("Agent stopped")


if __name__ == "__main__":
    logger.info("Starting Clarity voice agent...")

    # Map ELEVENLABS_API_KEY to ELEVEN_API_KEY for ElevenLabs plugin compatibility
    if os.getenv("ELEVENLABS_API_KEY") and not os.getenv("ELEVEN_API_KEY"):
        os.environ["ELEVEN_API_KEY"] = os.getenv("ELEVENLABS_API_KEY")
        logger.info("Mapped ELEVENLABS_API_KEY to ELEVEN_API_KEY")

    # Run the agent worker (simplified like Cassette)
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )