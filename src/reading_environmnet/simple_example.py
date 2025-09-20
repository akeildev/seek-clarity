# Simple Example: What You Need to Provide
import asyncio
from reading_agent import ReadingAgent, QueryData
from data_collector import DataCollector

async def main():
    """Simple example showing exactly what data you need to provide"""
    
    print("=" * 60)
    print("SIMPLE EXAMPLE: WHAT YOU NEED TO PROVIDE")
    print("=" * 60)
    
    # 1. Create the reading agent
    agent = ReadingAgent()
    
    # 2. Create a data collector to help manage session data
    collector = DataCollector()
    collector.start_session()
    
    # 3. Simulate user commands (you get these from voice input)
    collector.add_command('faster')
    collector.add_command('repeat')
    collector.add_command('explain')
    collector.update_progress(0.4)  # 40% through the text
    
    # 4. Create the query data - THIS IS WHAT YOU NEED TO PROVIDE
    query_data = QueryData(
        # REQUIRED: Text Analysis (from MCP tools or TTS API)
        text_difficulty=0.6,    # How difficult is the text? (0.0 = easy, 1.0 = very hard)
        text_type=0.8,          # What type of text? (0.1 = email, 0.8 = academic, 0.4 = general)
        text_length=0.7,        # How long is the text? (0.0 = short, 1.0 = very long)
        
        # REQUIRED: User Behavior (from voice commands and interactions)
        user_engagement=0.8,    # How engaged is the user? (0.0 = not engaged, 1.0 = very engaged)
        user_comprehension=0.7, # How well does user understand? (0.0 = confused, 1.0 = understands well)
        recent_commands=['faster', 'repeat', 'explain'],  # Recent voice commands
        text_progress=0.4,      # How far through the text? (0.0 = start, 1.0 = finished)
        
        # REQUIRED: Current Settings (what the TTS is currently set to)
        current_reading_speed=1.0,      # Current speed (0.5 = slow, 1.5 = fast)
        current_pause_frequency=0.3,    # Current pause frequency (0.1 = few pauses, 0.8 = many pauses)
        current_highlight_intensity=0.5, # Current highlighting (0.0 = none, 1.0 = heavy)
        current_chunk_size=0.5,         # Current chunk size (0.1 = small chunks, 1.0 = large chunks)
        
        # OPTIONAL: Additional Data (if you have it)
        session_duration=300.0,         # How long has this session been? (seconds)
        action_count=15,                # How many actions has user taken?
        preferred_speed=1.1,            # User's preferred speed (learned over time)
        preferred_pauses=0.3,           # User's preferred pause frequency
        preferred_highlighting=0.6      # User's preferred highlighting
    )
    
    # 5. Process the query and get recommendations
    result = await agent.process_query(query_data)
    
    # 6. Print the results
    print("\nRECOMMENDATIONS:")
    print("-" * 30)
    for setting, value in result['recommendations'].items():
        print(f"{setting}: {value:.2f}")
    
    print("\nCURRENT SETTINGS:")
    print("-" * 30)
    for setting, value in result['current_settings'].items():
        print(f"{setting}: {value:.2f}")
    
    print(f"\nREWARD (for learning): {result['learning_data']['reward']:.2f}")
    
    print("\nREWARD BREAKDOWN:")
    print("-" * 30)
    for component, value in result['reward_breakdown'].items():
        if component != 'total_reward':
            print(f"{component}: {value:.2f}")
    
    return result

