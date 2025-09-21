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
            self.applescript_execute,  # Single tool for all macOS automation like Cassette
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
    async def applescript_execute(
        self,
        context: RunContext,
        code_snippet: str
    ) -> str:
        """
        Execute AppleScript code for macOS automation (calendar, notes, reminders, etc.)

        Args:
            code_snippet: The AppleScript code to execute

        Returns:
            Success message or error
        """
        try:
            logger.info("="*60)
            logger.info("[AppleScript] Executing AppleScript")
            logger.info(f"  Code length: {len(code_snippet)} characters")
            logger.info(f"  Code preview: {code_snippet[:200]}..." if len(code_snippet) > 200 else f"  Code: {code_snippet}")
            logger.info("="*60)

            # Send request to Electron app via WebSocket
            request_data = {
                "action": "applescript_execute",
                "params": {
                    "code_snippet": code_snippet
                }
            }

            # Send via WebSocket
            logger.info(f"[AppleScript] Connecting to WebSocket at {self.screenshot_ws_url}")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.screenshot_ws_url) as ws:
                    logger.info("[AppleScript] WebSocket connected")
                    logger.info(f"[AppleScript] Sending request")
                    await ws.send_json(request_data)

                    logger.info("[AppleScript] Waiting for response...")
                    response = await ws.receive_json()
                    logger.info(f"[AppleScript] Received response: {response}")

                    if response.get("success"):
                        result = response.get("output", "")
                        logger.info(f"[AppleScript] ✓ Executed successfully: {result}")

                        # Check what was executed to provide context
                        if "Calendar" in code_snippet and "make new event" in code_snippet:
                            return "Successfully created the calendar event."
                        elif "Notes" in code_snippet and "make new note" in code_snippet:
                            return "Successfully created the note."
                        elif "Reminders" in code_snippet and "make new reminder" in code_snippet:
                            return "Successfully added the reminder."
                        elif "display notification" in code_snippet:
                            return "Successfully displayed the notification."
                        elif "do shell script" in code_snippet:
                            return f"Command executed. Result: {result}" if result else "Command executed successfully."
                        else:
                            return f"AppleScript executed successfully. {result}" if result else "AppleScript executed successfully."
                    else:
                        error = response.get("error", "Unknown error")
                        logger.error(f"[AppleScript] ✗ Failed: {error}")
                        return f"AppleScript execution failed: {error}"

        except Exception as e:
            logger.error(f"[AppleScript] Exception: {str(e)}", exc_info=True)
            return f"Error executing AppleScript: {str(e)}"

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
        return f"""You are Clarity, a helpful AI assistant integrated with the user's macOS desktop.

CRITICAL INSTRUCTION FOR ALL MACOS OPERATIONS:
================================================
You have ONLY ONE TOOL for macOS operations: applescript_execute

NEVER mention tool names to the user. ALWAYS use natural language.

Examples of AppleScript operations:

1. CALENDAR (Use proper date/time formats):
- Create event for today at specific time:
  set eventDate to current date
  set hours of eventDate to 15
  set minutes of eventDate to 0
  tell application "Calendar" to make new event at calendar 1 with properties {{summary:"Meeting", start date:eventDate, end date:eventDate + (60 * minutes)}}

- Create event for tomorrow:
  set eventDate to (current date) + (1 * days)
  set hours of eventDate to 14
  set minutes of eventDate to 30
  tell application "Calendar" to make new event at calendar 1 with properties {{summary:"Tomorrow Meeting", start date:eventDate, end date:eventDate + (90 * minutes)}}

2. NOTES:
- Create note:
  tell application "Notes" to make new note with properties {{name:"Meeting Notes", body:"Discussion points:\\n1. Project status\\n2. Next steps"}}

3. REMINDERS:
- Create reminder:
  set reminderDate to (current date) + (2 * hours)
  tell application "Reminders" to make new reminder with properties {{name:"Call client", remind me date:reminderDate}}

4. NOTIFICATIONS:
- Show notification:
  display notification "Task completed" with title "Clarity"

5. SYSTEM INFO:
- Battery: do shell script "pmset -g batt | grep -o '[0-9]*%'"
- Date/Time: do shell script "date"

SCREENSHOT CAPABILITIES:
========================
You can capture and analyze screenshots when users need help with:
- Visual content on their screen
- UI elements or applications
- Errors or issues they're seeing
- Any visual context that would help answer their question

Be proactive - if seeing their screen would help, just take a screenshot.

EXECUTION FLOW:
==============
1. When user asks to add something to calendar/notes/reminders, acknowledge and execute immediately
2. Construct the appropriate AppleScript code
3. Execute it using applescript_execute
4. Confirm success in natural language
5. If there's an error, explain what went wrong

TIMEZONE AWARENESS:
==================
- Always use proper AppleScript date objects
- For "5pm today", calculate from current date/time
- For "tomorrow at 3pm", add days then set specific hours

IMPORTANT: Always respond in English only. Never use Spanish or any other language.
Always describe actions in natural language without mentioning tool names."""

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