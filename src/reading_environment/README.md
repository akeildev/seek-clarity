# Reading Agent - Standalone Package

This is a standalone reading agent package that works independently without requiring the rest of the project. It provides intelligent reading assistance using A2C (Advantage Actor-Critic) reinforcement learning.

## Quick Start

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

## Files

- `reading_agent.py` - Main agent interface
- `data_collector.py` - Helper for collecting data
- `reading_environment.py` - Environment with reward function
- `reading_a2c.py` - A2C reinforcement learning agent
- `simple_example.py` - Complete working example
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation guide

## Required Data

You need to provide these data points for each query:

### Text Analysis (from MCP tools or TTS API)
- `text_difficulty`: 0.0-1.0 (how hard is the text?)
- `text_type`: 0.0-1.0 (what type of text?)
- `text_length`: 0.0-1.0 (how long is the text?)

### User Behavior (from voice commands)
- `user_engagement`: 0.0-1.0 (how engaged is user?)
- `user_comprehension`: 0.0-1.0 (how well does user understand?)
- `recent_commands`: List[str] (recent voice commands)
- `text_progress`: 0.0-1.0 (how far through text?)

### Current Settings (what TTS is currently set to)
- `current_reading_speed`: 0.5-1.5 (current speed)
- `current_pause_frequency`: 0.1-0.8 (current pause frequency)
- `current_highlight_intensity`: 0.0-1.0 (current highlighting)
- `current_chunk_size`: 0.1-1.0 (current chunk size)

## What You Get Back

```python
result = await agent.process_query(query_data)

# Recommendations for optimal settings
recommendations = result['recommendations']
# {
#     'recommended_reading_speed': 1.12,
#     'recommended_pause_frequency': 0.49,
#     'recommended_highlight_intensity': 0.67,
#     'recommended_chunk_size': 0.45
# }

# Current settings
current_settings = result['current_settings']

# Learning data for training
learning_data = result['learning_data']

# Reward breakdown for debugging
reward_breakdown = result['reward_breakdown']
```

## Testing

Run the example to see it in action:

```bash
python simple_example.py
```

## Dependencies

- Python 3.7+
- torch
- numpy
- asyncio (built-in)

## Integration

This package is designed to work with your account routing system. You can:

1. Import it from your main application
2. Use it as a standalone service
3. Integrate it with your MCP tools
4. Connect it to your TTS API

The agent learns from your data and provides increasingly better recommendations over time.