def show_data_requirements():
    """Show exactly what data you need to provide"""
    
    print("\n" + "=" * 60)
    print("DATA REQUIREMENTS SUMMARY")
    print("=" * 60)
    
    print("""
    REQUIRED DATA (you must provide these):
    
    1. TEXT ANALYSIS (from MCP tools or TTS API):
       - text_difficulty: 0.0-1.0 (how hard is the text?)
       - text_type: 0.0-1.0 (what type of text?)
       - text_length: 0.0-1.0 (how long is the text?)
    
    2. USER BEHAVIOR (from voice commands and interactions):
       - user_engagement: 0.0-1.0 (how engaged is user?)
       - user_comprehension: 0.0-1.0 (how well does user understand?)
       - recent_commands: List[str] (recent voice commands)
       - text_progress: 0.0-1.0 (how far through text?)
    
    3. CURRENT SETTINGS (what TTS is currently set to):
       - current_reading_speed: 0.5-1.5 (current speed)
       - current_pause_frequency: 0.1-0.8 (current pause frequency)
       - current_highlight_intensity: 0.0-1.0 (current highlighting)
       - current_chunk_size: 0.1-1.0 (current chunk size)
    
    OPTIONAL DATA (if you have it):
    - session_duration: float (session length in seconds)
    - action_count: int (number of user actions)
    - preferred_speed: float (user's preferred speed)
    - preferred_pauses: float (user's preferred pause frequency)
    - preferred_highlighting: float (user's preferred highlighting)
    
    HOW TO GET THIS DATA:
    
    1. From TTS API:
       - text_difficulty: API difficulty score
       - text_type: API content type classification
       - text_length: API word count / 1000
       - current_*: Current TTS settings
    
    2. From Voice Commands:
       - recent_commands: List of recent commands
       - user_engagement: Analyze command patterns
       - user_comprehension: Analyze command patterns
    
    3. From User Interface:
       - text_progress: Track reading progress
       - session_duration: Track session time
       - action_count: Count user actions
    """)

def show_example_implementations():
    """Show example implementations for different data sources"""
    
    print("\n" + "=" * 60)
    print("EXAMPLE IMPLEMENTATIONS")
    print("=" * 60)
    
    print("""
    EXAMPLE 1: From TTS API Response
    ```python
    # TTS API returns something like:
    tts_response = {
        'difficulty_score': 0.6,
        'content_type': 'academic',
        'word_count': 700,
        'current_speed': 1.0,
        'current_pauses': 0.3,
        'current_highlighting': 0.5
    }
    
    # Convert to QueryData:
    query_data = QueryData(
        text_difficulty=tts_response['difficulty_score'],
        text_type=0.8 if tts_response['content_type'] == 'academic' else 0.4,
        text_length=tts_response['word_count'] / 1000.0,
        user_engagement=0.8,  # Calculate from user behavior
        user_comprehension=0.7,  # Calculate from user behavior
        recent_commands=['faster', 'repeat'],
        text_progress=0.4,
        current_reading_speed=tts_response['current_speed'],
        current_pause_frequency=tts_response['current_pauses'],
        current_highlight_intensity=tts_response['current_highlighting'],
        current_chunk_size=0.5
    )
    ```
    
    EXAMPLE 2: From MCP Tools Analysis
    ```python
    # MCP tools analyze text and user behavior:
    mcp_analysis = {
        'text_difficulty': 0.6,
        'text_type': 0.8,
        'text_length': 0.7,
        'user_engagement': 0.8,
        'user_comprehension': 0.7
    }
    
    # Convert to QueryData:
    query_data = QueryData(
        text_difficulty=mcp_analysis['text_difficulty'],
        text_type=mcp_analysis['text_type'],
        text_length=mcp_analysis['text_length'],
        user_engagement=mcp_analysis['user_engagement'],
        user_comprehension=mcp_analysis['user_comprehension'],
        recent_commands=['faster', 'repeat'],
        text_progress=0.4,
        current_reading_speed=1.0,
        current_pause_frequency=0.3,
        current_highlight_intensity=0.5,
        current_chunk_size=0.5
    )
    ```
    
    EXAMPLE 3: Simple Implementation
    ```python
    # If you only have basic data:
    query_data = QueryData(
        text_difficulty=0.5,  # Default moderate difficulty
        text_type=0.4,        # Default general text
        text_length=0.5,      # Default medium length
        user_engagement=0.5,  # Default neutral engagement
        user_comprehension=0.5,  # Default neutral comprehension
        recent_commands=[],   # No commands yet
        text_progress=0.0,    # Start of text
        current_reading_speed=1.0,      # Default speed
        current_pause_frequency=0.3,    # Default pauses
        current_highlight_intensity=0.5, # Default highlighting
        current_chunk_size=0.5          # Default chunk size
    )
    ```
    """)

if __name__ == "__main__":
    asyncio.run(main())
    show_data_requirements()
    show_example_implementations()
