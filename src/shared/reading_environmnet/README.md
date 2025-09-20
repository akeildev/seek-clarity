# Reading Agent with A2C and MCP Tools Integration

This system provides an intelligent reading assistant that uses A2C (Advantage Actor-Critic) reinforcement learning to optimize reading parameters based on text content and user behavior, while maintaining complete independence between ElevenLabs voice settings and the A2C agent.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Tools     │───▶│  Settings Manager │───▶│   Voice Agent   │
│ (Text Analysis) │    │ (Feedback Loop)   │    │  (Main Interface)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   A2C Agent     │
                                                │ (RL Optimizer)  │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Reading Env     │
                                                │ (State Collector)│
                                                └─────────────────┘
```

## Key Components

### 1. VoiceAgent (`voice_agent.py`)
- **Main interface** for the reading assistant
- Coordinates between A2C agent and MCP tools
- Manages both A2C settings and ElevenLabs settings independently
- Provides async methods for text processing

### 2. ReadingA2C (`reading_a2c.py`)
- **Reinforcement learning agent** that optimizes reading parameters
- Uses 12-dimensional state space from MCP tools
- Provides recommendations for reading speed, pause frequency, etc.
- Completely independent of ElevenLabs voice settings

### 3. ReadingStateCollector (`mcp_utils.py`)
- **Collects 12 state dimensions** for A2C agent
- Integrates with MCP tools for text analysis
- Assesses text difficulty, user engagement, comprehension
- Provides normalized state vectors for neural network

### 4. SettingsManager (`settings_manager.py`)
- **Manages feedback loop** between MCP tools and voice agent
- Tracks setting changes and trends
- Handles async feedback processing
- Provides setting history and analysis

### 5. ReadingEnvironment (`reading_environment.py`)
- **Environment for A2C training**
- Integrates with state collector
- Provides reward calculation and action application

## State Dimensions (12 total)

The A2C agent uses these 12 dimensions collected via MCP tools:

1. **text_difficulty** - Assessed via text analysis
2. **text_length** - Normalized text length
3. **text_type** - Email, academic, news, etc.
4. **reading_speed** - Current reading speed setting
5. **pause_frequency** - Current pause frequency
6. **highlight_intensity** - Current highlight intensity
7. **chunk_size** - Current text chunk size
8. **user_engagement** - From user commands
9. **user_comprehension** - From user behavior
10. **session_progress** - Reading progress
11. **action_count** - Number of user actions
12. **recent_commands** - Recent command encoding

## Usage Examples

### Basic Usage

```python
import asyncio
from voice_agent import VoiceAgent

async def main():
    # Initialize agent
    agent = VoiceAgent()
    
    # Process text
    text = "Your text content here"
    commands = ["read this", "go faster"]
    
    result = await agent.process_text(text, commands)
    print("A2C Settings:", result['a2c_settings'])
    print("ElevenLabs Settings:", result['elevenlabs_settings'])
```

### MCP Tools Integration

```python
from settings_manager import SettingsManager

# Initialize settings manager
settings_manager = SettingsManager(agent)

# Apply MCP tools feedback
mcp_feedback = {
    'reading_analysis': {
        'suggested_speed': 0.9,
        'suggested_pauses': 0.6
    }
}

await settings_manager.apply_mcp_feedback(mcp_feedback)
```

### ElevenLabs Integration (Independent)

```python
# Update ElevenLabs settings independently
agent.update_elevenlabs_settings({
    'stability': 0.7,
    'similarity_boost': 0.8,
    'voice_id': 'custom_voice'
})
```

## Key Features

### 1. Complete Independence
- **ElevenLabs settings** are completely independent of A2C agent
- You can change voice, stability, similarity_boost without affecting A2C
- A2C only controls reading parameters (speed, pauses, highlighting)

### 2. MCP Tools Integration
- **Text analysis** via MCP tools feeds into state collection
- **User behavior analysis** provides engagement and comprehension metrics
- **Feedback loop** allows continuous improvement

### 3. Async Processing
- All MCP tool interactions are async
- Non-blocking feedback processing
- Concurrent state collection and recommendation generation

### 4. Settings Management
- **Complete history** of all setting changes
- **Trend analysis** for each setting type
- **Confidence scoring** for different feedback sources
- **Export/import** functionality for persistence

## MCP Tools Feedback Format

Your MCP tools should send feedback in this format:

```python
{
    'reading_analysis': {
        'text_difficulty': 0.8,
        'suggested_speed': 0.9,
        'suggested_pauses': 0.6,
        'comprehension_score': 0.7
    },
    'user_behavior': {
        'engagement_level': 0.8,
        'confusion_indicators': ['slower', 'repeat'],
        'preferred_style': 'academic'
    }
}
```

## Running the System

1. **Install dependencies**:
   ```bash
   pip install torch numpy asyncio
   ```

2. **Run the integration example**:
   ```bash
   python integration_example.py
   ```

3. **Use in your application**:
   ```python
   from voice_agent import VoiceAgent
   # See integration_example.py for complete usage
   ```

## Customization

### Adding New State Dimensions
1. Update `ReadingStateCollector.collect_reading_state()`
2. Update `get_state_vector()` method
3. Update A2C agent state size if needed

### Adding New MCP Tools
1. Implement new analysis methods in `ReadingStateCollector`
2. Update `_parse_mcp_feedback()` in `SettingsManager`
3. Add new setting types to `SettingType` enum

### Modifying A2C Behavior
1. Adjust action mappings in `get_recommended_settings()`
2. Modify reward calculation in `ReadingEnvironment`
3. Update neural network architecture in `ReadingA2C`

This system provides a robust foundation for intelligent reading assistance with complete separation between voice synthesis (ElevenLabs) and reading optimization (A2C), while maintaining seamless integration with MCP tools for continuous improvement.
