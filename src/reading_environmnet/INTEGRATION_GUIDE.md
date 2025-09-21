# A2C-TTS Integration Guide

## Overview

The A2C (Advantage Actor-Critic) agent is now fully integrated with the TTS system and voice agent. The system automatically adjusts TTS settings based on conversation analysis and reinforcement learning.

## How It Works

### 1. Conversation Analysis
Every user interaction is analyzed for:
- **Text Difficulty**: Based on sentence complexity, technical terms, and length
- **User Engagement**: Detected through questions, enthusiasm markers, and response patterns
- **User Comprehension**: Estimated from engagement and conversation flow

### 2. A2C Decision Making
The A2C agent uses these conversation metrics to:
- Adjust voice speed (slower for complex topics)
- Modify pause lengths (more pauses for difficult content)
- Change chunk sizes (smaller chunks for complex text)
- Fine-tune pitch, volume, and clarity

### 3. Reward System
The system learns from:
- **Speed Optimization**: Matching reading speed to content difficulty
- **Engagement Rewards**: Maintaining user interest
- **Comprehension Rewards**: Ensuring understanding
- **TTS Quality**: Optimal voice settings for context
- **User Preferences**: Learning individual preferences over time

## Console Monitoring

When running the voice agent, you'll see detailed feedback:

```
============================================================
A2C TRAINING FEEDBACK
============================================================
CONVERSATION STATE:
  Text Difficulty: 0.750
  User Engagement: 0.600
  User Comprehension: 0.480
  Session Progress: 0.200
  Turn Count: 15

A2C ACTION OUTPUT:
  Action Vector: [-0.300, 0.400, 0.200, -0.200, 0.100, 0.300, -0.300, 0.000]

RECOMMENDED TTS SETTINGS:
  Voice Speed: 0.800
  Pause Length: 0.900
  Chunk Size: 120

REWARD SIGNAL: 2.150

REWARD BREAKDOWN:
  speed_reward: 0.800
  engagement_reward: 0.500
  comprehension_reward: 0.400
  tts_reward: 0.450
============================================================
```

## Training Status Updates

Every 5 conversation turns, you'll see:

```
============================================================
TRAINING STATUS UPDATE
============================================================
DATA COLLECTION:
  Episodes Collected: 8
  Buffer States: 12
  Average Reward: 1.850
  Collection Active: true

TRAINING:
  Total Training Steps: 2
  Time Since Last Training: 45.2s
  Next Training In: 214.8s

DATA COLLECTION SUGGESTIONS:
  • Continue conversation for more data
  • Try varying conversation complexity
============================================================
```

## Testing the System

### Quick Test
Run the monitor script to see the A2C system in action:
```bash
cd src/reading_environmnet
python monitor_a2c.py
```

### Integration Test
1. Start the voice agent normally
2. Have conversations with varying complexity
3. Watch console output for A2C feedback
4. Notice TTS adjustments based on conversation difficulty

## Configuration

### TTS Settings
The system automatically manages these TTS parameters:
- `voice_speed`: 0.5-2.0 (slower for complex content)
- `voice_pitch`: -0.5 to 0.5 (subtle adjustments)
- `voice_volume`: 0.3-1.0 (context-appropriate)
- `pause_length`: 0.1-2.0 (more pauses for difficulty)
- `chunk_size`: 50-300 characters (smaller for complex text)

### Training Parameters
- **Training Interval**: 300 seconds (5 minutes)
- **Episode Length**: Up to 50 conversation turns
- **Buffer Size**: Keeps recent 10 episodes
- **Reward Range**: -1.0 to 5.0

## Data Collection Strategy

The system collects training data from:

1. **Conversation Turns**: Each user input → AI response cycle
2. **State Vectors**: 20-dimensional vectors capturing conversation context
3. **Actions**: 8-dimensional continuous actions for TTS adjustments
4. **Rewards**: Comprehensive reward signal based on multiple factors

### What Makes Good Training Data

- **Varied Conversation Types**: Simple questions, complex explanations, technical discussions
- **Different Engagement Levels**: Enthusiastic users, confused users, disengaged users
- **Length Variation**: Short responses, long explanations, multi-part questions
- **Topic Diversity**: Different subjects requiring different speaking styles

## File Structure

```
src/reading_environmnet/
├── reading_environment.py     # Core environment with TTS integration
├── reading_a2c.py            # A2C agent implementation
├── training_scheduler.py     # Background training and data collection
├── tts_integration_example.py # Integration example
├── monitor_a2c.py           # Testing and monitoring script
├── training_data/           # Generated training data
│   ├── training_stats.json
│   └── episodes_*.json
└── tts_config.json         # Persistent TTS settings
```

## Troubleshooting

### No A2C Feedback
- Check that conversation analysis is working
- Ensure user inputs are being processed
- Verify the reading environment is initialized

### Low Rewards
- Check reward breakdown to see which components are low
- Ensure conversation variety (difficulty, engagement)
- Look for extreme TTS settings causing penalties

### Training Not Starting
- Need at least 2 episodes before training begins
- Check that data collection is active
- Verify sufficient conversation turns per episode

### Poor TTS Adjustments
- System learns over time - initial adjustments may be suboptimal
- Check if extreme penalty rewards are triggering
- Ensure conversation state analysis is accurate

## Performance Tips

1. **Longer Conversations**: More turns per episode = better training data
2. **Varied Complexity**: Mix simple and complex topics for robust learning
3. **Engagement Variation**: Include enthusiastic and disengaged interactions
4. **Consistent Use**: Regular conversations help the system learn preferences
5. **Monitor Console**: Watch feedback to understand system behavior

## Integration with Rest of Project

The A2C-TTS system integrates seamlessly with:
- **Voice Agent**: Automatic conversation analysis and TTS updates
- **LiveKit Service**: TTS settings applied through environment variables
- **Electron App**: No changes needed - works behind the scenes
- **MCP Router**: Conversation data flows through existing architecture

The system is designed to be:
- **Non-intrusive**: Works automatically without user intervention
- **Fail-safe**: Falls back to default settings if issues occur
- **Persistent**: Saves learned preferences across sessions
- **Monitorable**: Detailed console feedback for debugging