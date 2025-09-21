# Data Collection Helper for Reading Agent
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from reading_agent import QueryData

class DataCollector:
    """Helper class to collect and format data for the reading agent"""
    
    def __init__(self):
        self.session_start_time = None
        self.command_history = []
        self.text_progress = 0.0
        self.session_count = 0
        
    def start_session(self):
        """Start a new reading session"""
        self.session_start_time = time.time()
        self.command_history = []
        self.text_progress = 0.0
        self.session_count += 1
    
    def end_session(self):
        """End current reading session"""
        self.session_start_time = None
    
    def add_command(self, command: str):
        """Add a user command to history"""
        self.command_history.append(command)
        # Keep only last 10 commands
        if len(self.command_history) > 10:
            self.command_history = self.command_history[-10:]
    
    def update_progress(self, progress: float):
        """Update text reading progress (0.0 to 1.0)"""
        self.text_progress = max(0.0, min(1.0, progress))
    
    def get_session_duration(self) -> float:
        """Get current session duration in seconds"""
        if self.session_start_time is None:
            return 0.0
        return time.time() - self.session_start_time
    
    def create_query_data(
        self,
        # REQUIRED: Text Analysis
        text_difficulty: float,
        text_type: float,
        text_length: float,
        
        # REQUIRED: User Behavior
        user_engagement: float,
        user_comprehension: float,
        text_progress: float,
        
        # REQUIRED: Current Settings
        current_reading_speed: float,
        current_pause_frequency: float,
        current_highlight_intensity: float,
        current_chunk_size: float,
        
        # OPTIONAL: Additional Data
        recent_commands: Optional[List[str]] = None,
        preferred_speed: Optional[float] = None,
        preferred_pauses: Optional[float] = None,
        preferred_highlighting: Optional[float] = None,
        session_duration: Optional[float] = None,
        action_count: Optional[int] = None
    ) -> QueryData:
        """Create QueryData object with validation"""
        
        # Use session data if not provided
        if recent_commands is None:
            recent_commands = self.command_history.copy()
        
        if session_duration is None:
            session_duration = self.get_session_duration()
        
        if action_count is None:
            action_count = len(self.command_history)
        
        # Create QueryData object
        return QueryData(
            # Text Analysis
            text_difficulty=text_difficulty,
            text_type=text_type,
            text_length=text_length,
            
            # User Behavior
            user_engagement=user_engagement,
            user_comprehension=user_comprehension,
            recent_commands=recent_commands,
            text_progress=text_progress,
            
            # Session Data
            current_reading_speed=current_reading_speed,
            current_pause_frequency=current_pause_frequency,
            current_highlight_intensity=current_highlight_intensity,
            current_chunk_size=current_chunk_size,
            
            # Optional Data
            session_duration=session_duration,
            action_count=action_count,
            preferred_speed=preferred_speed,
            preferred_pauses=preferred_pauses,
            preferred_highlighting=preferred_highlighting
        )

# Helper functions for common data collection scenarios

def create_query_from_tts_api(
    tts_response: Dict[str, Any],
    user_commands: List[str],
    current_settings: Dict[str, float],
    data_collector: DataCollector
) -> QueryData:
    """Create QueryData from TTS API response"""
    
    return data_collector.create_query_data(
        # Text Analysis (from TTS API)
        text_difficulty=tts_response.get('difficulty_score', 0.5),
        text_type=tts_response.get('content_type', 0.4),
        text_length=tts_response.get('word_count', 0) / 1000.0,
        
        # User Behavior (from commands and analysis)
        user_engagement=calculate_engagement_from_commands(user_commands),
        user_comprehension=calculate_comprehension_from_commands(user_commands),
        text_progress=data_collector.text_progress,
        
        # Current Settings
        current_reading_speed=current_settings.get('reading_speed', 1.0),
        current_pause_frequency=current_settings.get('pause_frequency', 0.3),
        current_highlight_intensity=current_settings.get('highlight_intensity', 0.5),
        current_chunk_size=current_settings.get('chunk_size', 0.5),
        
        # Additional Data
        recent_commands=user_commands,
        session_duration=data_collector.get_session_duration(),
        action_count=len(user_commands)
    )

