# Clean Reading Agent Interface
import asyncio
import numpy as np
import torch
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from reading_environment import ReadingEnvironment
from reading_a2c import ReadingA2C

@dataclass
class QueryData:
    """Required data structure for each query"""
    # Text Analysis (REQUIRED)
    text_difficulty: float  # 0.0-1.0, difficulty of the text
    text_type: float        # 0.0-1.0, type of text (email=0.1, academic=0.8, etc.)
    text_length: float      # 0.0-1.0, normalized text length
    
    # User Behavior (REQUIRED)
    user_engagement: float  # 0.0-1.0, how engaged the user is
    user_comprehension: float  # 0.0-1.0, how well user understands
    recent_commands: List[str]  # Recent user voice commands
    text_progress: float    # 0.0-1.0, progress through text
    
    # Session Data (REQUIRED)
    current_reading_speed: float      # 0.5-1.5, current speed setting
    current_pause_frequency: float    # 0.1-0.8, current pause frequency
    current_highlight_intensity: float  # 0.0-1.0, current highlight intensity
    current_chunk_size: float        # 0.1-1.0, current chunk size
    
    # Optional Data
    session_duration: float = 0.0     # Session duration in seconds
    action_count: int = 0             # Number of user actions
    preferred_speed: Optional[float] = None      # User's preferred speed
    preferred_pauses: Optional[float] = None     # User's preferred pauses
    preferred_highlighting: Optional[float] = None  # User's preferred highlighting

