# Reading Environment for A2C Agent
import asyncio
import numpy as np
import torch
from typing import List, Dict, Any

class ReadingEnvironment:
    def __init__(self, state_size=20, action_size=8, voice_agent=None):
        self.state_size = state_size
        self.action_size = action_size
        self.voice_agent = voice_agent
        
        # State tracking
        self.current_state = None
        
        # Reading state components
        self.current_text_difficulty = 0.5
        self.current_reading_speed = 1.0
        self.user_comprehension = 0.5
        self.user_engagement = 0.5
        self.pause_frequency = 0.3
        self.highlight_intensity = 0.5
        
        # User behavior tracking
        self.reading_sessions = []
        self.user_feedback_history = []
        self.current_text = ""
        
        # Additional attributes for reward calculation
        self.text_progress = 0.0
        self.session_start_time = None
        
    def reset(self):
        """Reset environment to initial state"""
        # Initialize with default reading state
        state = self._get_state_vector()
        return state, {}
    
    def step(self, action):
        """Execute action and return new state, reward, done, info"""
        # Convert action to reading parameters
        self._apply_action(action)
        
        # Simulate user behavior (in real app, this comes from actual user)
        reward = self._calculate_reward()
        
        # Check if reading session is complete
        done = self._is_session_complete()
        
        # Get new state
        next_state = self._get_state_vector()
        
        return next_state, reward, done, False, {}
    
    def _get_state_vector(self):
        """Convert current state to vector for neural network"""
        return np.array([
            self.current_text_difficulty,
            self.current_reading_speed,
            self.user_comprehension,
            self.user_engagement,
            self.pause_frequency,
            self.highlight_intensity,
            # Add more state components as needed
            len(self.reading_sessions),
            np.mean([f.get('score', 0.5) for f in self.user_feedback_history]) if self.user_feedback_history else 0.5,
            # ... more state features
        ] + [0.0] * (self.state_size - 9))  # Pad to state_size
    
    def _apply_action(self, action):
        """Apply action to reading parameters"""
        # Action is a vector of 8 values (action_size=8)
        # Map to reading parameters
        
        # Reading speed adjustment
        self.current_reading_speed = max(0.5, min(1.5, 1.0 + action[0] * 0.5))
        
        # Pause frequency adjustment
        self.pause_frequency = max(0.1, min(0.8, 0.3 + action[1] * 0.5))
        
        # Highlight intensity adjustment
        self.highlight_intensity = max(0.0, min(1.0, 0.5 + action[2] * 0.5))
        
        # Add more action mappings as needed
    
    def _calculate_reward(self):
        """Calculate comprehensive reward based on reading assistance effectiveness"""
        reward = 0.0
        
        # 1. READING SPEED OPTIMIZATION (0-1.0 points)
        reward += self._calculate_speed_reward()
        
        # 2. PAUSE FREQUENCY OPTIMIZATION (0-0.8 points)
        reward += self._calculate_pause_reward()
        
        # 3. HIGHLIGHT INTENSITY OPTIMIZATION (0-0.6 points)
        reward += self._calculate_highlight_reward()
        
        # 4. USER ENGAGEMENT REWARD (0-1.2 points)
        reward += self._calculate_engagement_reward()
        
        # 5. COMPREHENSION REWARD (0-1.5 points)
        reward += self._calculate_comprehension_reward()
        
        # 6. TEXT DIFFICULTY ADAPTATION (0-0.8 points)
        reward += self._calculate_difficulty_adaptation_reward()
        
        # 7. SESSION CONTINUITY REWARD (0-0.5 points)
        reward += self._calculate_continuity_reward()
        
        # 8. USER PREFERENCE ALIGNMENT (0-0.6 points)
        reward += self._calculate_preference_reward()
        
        # 9. EFFICIENCY REWARD (0-0.4 points)
        reward += self._calculate_efficiency_reward()
        
        # 10. PENALTY FOR EXTREME SETTINGS (-0.3 to 0 points)
        reward += self._calculate_extreme_penalty()
        
        # Normalize to reasonable range (-1.0 to 5.0)
        return max(-1.0, min(5.0, reward))
    
    def _calculate_speed_reward(self):
        """Reward for optimal reading speed based on text difficulty and user profile"""
        # Base speed reward
        speed = self.current_reading_speed
        
        # Optimal speed depends on text difficulty
        if hasattr(self, 'current_text_difficulty'):
            difficulty = self.current_text_difficulty
            # More difficult text should be read slower
            optimal_speed = 1.2 - (difficulty * 0.4)  # 0.8 to 1.2 range
        else:
            optimal_speed = 1.0
        
        # Calculate distance from optimal
        speed_diff = abs(speed - optimal_speed)
        
        # Reward decreases as distance from optimal increases
        if speed_diff <= 0.1:
            return 1.0  # Perfect speed
        elif speed_diff <= 0.2:
            return 0.8  # Good speed
        elif speed_diff <= 0.3:
            return 0.5  # Acceptable speed
        else:
            return max(0.0, 0.5 - speed_diff)  # Decreasing reward
    
    def _calculate_pause_reward(self):
        """Reward for appropriate pause frequency"""
        pause_freq = self.pause_frequency
        
        # Optimal pause frequency depends on text complexity and user comprehension
        if hasattr(self, 'current_text_difficulty') and hasattr(self, 'user_comprehension'):
            difficulty = self.current_text_difficulty
            comprehension = self.user_comprehension
            
            # More difficult text and lower comprehension need more pauses
            optimal_pause = 0.2 + (difficulty * 0.3) + ((1 - comprehension) * 0.2)
            optimal_pause = min(0.7, optimal_pause)  # Cap at 0.7
        else:
            optimal_pause = 0.3
        
        # Calculate reward based on distance from optimal
        pause_diff = abs(pause_freq - optimal_pause)
        
        if pause_diff <= 0.1:
            return 0.8
        elif pause_diff <= 0.2:
            return 0.6
        elif pause_diff <= 0.3:
            return 0.3
        else:
            return max(0.0, 0.3 - pause_diff)
    
    def _calculate_highlight_reward(self):
        """Reward for appropriate highlight intensity"""
        highlight = self.highlight_intensity
        
        # Optimal highlighting depends on text type and user engagement
        if hasattr(self, 'current_text_difficulty') and hasattr(self, 'user_engagement'):
            difficulty = self.current_text_difficulty
            engagement = self.user_engagement
            
            # More difficult text and lower engagement need more highlighting
            optimal_highlight = 0.3 + (difficulty * 0.4) + ((1 - engagement) * 0.2)
            optimal_highlight = min(0.9, optimal_highlight)  # Cap at 0.9
        else:
            optimal_highlight = 0.5
        
        # Calculate reward
        highlight_diff = abs(highlight - optimal_highlight)
        
        if highlight_diff <= 0.15:
            return 0.6
        elif highlight_diff <= 0.25:
            return 0.4
        elif highlight_diff <= 0.35:
            return 0.2
        else:
            return max(0.0, 0.2 - highlight_diff)
    
    def _calculate_engagement_reward(self):
        """Reward for maintaining user engagement"""
        engagement = self.user_engagement
        
        # Direct engagement reward
        if engagement >= 0.9:
            return 1.2
        elif engagement >= 0.8:
            return 1.0
        elif engagement >= 0.7:
            return 0.8
        elif engagement >= 0.6:
            return 0.5
        elif engagement >= 0.4:
            return 0.2
        else:
            return 0.0
    
    def _calculate_comprehension_reward(self):
        """Reward for maintaining comprehension"""
        comprehension = self.user_comprehension
        
        # Comprehension is critical - higher weight
        if comprehension >= 0.9:
            return 1.5
        elif comprehension >= 0.8:
            return 1.2
        elif comprehension >= 0.7:
            return 1.0
        elif comprehension >= 0.6:
            return 0.7
        elif comprehension >= 0.5:
            return 0.4
        elif comprehension >= 0.3:
            return 0.1
        else:
            return -0.5  # Penalty for very low comprehension
    
    def _calculate_difficulty_adaptation_reward(self):
        """Reward for adapting to text difficulty"""
        if not hasattr(self, 'current_text_difficulty'):
            return 0.0
        
        difficulty = self.current_text_difficulty
        speed = self.current_reading_speed
        pause_freq = self.pause_frequency
        
        # Check if settings adapt to difficulty
        adaptation_score = 0.0
        
        # Speed should decrease with difficulty
        if difficulty > 0.7 and speed < 1.0:
            adaptation_score += 0.3
        elif difficulty < 0.3 and speed > 1.0:
            adaptation_score += 0.3
        
        # Pause frequency should increase with difficulty
        if difficulty > 0.7 and pause_freq > 0.4:
            adaptation_score += 0.3
        elif difficulty < 0.3 and pause_freq < 0.4:
            adaptation_score += 0.3
        
        # Highlight intensity should increase with difficulty
        if hasattr(self, 'current_highlight_intensity'):
            highlight = self.current_highlight_intensity
            if difficulty > 0.7 and highlight > 0.6:
                adaptation_score += 0.2
            elif difficulty < 0.3 and highlight < 0.6:
                adaptation_score += 0.2
        
        return min(0.8, adaptation_score)
    
    def _calculate_continuity_reward(self):
        """Reward for maintaining reading session continuity"""
        if not self.reading_sessions:
            return 0.0
        
        # Reward for longer sessions (up to a point)
        session_length = len(self.reading_sessions)
        
        if session_length >= 20:  # Good session length
            return 0.5
        elif session_length >= 10:
            return 0.3
        elif session_length >= 5:
            return 0.1
        else:
            return 0.0
    
    def _calculate_preference_reward(self):
        """Reward for aligning with user preferences"""
        if not self.user_feedback_history:
            return 0.0
        
        # Analyze recent feedback for preferences
        recent_feedback = self.user_feedback_history[-5:]  # Last 5 feedback items
        
        preference_score = 0.0
        for feedback in recent_feedback:
            if 'preferred_speed' in feedback:
                speed_diff = abs(self.current_reading_speed - feedback['preferred_speed'])
                if speed_diff <= 0.1:
                    preference_score += 0.2
            
            if 'preferred_pauses' in feedback:
                pause_diff = abs(self.pause_frequency - feedback['preferred_pauses'])
                if pause_diff <= 0.1:
                    preference_score += 0.2
            
            if 'preferred_highlighting' in feedback:
                highlight_diff = abs(self.highlight_intensity - feedback['preferred_highlighting'])
                if highlight_diff <= 0.1:
                    preference_score += 0.2
        
        return min(0.6, preference_score)
    
    def _calculate_efficiency_reward(self):
        """Reward for efficient reading (good progress with good comprehension)"""
        if not hasattr(self, 'text_progress'):
            return 0.0
        
        progress = getattr(self, 'text_progress', 0.0)
        comprehension = self.user_comprehension
        
        # Efficiency = progress * comprehension
        efficiency = progress * comprehension
        
        if efficiency >= 0.8:
            return 0.4
        elif efficiency >= 0.6:
            return 0.3
        elif efficiency >= 0.4:
            return 0.2
        elif efficiency >= 0.2:
            return 0.1
        else:
            return 0.0
    
    def _calculate_extreme_penalty(self):
        """Penalty for extreme settings that might be uncomfortable"""
        penalty = 0.0
        
        # Penalty for very slow or very fast reading
        if self.current_reading_speed < 0.6 or self.current_reading_speed > 1.4:
            penalty -= 0.1
        
        # Penalty for too many or too few pauses
        if self.pause_frequency < 0.05 or self.pause_frequency > 0.9:
            penalty -= 0.1
        
        # Penalty for extreme highlighting
        if self.highlight_intensity < 0.05 or self.highlight_intensity > 0.95:
            penalty -= 0.1
        
        return penalty
    
    def _is_session_complete(self):
        """Check if reading session is complete"""
        # Complete after some number of steps or user stops
        return len(self.reading_sessions) > 50
    
    def update_user_feedback(self, feedback: Dict[str, Any]):
        """Update environment with real user feedback"""
        self.user_feedback_history.append(feedback)
        
        # Update user state based on feedback
        if 'comprehension' in feedback:
            self.user_comprehension = feedback['comprehension']
        if 'engagement' in feedback:
            self.user_engagement = feedback['engagement']
    
    def set_text_content(self, text_content: str):
        """Set text content for state collection"""
        self.current_text = text_content
    
    def collect_state_from_data(self, state_data: Dict[str, Any]):
        """Collect state from provided data"""
        self.current_state = state_data
        return state_data
    
    def update_text_progress(self, progress: float):
        """Update text reading progress (0.0 to 1.0)"""
        self.text_progress = max(0.0, min(1.0, progress))
    
    def start_session(self):
        """Start a new reading session"""
        import time
        self.session_start_time = time.time()
        self.reading_sessions.append({
            'start_time': self.session_start_time,
            'text_difficulty': getattr(self, 'current_text_difficulty', 0.5),
            'initial_settings': {
                'reading_speed': self.current_reading_speed,
                'pause_frequency': self.pause_frequency,
                'highlight_intensity': self.highlight_intensity
            }
        })
    
    def end_session(self):
        """End current reading session"""
        if self.session_start_time:
            import time
            session_duration = time.time() - self.session_start_time
            if self.reading_sessions:
                self.reading_sessions[-1]['duration'] = session_duration
                self.reading_sessions[-1]['final_settings'] = {
                    'reading_speed': self.current_reading_speed,
                    'pause_frequency': self.pause_frequency,
                    'highlight_intensity': self.highlight_intensity
                }
            self.session_start_time = None
    
    def get_reward_breakdown(self):
        """Get detailed breakdown of reward components for debugging"""
        return {
            'speed_reward': self._calculate_speed_reward(),
            'pause_reward': self._calculate_pause_reward(),
            'highlight_reward': self._calculate_highlight_reward(),
            'engagement_reward': self._calculate_engagement_reward(),
            'comprehension_reward': self._calculate_comprehension_reward(),
            'difficulty_adaptation_reward': self._calculate_difficulty_adaptation_reward(),
            'continuity_reward': self._calculate_continuity_reward(),
            'preference_reward': self._calculate_preference_reward(),
            'efficiency_reward': self._calculate_efficiency_reward(),
            'extreme_penalty': self._calculate_extreme_penalty(),
            'total_reward': self._calculate_reward()
        }