def create_query_from_mcp_analysis(
    mcp_analysis: Dict[str, Any],
    user_commands: List[str],
    current_settings: Dict[str, float],
    data_collector: DataCollector
) -> QueryData:
    """Create QueryData from MCP tools analysis"""
    
    return data_collector.create_query_data(
        # Text Analysis (from MCP tools)
        text_difficulty=mcp_analysis.get('text_difficulty', 0.5),
        text_type=mcp_analysis.get('text_type', 0.4),
        text_length=mcp_analysis.get('text_length', 0.5),
        
        # User Behavior (from MCP analysis)
        user_engagement=mcp_analysis.get('user_engagement', 0.5),
        user_comprehension=mcp_analysis.get('user_comprehension', 0.5),
        text_progress=data_collector.text_progress,
        
        # Current Settings
        current_reading_speed=current_settings.get('reading_speed', 1.0),
        current_pause_frequency=current_settings.get('pause_frequency', 0.3),
        current_highlight_intensity=current_settings.get('highlight_intensity', 0.5),
        current_chunk_size=current_settings.get('chunk_size', 0.5),
        
        # Additional Data
        recent_commands=user_commands,
        session_duration=data_collector.get_session_duration(),
        action_count=len(user_commands)
    )

def calculate_engagement_from_commands(commands: List[str]) -> float:
    """Calculate user engagement from voice commands"""
    if not commands:
        return 0.5  # Neutral engagement
    
    # Positive engagement indicators
    positive_commands = ['continue', 'faster', 'slower', 'repeat', 'explain', 'more', 'yes', 'good']
    negative_commands = ['stop', 'pause', 'skip', 'enough', 'quit', 'no', 'bad']
    
    positive_count = sum(1 for cmd in commands if any(pos in cmd.lower() for pos in positive_commands))
    negative_count = sum(1 for cmd in commands if any(neg in cmd.lower() for neg in negative_commands))
    
    if positive_count + negative_count == 0:
        return 0.5
    
    return positive_count / (positive_count + negative_count)

def calculate_comprehension_from_commands(commands: List[str]) -> float:
    """Calculate user comprehension from voice commands"""
    if not commands:
        return 0.5  # Neutral comprehension
    
    # Comprehension indicators
    confusion_commands = ['explain', 'what', 'why', 'how', 'repeat', 'clarify', 'confused', 'huh']
    confidence_commands = ['got it', 'understand', 'clear', 'makes sense', 'continue', 'okay', 'yes']
    
    confusion_count = sum(1 for cmd in commands if any(conf in cmd.lower() for conf in confusion_commands))
    confidence_count = sum(1 for cmd in commands if any(conf in cmd.lower() for conf in confidence_commands))
    
    if confusion_count + confidence_count == 0:
        return 0.5
    
    return confidence_count / (confusion_count + confidence_count)

# Example usage
def example_data_collection():
    """Example of how to use the DataCollector"""
    
    # Create data collector
    collector = DataCollector()
    collector.start_session()
    
    # Simulate user commands
    collector.add_command('faster')
    collector.add_command('repeat')
    collector.add_command('explain')
    collector.update_progress(0.4)
    
    # Create query data
    query_data = collector.create_query_data(
        # Text Analysis
        text_difficulty=0.6,
        text_type=0.8,
        text_length=0.7,
        
        # User Behavior
        user_engagement=0.8,
        user_comprehension=0.7,
        text_progress=0.4,
        
        # Current Settings
        current_reading_speed=1.0,
        current_pause_frequency=0.3,
        current_highlight_intensity=0.5,
        current_chunk_size=0.5
    )
    
    print("Query Data created:")
    print(f"Text Difficulty: {query_data.text_difficulty}")
    print(f"User Engagement: {query_data.user_engagement}")
    print(f"Recent Commands: {query_data.recent_commands}")
    print(f"Session Duration: {query_data.session_duration}")
    
    return query_data

if __name__ == "__main__":
    example_data_collection()
