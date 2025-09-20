#!/usr/bin/env python3
"""
Clarity Voice Agent - LiveKit integration with OpenAI Realtime and ElevenLabs
"""

import asyncio
import logging
import os
import json
import uuid
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


class ClarityVoiceAgent:
    """Voice agent for Clarity assistant"""

    def __init__(self):
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.room_name: Optional[str] = None
        self.participant_identity: Optional[str] = None

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
        greeting = "Hello! I'm Clarity, your AI assistant. How can I help you today?"
        if self.session:
            logger.info("Sending greeting message...")
            try:
                await self.session.say(greeting)
                logger.info("✓ Greeting sent successfully")
            except Exception as e:
                logger.error(f"Failed to send greeting: {e}")

    def _get_instructions(self) -> str:
        """Get system instructions for the AI"""
        return """You are Clarity, a helpful and friendly AI assistant.

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
        logger.info("Cleanup complete")


def request_all_jobs(req: JobRequest) -> bool:
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
            logger.info(f"Agent loop iteration {iteration}, room: {self.room_name}, state: {ctx.room.connection_state}")

            # Check if this is our target room
            if self.room_name.startswith("clarity-"):
                logger.info(f"✓ Processing target room: {self.room_name}")
                break
            else:
                logger.info(f"Waiting for target room, current room: {self.room_name}")
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