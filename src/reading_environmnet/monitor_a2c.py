#!/usr/bin/env python3
"""
A2C Training Monitor and Testing Script
Run this to see A2C training feedback and test the system
"""

import asyncio
import time
import json
import logging
from pathlib import Path
import numpy as np

# Setup logging to match voice agent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("a2c-monitor")

# Import our components
from reading_environment import ReadingEnvironment
from reading_a2c import ReadingA2C
from training_scheduler import A2CTrainingScheduler

class A2CMonitor:
    """Monitor and test A2C training system"""

    def __init__(self):
        # Initialize components
        self.reading_env = ReadingEnvironment(state_size=20, action_size=8)
        self.a2c_agent = ReadingA2C(state_size=20, action_size=8)
        self.reading_env.set_a2c_agent(self.a2c_agent)

        self.training_scheduler = A2CTrainingScheduler(
            self.reading_env,
            self.a2c_agent,
            training_interval=60  # Train every minute for testing
        )

        # Test conversation scenarios with QueryData features
        self.test_scenarios = [
            {
                'name': 'Simple Question',
                'user_input': 'What is the weather like?',
                'expected_difficulty': 0.2,
                'expected_engagement': 0.4,
                'expected_commands': []
            },
            {
                'name': 'Complex Technical Query',
                'user_input': 'Can you explain the differences between reinforcement learning algorithms like A2C, PPO, and DQN, particularly in terms of their policy gradient methods and value function estimation techniques?',
                'expected_difficulty': 0.9,
                'expected_engagement': 0.8,
                'expected_commands': ['explain']
            },
            {
                'name': 'Speed Command',
                'user_input': 'That\'s too slow, can you speak faster please?',
                'expected_difficulty': 0.3,
                'expected_engagement': 0.6,
                'expected_commands': ['faster']
            },
            {
                'name': 'Confusion Request',
                'user_input': 'I\'m confused about this part, can you repeat that more slowly?',
                'expected_difficulty': 0.6,
                'expected_engagement': 0.4,
                'expected_commands': ['repeat', 'slower']
            },
            {
                'name': 'Engaged Follow-up',
                'user_input': 'Yes, that\'s very helpful! Can you continue with more details?',
                'expected_difficulty': 0.5,
                'expected_engagement': 0.9,
                'expected_commands': ['continue']
            },
            {
                'name': 'Multiple Questions',
                'user_input': 'I have several questions. First, how does this work? Second, what are the benefits? And finally, what should I do next?',
                'expected_difficulty': 0.7,
                'expected_engagement': 0.7,
                'expected_commands': []
            }
        ]

    async def run_comprehensive_test(self):
        """Run comprehensive A2C testing and monitoring"""
        logger.info("="*80)
        logger.info("STARTING A2C COMPREHENSIVE TESTING")
        logger.info("="*80)

        # Start training scheduler
        self.training_scheduler.start_data_collection()
        logger.info("Training scheduler started")

        try:
            # Run test scenarios
            await self._run_test_scenarios()

            # Wait for training to occur
            await self._wait_for_training()

            # Test different conversation patterns
            await self._test_conversation_patterns()

            # Show final results
            await self._show_final_results()

        finally:
            await self.training_scheduler.stop_data_collection()
            logger.info("Training scheduler stopped")

    async def _run_test_scenarios(self):
        """Run predefined test scenarios"""
        logger.info("\n" + "="*60)
        logger.info("TESTING CONVERSATION SCENARIOS")
        logger.info("="*60)

        for i, scenario in enumerate(self.test_scenarios, 1):
            logger.info(f"\nSCENARIO {i}: {scenario['name']}")
            logger.info(f"Input: {scenario['user_input']}")

            # Simulate conversation analysis
            conversation_state = self._simulate_conversation_analysis(
                scenario['user_input'],
                scenario['expected_difficulty'],
                scenario['expected_engagement']
            )

            # Get A2C action and apply to environment
            current_state = self.reading_env._get_state_vector()
            action = self.a2c_agent.get_recommended_action(conversation_state)
            next_state, reward, done, truncated, info = self.reading_env.step(action)

            # Collect training data
            self.training_scheduler.collect_experience(
                state=current_state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done
            )

            # Log results
            self._log_scenario_results(scenario, conversation_state, action, reward)

            # Small delay between scenarios
            await asyncio.sleep(1)

    def _simulate_conversation_analysis(self, user_input: str, expected_difficulty: float, expected_engagement: float):
        """Simulate conversation analysis compatible with QueryData structure"""
        import re

        # Simulate complexity analysis
        complexity_indicators = [
            len(user_input.split()) > 15,
            len(re.findall(r'[.!?]+', user_input)) > 2,
            bool(re.search(r'\b(explain|describe|analyze|compare|why|how)\b', user_input.lower())),
            len(re.findall(r'\b[A-Z][a-z]+\b', user_input)) > 3,
        ]
        complexity_score = sum(complexity_indicators) / len(complexity_indicators)

        # Simulate engagement analysis
        engagement_indicators = [
            'thank' in user_input.lower(),
            '?' in user_input,
            len(user_input) > 20,
            bool(re.search(r'\b(yes|yeah|ok|sure|please|more)\b', user_input.lower())),
            user_input.count('!') > 0
        ]
        engagement_score = sum(engagement_indicators) / len(engagement_indicators)

        # Extract recent commands
        command_words = ['faster', 'slower', 'repeat', 'stop', 'continue', 'explain', 'clarify']
        recent_commands = [word for word in command_words if word in user_input.lower()]

        # Create QueryData-compatible conversation state
        state = {
            # Text Analysis (QueryData required fields)
            'text_difficulty': min(1.0, complexity_score + (len(user_input) / 200)),
            'text_type': complexity_score,
            'text_length': min(1.0, len(user_input) / 100),

            # User Behavior (QueryData required fields)
            'user_engagement': engagement_score,
            'user_comprehension': min(1.0, max(0.1, engagement_score * 0.8)),
            'recent_commands': recent_commands,
            'text_progress': 0.3,  # Simulated progress

            # Current Settings (QueryData required fields)
            'current_reading_speed': self.reading_env.current_reading_speed,
            'current_pause_frequency': self.reading_env.pause_frequency,
            'current_highlight_intensity': self.reading_env.highlight_intensity,
            'current_chunk_size': self.reading_env.tts_settings['chunk_size'] / 300.0,

            # Optional Data (QueryData optional fields)
            'session_duration': 180.0,  # Simulated 3 minutes
            'action_count': 1
        }

        return state

    def _log_scenario_results(self, scenario: dict, state: dict, action: np.ndarray, reward: float):
        """Log results for a test scenario with QueryData structure"""
        logger.info(f"  TEXT ANALYSIS:")
        logger.info(f"    Difficulty: {scenario['expected_difficulty']:.3f} → {state['text_difficulty']:.3f}")
        logger.info(f"    Text Type: {state['text_type']:.3f}")
        logger.info(f"    Text Length: {state['text_length']:.3f}")

        logger.info(f"  USER BEHAVIOR:")
        logger.info(f"    Engagement: {scenario['expected_engagement']:.3f} → {state['user_engagement']:.3f}")
        logger.info(f"    Comprehension: {state['user_comprehension']:.3f}")
        logger.info(f"    Expected Commands: {scenario.get('expected_commands', [])}")
        logger.info(f"    Detected Commands: {state['recent_commands']}")

        logger.info(f"  A2C ACTION: [{', '.join([f'{x:.3f}' for x in action])}]")
        logger.info(f"  REWARD: {reward:.3f}")

        # Show TTS adjustments
        tts_settings = self.reading_env.get_current_tts_settings()
        logger.info(f"  TTS ADJUSTMENTS:")
        logger.info(f"    Voice Speed: {tts_settings['voice_speed']:.3f}")
        logger.info(f"    Pause Length: {tts_settings['pause_length']:.3f}")
        logger.info(f"    Chunk Size: {int(tts_settings['chunk_size'])}")

        # Show reward components that are non-zero
        rewards = self.reading_env.get_reward_breakdown()
        logger.info(f"  REWARD COMPONENTS:")
        for component, value in rewards.items():
            if abs(value) > 0.01:  # Only show significant components
                logger.info(f"    {component}: {value:.3f}")

    async def _wait_for_training(self):
        """Wait for and monitor training"""
        logger.info("\n" + "="*60)
        logger.info("WAITING FOR A2C TRAINING")
        logger.info("="*60)

        # Check if we have enough data for training
        status = self.training_scheduler.get_training_status()
        logger.info(f"Episodes collected: {status['episodes_collected']}")
        logger.info(f"Buffer sizes: {status['buffer_sizes']}")

        if status['episodes_collected'] < 2:
            logger.info("Not enough episodes for training, generating more data...")
            await self._generate_more_training_data()

        # Force training to demonstrate
        logger.info("Forcing training to demonstrate...")
        success = self.training_scheduler.force_training()
        if success:
            logger.info("✓ Training initiated")
            await asyncio.sleep(5)  # Wait for training to complete
        else:
            logger.warning("Could not force training - insufficient data")

    async def _generate_more_training_data(self):
        """Generate additional training data"""
        logger.info("Generating additional training data...")

        additional_inputs = [
            "Help me understand this concept",
            "That's interesting, tell me more",
            "I'm confused about this part",
            "Can you repeat that?",
            "Perfect, that makes sense now!"
        ]

        for input_text in additional_inputs:
            state = self._simulate_conversation_analysis(input_text, 0.5, 0.6)
            current_state = self.reading_env._get_state_vector()
            action = self.a2c_agent.get_recommended_action(state)
            next_state, reward, done, truncated, info = self.reading_env.step(action)

            self.training_scheduler.collect_experience(
                state=current_state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done
            )

            await asyncio.sleep(0.5)

        logger.info("✓ Additional training data generated")

    async def _test_conversation_patterns(self):
        """Test different conversation patterns"""
        logger.info("\n" + "="*60)
        logger.info("TESTING CONVERSATION PATTERNS")
        logger.info("="*60)

        patterns = [
            "Pattern 1: Increasing complexity",
            "Pattern 2: High engagement session",
            "Pattern 3: Low engagement recovery"
        ]

        for pattern in patterns:
            logger.info(f"\nTesting: {pattern}")
            await self._simulate_pattern(pattern)

    async def _simulate_pattern(self, pattern_name: str):
        """Simulate a specific conversation pattern"""
        if "complexity" in pattern_name:
            # Gradually increase difficulty
            difficulties = [0.2, 0.4, 0.6, 0.8]
            engagements = [0.5, 0.6, 0.7, 0.6]  # Slight drop at high difficulty
        elif "High engagement" in pattern_name:
            # Maintain high engagement
            difficulties = [0.3, 0.5, 0.4, 0.6]
            engagements = [0.8, 0.9, 0.9, 0.8]
        else:  # Low engagement recovery
            # Start low, recover
            difficulties = [0.3, 0.4, 0.5, 0.4]
            engagements = [0.2, 0.3, 0.6, 0.8]

        for i, (diff, eng) in enumerate(zip(difficulties, engagements)):
            state = {
                'text_difficulty': diff,
                'text_length': 0.5,
                'text_type': diff,
                'reading_speed': self.reading_env.current_reading_speed,
                'pause_frequency': self.reading_env.pause_frequency,
                'highlight_intensity': self.reading_env.highlight_intensity,
                'chunk_size': self.reading_env.tts_settings['chunk_size'] / 300.0,
                'user_engagement': eng,
                'user_comprehension': eng * 0.8,
                'session_progress': (i + 1) / 4,
                'action_count': i + 1,
                'recent_commands': 0.1
            }

            current_state = self.reading_env._get_state_vector()
            action = self.a2c_agent.get_recommended_action(state)
            next_state, reward, done, truncated, info = self.reading_env.step(action)

            logger.info(f"  Step {i+1}: Diff={diff:.1f}, Eng={eng:.1f}, Reward={reward:.3f}")

            await asyncio.sleep(0.5)

    async def _show_final_results(self):
        """Show final training results and statistics"""
        logger.info("\n" + "="*80)
        logger.info("FINAL A2C TRAINING RESULTS")
        logger.info("="*80)

        # Training statistics
        status = self.training_scheduler.get_training_status()
        logger.info(f"TRAINING STATISTICS:")
        logger.info(f"  Total Episodes: {status['episodes_collected']}")
        logger.info(f"  Training Steps: {status['total_training_steps']}")
        logger.info(f"  Average Reward: {status['average_reward']:.3f}")

        # Current TTS settings
        tts_settings = self.reading_env.get_current_tts_settings()
        logger.info(f"\nFINAL TTS SETTINGS:")
        for key, value in tts_settings.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.3f}")
            else:
                logger.info(f"  {key}: {value}")

        # Reward breakdown
        rewards = self.reading_env.get_reward_breakdown()
        logger.info(f"\nREWARD BREAKDOWN:")
        for component, value in rewards.items():
            logger.info(f"  {component}: {value:.3f}")

        # Data collection suggestions
        suggestions = self.training_scheduler.get_data_collection_suggestions()
        if suggestions:
            logger.info(f"\nDATA COLLECTION SUGGESTIONS:")
            for suggestion in suggestions:
                logger.info(f"  • {suggestion}")

        logger.info("\n" + "="*80)
        logger.info("A2C TESTING COMPLETE")
        logger.info("="*80)

def main():
    """Main function to run A2C monitoring"""
    print("Starting A2C Training Monitor...")
    print("This will demonstrate the A2C system working with conversation data")
    print("Check the console output for detailed feedback")
    print("-" * 60)

    monitor = A2CMonitor()
    asyncio.run(monitor.run_comprehensive_test())

if __name__ == "__main__":
    main()