# MCP Tools Integration for Reading Agent
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional
import json

class ReadingStateCollector:
    def __init__(self, voice_agent=None):
        self.voice_agent = voice_agent
        self.current_state = None
        self.state_history = []
        
    async def collect_reading_state(self, text_content: str, user_commands: Optional[List[str]] = None) -> Dict[str, float]:
        """Collect all 12 state dimensions for A2C"""
        state = {}
        
        # Text characteristics (LLM-based)
        state['text_difficulty'] = await self._assess_text_difficulty(text_content)
        state['text_length'] = self._normalize_text_length(text_content)
        state['text_type'] = await self._classify_text_type(text_content)
        
        # Current reading parameters (from voice agent)
        if self.voice_agent:
            state['reading_speed'] = self.voice_agent.current_reading_speed
            state['pause_frequency'] = self.voice_agent.current_pause_frequency
            state['highlight_intensity'] = self.voice_agent.current_highlight_intensity
            state['chunk_size'] = self.voice_agent.current_chunk_size
        else:
            # Default values if no voice agent
            state['reading_speed'] = 1.0
            state['pause_frequency'] = 0.3
            state['highlight_intensity'] = 0.5
            state['chunk_size'] = 0.5
        
        # User behavior (from voice commands and behavior)
        state['user_engagement'] = await self._assess_engagement(user_commands)
        state['user_comprehension'] = await self._assess_comprehension(user_commands)
        state['session_progress'] = self._calculate_session_progress()
        state['action_count'] = len(self.voice_agent.command_history) if self.voice_agent else 0
        state['recent_commands'] = self._encode_recent_commands(user_commands)
        
        self.current_state = state
        self.state_history.append(state.copy())
        return state
    
    async def _assess_text_difficulty(self, text_content: str) -> float:
        """Assess text difficulty using MCP tools"""
        # This would call your MCP tool for text analysis
        # For now, use simple heuristics
        word_count = len(text_content.split())
        avg_word_length = np.mean([len(word) for word in text_content.split()])
        sentence_count = text_content.count('.') + text_content.count('!') + text_content.count('?')
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Normalize to 0-1 scale
        difficulty = min(1.0, (avg_word_length / 10.0 + avg_sentence_length / 20.0) / 2.0)
        return difficulty
    
    def _normalize_text_length(self, text_content: str) -> float:
        """Normalize text length to 0-1 scale"""
        word_count = len(text_content.split())
        # Normalize based on typical reading session lengths
        return min(1.0, word_count / 1000.0)
    
    async def _classify_text_type(self, text_content: str) -> float:
        """Classify text type using MCP tools"""
        # This would call your MCP tool for text classification
        # For now, use simple heuristics
        text_lower = text_content.lower()
        
        # Email indicators
        if '@' in text_content or 'dear' in text_lower or 'sincerely' in text_lower:
            return 0.1  # Email
        
        # Academic/textbook indicators
        if any(word in text_lower for word in ['chapter', 'section', 'figure', 'table', 'reference']):
            return 0.8  # Academic
        
        # News/article indicators
        if any(word in text_lower for word in ['breaking', 'reported', 'according to', 'sources']):
            return 0.6  # News
        
        # Default to general text
        return 0.4
    
    async def _assess_engagement(self, user_commands: Optional[List[str]]) -> float:
        """Assess user engagement from commands"""
        if not user_commands:
            return 0.5  # Neutral engagement
        
        # Positive engagement indicators
        positive_commands = ['continue', 'faster', 'slower', 'repeat', 'explain', 'more']
        negative_commands = ['stop', 'pause', 'skip', 'enough', 'quit']
        
        positive_count = sum(1 for cmd in user_commands if any(pos in cmd.lower() for pos in positive_commands))
        negative_count = sum(1 for cmd in user_commands if any(neg in cmd.lower() for neg in negative_commands))
        
        if positive_count + negative_count == 0:
            return 0.5
        
        return positive_count / (positive_count + negative_count)
    
    async def _assess_comprehension(self, user_commands: Optional[List[str]]) -> float:
        """Assess user comprehension from commands"""
        if not user_commands:
            return 0.5  # Neutral comprehension
        
        # Comprehension indicators
        comprehension_commands = ['explain', 'what', 'why', 'how', 'repeat', 'clarify', 'confused']
        confidence_commands = ['got it', 'understand', 'clear', 'makes sense', 'continue']
        
        confusion_count = sum(1 for cmd in user_commands if any(comp in cmd.lower() for comp in comprehension_commands))
        confidence_count = sum(1 for cmd in user_commands if any(conf in cmd.lower() for conf in confidence_commands))
        
        if confusion_count + confidence_count == 0:
            return 0.5
        
        return confidence_count / (confusion_count + confidence_count)
    
    def _calculate_session_progress(self) -> float:
        """Calculate session progress"""
        if not self.voice_agent:
            return 0.0
        
        # Calculate based on text progress or time
        if hasattr(self.voice_agent, 'text_progress'):
            return self.voice_agent.text_progress
        elif hasattr(self.voice_agent, 'session_duration'):
            return min(1.0, self.voice_agent.session_duration / 3600.0)  # 1 hour max
        else:
            return 0.0
    
    def _encode_recent_commands(self, user_commands: Optional[List[str]]) -> float:
        """Encode recent commands as a single value"""
        if not user_commands:
            return 0.0
        
        # Simple encoding: number of recent commands normalized
        return min(1.0, len(user_commands) / 10.0)
    
    def get_state_vector(self) -> np.ndarray:
        """Get current state as numpy array for A2C"""
        if not self.current_state:
            return np.zeros(12)
        
        return np.array([
            self.current_state['text_difficulty'],
            self.current_state['text_length'],
            self.current_state['text_type'],
            self.current_state['reading_speed'],
            self.current_state['pause_frequency'],
            self.current_state['highlight_intensity'],
            self.current_state['chunk_size'],
            self.current_state['user_engagement'],
            self.current_state['user_comprehension'],
            self.current_state['session_progress'],
            self.current_state['action_count'],
            self.current_state['recent_commands']
        ])

