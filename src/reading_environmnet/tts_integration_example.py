#!/usr/bin/env python3
"""
Example of how to use the Reading Environment with TTS integration
"""

import numpy as np
from reading_environment import ReadingEnvironment
from reading_a2c import ReadingA2C

def main():
    """Demonstrate TTS integration with A2C agent"""

    # Initialize environment
    print("Initializing Reading Environment with TTS integration...")
    env = ReadingEnvironment(state_size=20, action_size=8)

    # Initialize A2C agent
    print("Initializing A2C agent...")
    agent = ReadingA2C(state_size=20, action_size=8)

    # Connect them
    env.set_a2c_agent(agent)

    # Example text analysis state
    state_data = {
        'text_difficulty': 0.7,      # Difficult text
        'text_length': 0.8,          # Long text
        'text_type': 0.6,            # Technical text
        'reading_speed': 1.0,        # Current reading speed
        'pause_frequency': 0.3,      # Current pause frequency
        'highlight_intensity': 0.5,  # Current highlighting
        'chunk_size': 0.5,           # Current chunk size
        'user_engagement': 0.6,      # User engagement level
        'user_comprehension': 0.7,   # User comprehension
        'session_progress': 0.2,     # 20% through session
        'action_count': 5,           # Number of actions taken
        'recent_commands': 0.1       # Recent command activity
    }

    print("\n" + "="*50)
    print("EXAMPLE: Adapting TTS settings for difficult text")
    print("="*50)

    # Simulate the A2C agent making decisions
    print(f"Input state: Difficult text (difficulty: {state_data['text_difficulty']})")
    print(f"User comprehension: {state_data['user_comprehension']}")
    print(f"User engagement: {state_data['user_engagement']}")

    # Get current TTS settings
    print(f"\nCurrent TTS settings:")
    current_tts = env.get_current_tts_settings()
    for key, value in current_tts.items():
        print(f"  {key}: {value}")

    # Get A2C recommendations
    print(f"\nA2C agent recommendations:")
    recommended_tts = env.get_a2c_recommended_tts_settings(state_data)
    for key, value in recommended_tts.items():
        print(f"  {key}: {value}")

    # Simulate applying an action from the A2C agent
    print(f"\nSimulating A2C action...")

    # Create a sample action that would adapt to difficult text:
    # - Slower speech (action[0] = -0.3)
    # - More pauses (action[1] = 0.4)
    # - Lower pitch for clarity (action[3] = -0.2)
    # - Slightly higher volume (action[4] = 0.1)
    # - Higher clarity (action[5] = 0.3)
    # - Smaller chunks (action[6] = -0.3)
    sample_action = np.array([-0.3, 0.4, 0.2, -0.2, 0.1, 0.3, -0.3, 0.0])

    # Apply the action through the environment
    env.current_text_difficulty = state_data['text_difficulty']
    env.user_comprehension = state_data['user_comprehension']
    env.user_engagement = state_data['user_engagement']

    # Reset and step
    state, _ = env.reset()
    next_state, reward, done, truncated, info = env.step(sample_action)

    print(f"\nAfter applying A2C action:")
    updated_tts = env.get_current_tts_settings()
    for key, value in updated_tts.items():
        print(f"  {key}: {value}")

    # Show reward breakdown
    print(f"\nReward breakdown:")
    reward_breakdown = env.get_reward_breakdown()
    for component, reward_value in reward_breakdown.items():
        print(f"  {component}: {reward_value:.3f}")

    print(f"\nTotal reward: {reward:.3f}")

    # Example of manual TTS setting update
    print(f"\n" + "="*50)
    print("EXAMPLE: Manual TTS setting adjustment")
    print("="*50)

    # Update a specific TTS setting
    success = env.update_tts_setting('voice_speed', 0.8)
    print(f"Updated voice_speed to 0.8: {'Success' if success else 'Failed'}")

    # Show the change
    print(f"New voice_speed: {env.get_current_tts_settings()['voice_speed']}")

    print(f"\n" + "="*50)
    print("EXAMPLE: Session tracking with TTS")
    print("="*50)

    # Start a session and show how TTS settings are tracked
    env.start_session()
    print("Started new session - TTS settings will be tracked")

    # Simulate some reading progress
    env.update_text_progress(0.5)
    print("Updated text progress to 50%")

    # Make another adjustment
    env._apply_action(np.array([0.2, -0.1, 0.0, 0.1, 0.0, 0.0, 0.2, 0.0]))
    print("Applied another A2C action")

    # End session
    env.end_session()
    print("Ended session")

    # Show session data
    if env.reading_sessions:
        last_session = env.reading_sessions[-1]
        print(f"\nSession data:")
        print(f"  Duration: {last_session.get('duration', 'N/A'):.2f} seconds")
        print(f"  Initial TTS settings: {last_session['initial_tts_settings']['voice_speed']}")
        print(f"  Final TTS settings: {last_session['final_tts_settings']['voice_speed']}")

    print(f"\n" + "="*50)
    print("Integration complete! TTS settings are now connected to A2C output.")
    print("="*50)

if __name__ == "__main__":
    main()