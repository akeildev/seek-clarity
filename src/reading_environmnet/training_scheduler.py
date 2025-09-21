#!/usr/bin/env python3
"""
Training scheduler and data collection strategy for A2C agent
"""

import asyncio
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger("training-scheduler")

class A2CTrainingScheduler:
    """Manages A2C training data collection and periodic training"""

    def __init__(self, reading_env, a2c_agent, training_interval=300):  # 5 minutes
        self.reading_env = reading_env
        self.a2c_agent = a2c_agent
        self.training_interval = training_interval

        # Training data buffers
        self.state_buffer = []
        self.action_buffer = []
        self.reward_buffer = []
        self.episode_data = []

        # Training statistics
        self.training_stats = {
            'episodes_collected': 0,
            'total_training_steps': 0,
            'average_reward': 0.0,
            'recent_rewards': [],
            'last_training_time': 0,
            'data_collection_active': False
        }

        # Background training task
        self.training_task = None
        self.is_running = False

        # Data persistence
        self.data_dir = Path(__file__).parent / "training_data"
        self.data_dir.mkdir(exist_ok=True)

    def start_data_collection(self):
        """Start background data collection and training"""
        if self.is_running:
            logger.warning("Training scheduler already running")
            return

        self.is_running = True
        self.training_stats['data_collection_active'] = True

        # Start background training task
        self.training_task = asyncio.create_task(self._training_loop())

        logger.info("Training scheduler started")
        logger.info(f"Training interval: {self.training_interval} seconds")

    async def stop_data_collection(self):
        """Stop data collection and training"""
        self.is_running = False
        self.training_stats['data_collection_active'] = False

        if self.training_task:
            self.training_task.cancel()
            try:
                await self.training_task
            except asyncio.CancelledError:
                pass

        # Save any remaining data
        await self._save_training_data()

        logger.info("Training scheduler stopped")

    def collect_experience(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray, done: bool):
        """Collect experience for training"""
        try:
            self.state_buffer.append(state.copy())
            self.action_buffer.append(action.copy())
            self.reward_buffer.append(reward)

            # Update statistics
            self.training_stats['recent_rewards'].append(reward)
            if len(self.training_stats['recent_rewards']) > 100:
                self.training_stats['recent_rewards'] = self.training_stats['recent_rewards'][-100:]

            self.training_stats['average_reward'] = np.mean(self.training_stats['recent_rewards'])

            # If episode is done, package the episode data
            if done or len(self.state_buffer) >= 50:  # Episode complete or max length
                self._package_episode()

        except Exception as e:
            logger.error(f"Error collecting experience: {e}")

    def _package_episode(self):
        """Package collected data into an episode"""
        if len(self.state_buffer) == 0:
            return

        episode = {
            'states': self.state_buffer.copy(),
            'actions': self.action_buffer.copy(),
            'rewards': self.reward_buffer.copy(),
            'episode_length': len(self.state_buffer),
            'total_reward': sum(self.reward_buffer),
            'timestamp': time.time()
        }

        self.episode_data.append(episode)

        # Clear buffers
        self.state_buffer.clear()
        self.action_buffer.clear()
        self.reward_buffer.clear()

        self.training_stats['episodes_collected'] += 1

        logger.info(f"Episode packaged: Length={episode['episode_length']}, Reward={episode['total_reward']:.3f}")

    async def _training_loop(self):
        """Background training loop"""
        logger.info("Training loop started")

        while self.is_running:
            try:
                await asyncio.sleep(self.training_interval)

                if not self.is_running:
                    break

                await self._perform_training()

            except asyncio.CancelledError:
                logger.info("Training loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in training loop: {e}")

    async def _perform_training(self):
        """Perform A2C training on collected data"""
        if len(self.episode_data) < 2:  # Need at least 2 episodes
            logger.info(f"Not enough episodes for training: {len(self.episode_data)}/2")
            return

        try:
            logger.info("="*60)
            logger.info("STARTING A2C TRAINING SESSION")
            logger.info("="*60)

            # Prepare training data
            all_states = []
            all_actions = []
            all_rewards = []

            for episode in self.episode_data:
                all_states.extend(episode['states'])
                all_actions.extend(episode['actions'])
                all_rewards.extend(episode['rewards'])

            logger.info(f"Training with {len(all_states)} steps from {len(self.episode_data)} episodes")
            logger.info(f"Average episode reward: {np.mean([ep['total_reward'] for ep in self.episode_data]):.3f}")

            # Convert to tensors
            import torch
            state_tensors = [torch.tensor(state, dtype=torch.float32) for state in all_states]
            action_tensors = [torch.tensor(action, dtype=torch.float32) for action in all_actions]

            # Train the A2C agent
            policy_loss, baseline_loss = self.a2c_agent.train(state_tensors, action_tensors, all_rewards)

            # Update networks
            if policy_loss is not None:
                self.a2c_agent.actor_optimizer.zero_grad()
                policy_loss.backward()
                self.a2c_agent.actor_optimizer.step()
                logger.info(f"Policy loss: {policy_loss.item():.4f}")

            if baseline_loss is not None:
                self.a2c_agent.critic_optimizer.zero_grad()
                baseline_loss.backward()
                self.a2c_agent.critic_optimizer.step()
                logger.info(f"Baseline loss: {baseline_loss.item():.4f}")

            # Update statistics
            self.training_stats['total_training_steps'] += 1
            self.training_stats['last_training_time'] = time.time()

            # Save training data and clear episodes
            await self._save_training_data()
            self._clear_old_episodes()

            logger.info("✓ Training session completed")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Error during training: {e}")

    def _clear_old_episodes(self):
        """Clear old episode data to prevent memory buildup"""
        # Keep only recent episodes
        max_episodes = 10
        if len(self.episode_data) > max_episodes:
            self.episode_data = self.episode_data[-max_episodes:]
            logger.info(f"Cleared old episodes, keeping {len(self.episode_data)}")

    async def _save_training_data(self):
        """Save training data to disk"""
        try:
            # Save statistics
            stats_file = self.data_dir / "training_stats.json"
            with open(stats_file, 'w') as f:
                # Convert numpy types to regular Python types for JSON serialization
                json_stats = {}
                for key, value in self.training_stats.items():
                    if isinstance(value, np.ndarray):
                        json_stats[key] = value.tolist()
                    elif isinstance(value, (np.integer, np.floating)):
                        json_stats[key] = value.item()
                    else:
                        json_stats[key] = value

                json.dump(json_stats, f, indent=2)

            # Save recent episodes
            if self.episode_data:
                episodes_file = self.data_dir / f"episodes_{int(time.time())}.json"
                serializable_episodes = []

                for episode in self.episode_data[-5:]:  # Save only recent episodes
                    serializable_episode = {
                        'episode_length': episode['episode_length'],
                        'total_reward': episode['total_reward'],
                        'timestamp': episode['timestamp'],
                        'rewards': episode['rewards']  # Save rewards for analysis
                    }
                    serializable_episodes.append(serializable_episode)

                with open(episodes_file, 'w') as f:
                    json.dump(serializable_episodes, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving training data: {e}")

    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            **self.training_stats,
            'buffer_sizes': {
                'states': len(self.state_buffer),
                'actions': len(self.action_buffer),
                'rewards': len(self.reward_buffer),
                'episodes': len(self.episode_data)
            },
            'time_since_last_training': time.time() - self.training_stats['last_training_time'],
            'next_training_in': max(0, self.training_interval - (time.time() - self.training_stats['last_training_time']))
        }

    def should_collect_more_data(self) -> bool:
        """Determine if we need more training data"""
        status = self.get_training_status()

        # Collect more data if:
        # 1. We have very few episodes
        # 2. Recent performance is poor
        # 3. We haven't trained in a while

        needs_more = (
            status['episodes_collected'] < 10 or
            status['average_reward'] < 1.0 or
            status['time_since_last_training'] > self.training_interval * 2
        )

        return needs_more

    def get_data_collection_suggestions(self) -> List[str]:
        """Get suggestions for improving data collection based on QueryData structure"""
        suggestions = []
        status = self.get_training_status()

        if status['episodes_collected'] < 5:
            suggestions.append("Need more conversation episodes - engage in longer conversations")

        if status['average_reward'] < 0.5:
            suggestions.append("Reward signals are low - try varying conversation complexity")

        if len(self.state_buffer) < 10:
            suggestions.append("Current episode is short - continue conversation for more data")

        if status['time_since_last_training'] > self.training_interval:
            suggestions.append("Training overdue - will train automatically soon")

        # QueryData-specific suggestions
        suggestions.append("Try different text types: simple emails (0.1) to technical docs (0.9)")
        suggestions.append("Vary text difficulty by asking complex questions vs simple ones")
        suggestions.append("Use voice commands like 'faster', 'slower', 'repeat' for command rewards")
        suggestions.append("Mix engaged responses with confused ones to test comprehension adaptation")

        return suggestions

    def force_training(self):
        """Force immediate training if data is available"""
        if len(self.episode_data) > 0:
            asyncio.create_task(self._perform_training())
            logger.info("Forced training initiated")
            return True
        else:
            logger.warning("No episode data available for training")
            return False