class MCPSettingsManager:
    """Manages settings changes from MCP tools feedback loop"""
    
    def __init__(self, voice_agent):
        self.voice_agent = voice_agent
        self.settings_history = []
        
    async def apply_settings_from_feedback(self, feedback_data: Dict[str, Any]):
        """Apply settings changes based on MCP tool feedback"""
        if not self.voice_agent:
            return
        
        # Extract settings from feedback
        settings = self._parse_feedback_settings(feedback_data)
        
        # Apply settings to voice agent
        if 'reading_speed' in settings:
            self.voice_agent.current_reading_speed = settings['reading_speed']
        
        if 'pause_frequency' in settings:
            self.voice_agent.current_pause_frequency = settings['pause_frequency']
        
        if 'highlight_intensity' in settings:
            self.voice_agent.current_highlight_intensity = settings['highlight_intensity']
        
        if 'chunk_size' in settings:
            self.voice_agent.current_chunk_size = settings['chunk_size']
        
        # Log the change
        self.settings_history.append({
            'timestamp': asyncio.get_event_loop().time(),
            'settings': settings,
            'source': 'mcp_feedback'
        })
    
    def _parse_feedback_settings(self, feedback_data: Dict[str, Any]) -> Dict[str, float]:
        """Parse settings from MCP tool feedback"""
        settings = {}
        
        # This would parse the actual feedback from your MCP tools
        # For now, return empty dict
        return settings
    
    def get_current_settings(self) -> Dict[str, float]:
        """Get current voice agent settings"""
        if not self.voice_agent:
            return {}
        
        return {
            'reading_speed': self.voice_agent.current_reading_speed,
            'pause_frequency': self.voice_agent.current_pause_frequency,
            'highlight_intensity': self.voice_agent.current_highlight_intensity,
            'chunk_size': self.voice_agent.current_chunk_size
        }
