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

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    RunContext,
)
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, elevenlabs, silero
from openai.types.beta.realtime.session import InputAudioTranscription
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clarity-agent")


class ClarityVoiceAgent:
    """Voice agent for Clarity assistant"""

    def __init__(self):
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.room_name: Optional[str] = None
        self.participant_identity: Optional[str] = None

    async def start(self, ctx: JobContext):
        """Initialize and start the agent session"""
        logger.info("Starting Clarity voice agent")
        self.context = ctx

        # Extract room and participant info
        self.room_name = ctx.room.name
        participants = list(ctx.room.remote_participants.values())
        if participants:
            self.participant_identity = participants[0].identity
            logger.info(f"Participant joined: {self.participant_identity}")

        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info(f"Connected to room: {self.room_name}")

        # Get API keys from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        eleven_api_key = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        eleven_voice_id = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

        if not openai_api_key:
            logger.error("OPENAI_API_KEY not set")
            return

        if not eleven_api_key:
            logger.warning("ElevenLabs API key not set - TTS may fail")

        # Create voice session with OpenAI Realtime
        logger.info("Creating voice session with OpenAI Realtime")
        self.session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                model="gpt-4o-realtime-preview",
                modalities=["text", "audio"],
                input_audio_transcription=InputAudioTranscription(
                    model="whisper-1",
                    language="en",
                ),
                instructions=self._get_instructions(),
                temperature=0.7,
                max_response_output_tokens=4096,
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

        # Start the session
        await self.session.start(room=ctx.room)
        logger.info("Voice session started successfully")

        # Send greeting
        await self._send_greeting()

    async def _send_greeting(self):
        """Send initial greeting"""
        greeting = "Hello! I'm Clarity, your AI assistant. How can I help you today?"
        if self.session:
            await self.session.say(greeting)
            logger.info("Greeting sent")

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
        logger.info("Cleaning up voice agent")
        if self.session:
            await self.session.close()
        self.session = None


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent"""
    agent = ClarityVoiceAgent()

    try:
        await agent.start(ctx)

        # Keep the agent running
        while ctx.room:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    # Run the agent worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )