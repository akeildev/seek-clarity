# Implementation Guide: What You Need to Provide

## Quick Start

The reading agent needs specific data from each query to make intelligent recommendations. Here's exactly what you need to provide:

## Required Data (You Must Provide These)

### 1. Text Analysis (from MCP tools or TTS API)
```python
text_analysis = {
    'text_difficulty': 0.6,    # 0.0 = very easy, 1.0 = very difficult
    'text_type': 0.8,          # 0.1 = email, 0.8 = academic, 0.4 = general
    'text_length': 0.7,        # 0.0 = short, 1.0 = very long (normalized)
}
```

### 2. User Behavior (from voice commands and interactions)
```python
user_behavior = {
    'user_engagement': 0.8,    # 0.0 = not engaged, 1.0 = very engaged
    'user_comprehension': 0.7, # 0.0 = confused, 1.0 = understands well
    'recent_commands': ['faster', 'repeat', 'explain'],  # Recent voice commands
    'text_progress': 0.4,      # 0.0 = start, 1.0 = finished
}
```

### 3. Current Settings (what TTS is currently set to)
```python
current_settings = {
    'current_reading_speed': 1.0,      # 0.5 = slow, 1.5 = fast
    'current_pause_frequency': 0.3,    # 0.1 = few pauses, 0.8 = many pauses
    'current_highlight_intensity': 0.5, # 0.0 = none, 1.0 = heavy
    'current_chunk_size': 0.5,         # 0.1 = small chunks, 1.0 = large chunks
}
```

## Optional Data (If You Have It)

```python
optional_data = {
    'session_duration': 300.0,         # Session length in seconds
    'action_count': 15,                # Number of user actions
    'preferred_speed': 1.1,            # User's preferred speed
    'preferred_pauses': 0.3,           # User's preferred pause frequency
    'preferred_highlighting': 0.6      # User's preferred highlighting
}
```

## How to Use

### 1. Basic Usage
```python
from reading_agent import ReadingAgent, QueryData

# Create agent
agent = ReadingAgent()

# Create query data
query_data = QueryData(
    # REQUIRED: Text Analysis
    text_difficulty=0.6,
    text_type=0.8,
    text_length=0.7,
    
    # REQUIRED: User Behavior
    user_engagement=0.8,
    user_comprehension=0.7,
    recent_commands=['faster', 'repeat'],
    text_progress=0.4,
    
    # REQUIRED: Current Settings
    current_reading_speed=1.0,
    current_pause_frequency=0.3,
    current_highlight_intensity=0.5,
    current_chunk_size=0.5
)

# Get recommendations
result = await agent.process_query(query_data)
print("Recommendations:", result['recommendations'])
```

### 2. Using Data Collector Helper
```python
from data_collector import DataCollector

# Create data collector
collector = DataCollector()
collector.start_session()

# Add user commands
collector.add_command('faster')
collector.add_command('repeat')
collector.update_progress(0.4)

# Create query data
query_data = collector.create_query_data(
    text_difficulty=0.6,
    text_type=0.8,
    text_length=0.7,
    user_engagement=0.8,
    user_comprehension=0.7,
    text_progress=0.4,
    current_reading_speed=1.0,
    current_pause_frequency=0.3,
    current_highlight_intensity=0.5,
    current_chunk_size=0.5
)
```

## Data Sources

### From TTS API
```python
# If your TTS API provides these metrics:
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

### From MCP Tools
```python
# If you have MCP tools analysis:
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

## Data Validation

The agent automatically validates your data and will raise errors if:
- Values are outside the required ranges
- Required fields are missing
- Data types are incorrect

## What You Get Back

```python
result = await agent.process_query(query_data)

# Recommendations for optimal settings
recommendations = result['recommendations']
# {
#     'recommended_reading_speed': 1.1,
#     'recommended_pause_frequency': 0.4,
#     'recommended_highlight_intensity': 0.6,
#     'recommended_chunk_size': 0.5
# }

# Current settings
current_settings = result['current_settings']

# Learning data for training
learning_data = result['learning_data']

# Reward breakdown for debugging
reward_breakdown = result['reward_breakdown']
```

## Files Overview

- `reading_agent.py` - Main agent interface
- `data_collector.py` - Helper for collecting and formatting data
- `reading_environment.py` - Environment with improved reward function
- `reading_a2c.py` - A2C reinforcement learning agent
- `mcp_utils.py` - MCP tools integration
- `simple_example.py` - Complete working example

## Running the Example

```bash
python simple_example.py
```

This will show you exactly what data you need to provide and how to use the agent.

## Key Points

1. **You must provide the required data** - the agent needs this to make intelligent decisions
2. **Data ranges are important** - values must be within the specified ranges
3. **User behavior is key** - engagement and comprehension are crucial for good recommendations
4. **The agent learns** - it uses your data to improve recommendations over time
5. **ElevenLabs settings are independent** - the agent only controls reading parameters, not voice synthesis

This implementation provides a clean, simple interface while maintaining the powerful A2C learning capabilities.
