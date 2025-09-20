# Voice Agent - Main interface for reading assistance
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional
from reading_a2c import ReadingA2C
from mcp_utils import ReadingStateCollector, MCPSettingsManager

class VoiceAgent:
    """Main voice agent that coordinates reading assistance using A2C"""
    
    def __init__(self, device="cpu"):
        self.device = device
        
        # Initialize A2C agent
        self.a2c_agent = ReadingA2C(
            state_size=20,
            action_size=8,
            device=device,
            voice_agent=self
        )
        
        # Initialize MCP tools
        self.state_collector = ReadingStateCollector(self)
        self.settings_manager = MCPSettingsManager(self)
        
        # Current reading parameters (these can be changed by A2C)
        self.current_reading_speed = 1.0
        self.current_pause_frequency = 0.3
        self.current_highlight_intensity = 0.5
        self.current_chunk_size = 0.5
        
        # Session tracking
        self.command_history = []
        self.text_progress = 0.0
        self.session_duration = 0.0
        self.current_text = ""
        
        # ElevenLabs integration (independent of A2C)
        self.elevenlabs_settings = {
            'voice_id': 'default',
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.5
            }
        }
    
    async def process_text(self, text_content: str, user_commands: List[str] = None):
        """Main method to process text and get recommendations"""
        if user_commands is None:
            user_commands = []
        
        # Update command history
        self.command_history.extend(user_commands)
        self.current_text = text_content
        
        # Collect state using MCP tools
        state_dict = await self.state_collector.collect_reading_state(text_content, user_commands)
        
        # Get A2C recommendations
        recommended_settings = self.a2c_agent.get_recommended_settings(text_content, user_commands)
        
        # Apply recommendations
        self._apply_settings(recommended_settings)
        
        # Return both A2C settings and ElevenLabs settings
        return {
            'a2c_settings': recommended_settings,
            'elevenlabs_settings': self.elevenlabs_settings,
            'state_info': state_dict
        }
    
    def _apply_settings(self, settings: Dict[str, float]):
        """Apply settings to voice agent"""
        if 'reading_speed' in settings:
            self.current_reading_speed = settings['reading_speed']
        
        if 'pause_frequency' in settings:
            self.current_pause_frequency = settings['pause_frequency']
        
        if 'highlight_intensity' in settings:
            self.current_highlight_intensity = settings['highlight_intensity']
        
        if 'chunk_size' in settings:
            self.current_chunk_size = settings['chunk_size']
    
    async def update_from_mcp_feedback(self, feedback_data: Dict[str, Any]):
        """Update settings based on MCP tool feedback"""
        await self.settings_manager.apply_settings_from_feedback(feedback_data)
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings for both A2C and ElevenLabs"""
        return {
            'a2c_settings': {
                'reading_speed': self.current_reading_speed,
                'pause_frequency': self.current_pause_frequency,
                'highlight_intensity': self.current_highlight_intensity,
                'chunk_size': self.current_chunk_size
            },
            'elevenlabs_settings': self.elevenlabs_settings,
            'session_info': {
                'command_count': len(self.command_history),
                'text_progress': self.text_progress,
                'session_duration': self.session_duration
            }
        }
    
    def update_elevenlabs_settings(self, new_settings: Dict[str, Any]):
        """Update ElevenLabs settings independently of A2C"""
        self.elevenlabs_settings.update(new_settings)
    
    def update_text_progress(self, progress: float):
        """Update text reading progress"""
        self.text_progress = max(0.0, min(1.0, progress))
    
    def update_session_duration(self, duration: float):
        """Update session duration in seconds"""
        self.session_duration = duration
    
    async def train_agent(self, training_data: List[Dict[str, Any]]):
        """Train the A2C agent with collected data"""
        # This would implement training with collected user data
        # For now, just a placeholder
        pass
    
    def reset_session(self):
        """Reset session data"""
        self.command_history = []
        self.text_progress = 0.0
        self.session_duration = 0.0
        self.current_text = ""
        
        # Reset to default settings
        self.current_reading_speed = 1.0
        self.current_pause_frequency = 0.3
        self.current_highlight_intensity = 0.5
        self.current_chunk_size = 0.5

# Example usage function
async def main():
    """Example of how to use the voice agent"""
    agent = VoiceAgent()
    
    # Process some text
    text = "This is a sample text for reading assistance. The agent will analyze it and provide recommendations."
    commands = ["read this", "go faster"]
    
    result = await agent.process_text(text, commands)
    print("A2C Settings:", result['a2c_settings'])
    print("ElevenLabs Settings:", result['elevenlabs_settings'])
    print("State Info:", result['state_info'])

if __name__ == "__main__":
    asyncio.run(main())