class ReadingAgent:
    """Clean interface for reading assistance with A2C agent"""
    
    def __init__(self, device="cpu"):
        self.device = device
        
        # Initialize A2C agent
        self.a2c_agent = ReadingA2C(
            state_size=20,
            action_size=8,
            device=device,
            voice_agent=self
        )
        
        # Initialize environment
        self.environment = ReadingEnvironment(
            state_size=20,
            action_size=8,
            voice_agent=self
        )
        
        # Current settings
        self.current_reading_speed = 1.0
        self.current_pause_frequency = 0.3
        self.current_highlight_intensity = 0.5
        self.current_chunk_size = 0.5
        
        # Session tracking
        self.command_history = []
        self.text_progress = 0.0
        self.session_duration = 0.0
        
    async def process_query(self, query_data: QueryData) -> Dict[str, Any]:
        """
        Process a reading query and return recommendations
        
        Args:
            query_data: QueryData object with all required information
            
        Returns:
            Dictionary with recommendations and analysis
        """
        # Validate input data
        self._validate_query_data(query_data)
        
        # Update internal state
        self._update_state_from_query(query_data)
        
        # Collect state for A2C
        state_dict = await self._collect_state(query_data)
        
        # Get A2C recommendations
        recommendations = self._get_recommendations(state_dict)
        
        # Calculate reward for learning
        reward = self._calculate_reward(query_data)
        
        # Return comprehensive response
        return {
            'recommendations': recommendations,
            'state_analysis': state_dict,
            'reward_breakdown': self.environment.get_reward_breakdown(),
            'current_settings': self._get_current_settings(),
            'learning_data': {
                'reward': reward,
                'state_vector': self.environment._get_state_vector(),
                'action_taken': recommendations
            }
        }
    
    def _validate_query_data(self, data: QueryData):
        """Validate that all required data is present and in correct ranges"""
        # Validate text analysis
        assert 0.0 <= data.text_difficulty <= 1.0, "text_difficulty must be 0.0-1.0"
        assert 0.0 <= data.text_type <= 1.0, "text_type must be 0.0-1.0"
        assert 0.0 <= data.text_length <= 1.0, "text_length must be 0.0-1.0"
        
        # Validate user behavior
        assert 0.0 <= data.user_engagement <= 1.0, "user_engagement must be 0.0-1.0"
        assert 0.0 <= data.user_comprehension <= 1.0, "user_comprehension must be 0.0-1.0"
        assert 0.0 <= data.text_progress <= 1.0, "text_progress must be 0.0-1.0"
        
        # Validate session data
        assert 0.5 <= data.current_reading_speed <= 1.5, "reading_speed must be 0.5-1.5"
        assert 0.1 <= data.current_pause_frequency <= 0.8, "pause_frequency must be 0.1-0.8"
        assert 0.0 <= data.current_highlight_intensity <= 1.0, "highlight_intensity must be 0.0-1.0"
        assert 0.1 <= data.current_chunk_size <= 1.0, "chunk_size must be 0.1-1.0"
    
    def _update_state_from_query(self, data: QueryData):
        """Update internal state from query data"""
        # Update current settings
        self.current_reading_speed = data.current_reading_speed
        self.current_pause_frequency = data.current_pause_frequency
        self.current_highlight_intensity = data.current_highlight_intensity
        self.current_chunk_size = data.current_chunk_size
        
        # Update session tracking
        self.command_history.extend(data.recent_commands)
        self.text_progress = data.text_progress
        self.session_duration = data.session_duration
        
        # Update environment
        self.environment.current_text_difficulty = data.text_difficulty
        self.environment.user_engagement = data.user_engagement
        self.environment.user_comprehension = data.user_comprehension
        self.environment.text_progress = data.text_progress
        
        # Update user feedback if preferences provided
        if data.preferred_speed is not None:
            self.environment.update_user_feedback({
                'preferred_speed': data.preferred_speed,
                'preferred_pauses': data.preferred_pauses,
                'preferred_highlighting': data.preferred_highlighting
            })
    
    async def _collect_state(self, data: QueryData) -> Dict[str, float]:
        """Collect state information for A2C agent"""
        return {
            'text_difficulty': data.text_difficulty,
            'text_length': data.text_length,
            'text_type': data.text_type,
            'reading_speed': data.current_reading_speed,
            'pause_frequency': data.current_pause_frequency,
            'highlight_intensity': data.current_highlight_intensity,
            'chunk_size': data.current_chunk_size,
            'user_engagement': data.user_engagement,
            'user_comprehension': data.user_comprehension,
            'session_progress': data.text_progress,
            'action_count': data.action_count,
            'recent_commands': min(1.0, len(data.recent_commands) / 10.0)
        }
    
    def _get_recommendations(self, state_dict: Dict[str, float]) -> Dict[str, float]:
        """Get recommendations from A2C agent"""
        # Convert state to vector
        state_vector = np.array([
            state_dict['text_difficulty'],
            state_dict['text_length'],
            state_dict['text_type'],
            state_dict['reading_speed'],
            state_dict['pause_frequency'],
            state_dict['highlight_intensity'],
            state_dict['chunk_size'],
            state_dict['user_engagement'],
            state_dict['user_comprehension'],
            state_dict['session_progress'],
            state_dict['action_count'],
            state_dict['recent_commands']
        ])
        
        # Pad to expected state size
        if len(state_vector) < 20:
            padding = np.zeros(20 - len(state_vector))
            state_vector = np.concatenate([state_vector, padding])
        
        # Get action from A2C agent
        state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            action, _ = self.a2c_agent.get_action(state_tensor, stochastic=False)
        
        # Convert action to recommendations
        action_np = action.squeeze(0).numpy()
        
        return {
            'recommended_reading_speed': max(0.5, min(1.5, 1.0 + action_np[0] * 0.5)),
            'recommended_pause_frequency': max(0.1, min(0.8, 0.3 + action_np[1] * 0.5)),
            'recommended_highlight_intensity': max(0.0, min(1.0, 0.5 + action_np[2] * 0.5)),
            'recommended_chunk_size': max(0.1, min(1.0, 0.5 + action_np[3] * 0.5)),
        }
    
    def _calculate_reward(self, data: QueryData) -> float:
        """Calculate reward for learning"""
        # Update environment with current state
        self.environment.current_text_difficulty = data.text_difficulty
        self.environment.user_engagement = data.user_engagement
        self.environment.user_comprehension = data.user_comprehension
        self.environment.text_progress = data.text_progress
        
        # Calculate reward
        return self.environment._calculate_reward()
    
    def _get_current_settings(self) -> Dict[str, float]:
        """Get current settings"""
        return {
            'reading_speed': self.current_reading_speed,
            'pause_frequency': self.current_pause_frequency,
            'highlight_intensity': self.current_highlight_intensity,
            'chunk_size': self.current_chunk_size
        }
    
    def update_settings(self, new_settings: Dict[str, float]):
        """Update current settings"""
        if 'reading_speed' in new_settings:
            self.current_reading_speed = new_settings['reading_speed']
        if 'pause_frequency' in new_settings:
            self.current_pause_frequency = new_settings['pause_frequency']
        if 'highlight_intensity' in new_settings:
            self.current_highlight_intensity = new_settings['highlight_intensity']
        if 'chunk_size' in new_settings:
            self.current_chunk_size = new_settings['chunk_size']
    
    def reset_session(self):
        """Reset session data"""
        self.command_history = []
        self.text_progress = 0.0
        self.session_duration = 0.0

# Example usage function
async def example_usage():
    """Example of how to use the ReadingAgent"""
    
    # Create agent
    agent = ReadingAgent()
    
    # Prepare query data
    query_data = QueryData(
        # Text Analysis (REQUIRED)
        text_difficulty=0.6,
        text_type=0.8,
        text_length=0.7,
        
        # User Behavior (REQUIRED)
        user_engagement=0.8,
        user_comprehension=0.7,
        recent_commands=['faster', 'repeat', 'explain'],
        text_progress=0.4,
        
        # Session Data (REQUIRED)
        current_reading_speed=1.0,
        current_pause_frequency=0.3,
        current_highlight_intensity=0.5,
        current_chunk_size=0.5,
        
        # Optional Data
        session_duration=300.0,
        action_count=15,
        preferred_speed=1.1,
        preferred_pauses=0.3,
        preferred_highlighting=0.6
    )
    
    # Process query
    result = await agent.process_query(query_data)
    
    # Print results
    print("Recommendations:", result['recommendations'])
    print("Current Settings:", result['current_settings'])
    print("Reward:", result['learning_data']['reward'])
    
    return result

if __name__ == "__main__":
    asyncio.run(example_usage())
