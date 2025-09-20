# Create: src/agent/reading_environment.py
import asyncio
import numpy as np
import torch
from typing import List, Dict, Any
from mcp_utils import ReadingStateCollector

class ReadingEnvironment:
    def __init__(self, state_size=20, action_size=8, voice_agent=None):
        self.state_size = state_size
        self.action_size = action_size
        self.voice_agent = voice_agent
        
        # Initialize state collector
        self.state_collector = ReadingStateCollector(voice_agent)
        
        # Reading state components
        self.current_text_difficulty = 0.5
        self.current_reading_speed = 1.0
        self.user_comprehension = 0.5
        self.user_engagement = 0.5
        self.pause_frequency = 0.3
        self.highlight_intensity = 0.5
        
        # User behavior tracking
        self.reading_sessions = []
        self.user_feedback_history = []
        self.current_text = ""
        
    def reset(self):
        """Reset environment to initial state"""
        # Initialize with default reading state
        state = self._get_state_vector()
        return state, {}
    
    def step(self, action):
        """Execute action and return new state, reward, done, info"""
        # Convert action to reading parameters
        self._apply_action(action)
        
        # Simulate user behavior (in real app, this comes from actual user)
        reward = self._calculate_reward()
        
        # Check if reading session is complete
        done = self._is_session_complete()
        
        # Get new state
        next_state = self._get_state_vector()
        
        return next_state, reward, done, False, {}
    
    def _get_state_vector(self):
        """Convert current state to vector for neural network"""
        # Use state collector if available
        if self.state_collector and self.current_text:
            return self.state_collector.get_state_vector()
        
        # Fallback to basic state
        return np.array([
            self.current_text_difficulty,
            self.current_reading_speed,
            self.user_comprehension,
            self.user_engagement,
            self.pause_frequency,
            self.highlight_intensity,
            # Add more state components as needed
            len(self.reading_sessions),
            np.mean(self.user_feedback_history) if self.user_feedback_history else 0.5,
            # ... more state features
        ] + [0.0] * (self.state_size - 9))  # Pad to state_size
    
    def _apply_action(self, action):
        """Apply action to reading parameters"""
        # Action is a vector of 8 values (action_size=8)
        # Map to reading parameters
        
        # Reading speed adjustment
        self.current_reading_speed = max(0.5, min(1.5, 1.0 + action[0] * 0.5))
        
        # Pause frequency adjustment
        self.pause_frequency = max(0.1, min(0.8, 0.3 + action[1] * 0.5))
        
        # Highlight intensity adjustment
        self.highlight_intensity = max(0.0, min(1.0, 0.5 + action[2] * 0.5))
        
        # Add more action mappings as needed
    
    def _calculate_reward(self):

        """Calculate reward based on user behavior

        THIS IS GOING TO NEED A LOT OF WORK
        
        """
        # This is where you'd integrate with real user feedback
        # For now, simulate based on reading parameters
        
        reward = 0.0
        
        # Reward for optimal reading speed
        if 0.8 <= self.current_reading_speed <= 1.2:
            reward += 0.5
        
        # Reward for good pause frequency
        if 0.2 <= self.pause_frequency <= 0.6:
            reward += 0.3
        
        # Reward for user engagement
        if self.user_engagement > 0.7:
            reward += 0.8
        
        # Penalty for poor comprehension
        if self.user_comprehension < 0.3:
            reward -= 0.5
        
        return reward
    
    def _is_session_complete(self):
        """Check if reading session is complete"""
        # Complete after some number of steps or user stops
        return len(self.reading_sessions) > 50
    
    def update_user_feedback(self, feedback: Dict[str, Any]):
        """Update environment with real user feedback"""
        self.user_feedback_history.append(feedback)
        
        # Update user state based on feedback
        if 'comprehension' in feedback:
            self.user_comprehension = feedback['comprehension']
        if 'engagement' in feedback:
            self.user_engagement = feedback['engagement']
    
    def set_text_content(self, text_content: str):
        """Set text content for state collection"""
        self.current_text = text_content
        if self.state_collector:
            # Update state collector with new text
            asyncio.create_task(self.state_collector.collect_reading_state(text_content))
    
    async def collect_state_async(self, text_content: str, user_commands: List[str] = None):
        """Asynchronously collect state using MCP tools"""
        if self.state_collector:
            return await self.state_collector.collect_reading_state(text_content, user_commands)
        return {}