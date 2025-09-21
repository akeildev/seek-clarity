# Reading A2C Agent
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

class ReadingA2C(nn.Module):
    def __init__(
        self,
        state_size=19,
        action_size=8,
        lr_actor=1e-3,
        lr_critic=1e-3,
        n=1,  # n-step
        gamma=0.99,
        device="cpu",
        voice_agent=None, # this is Akeils stuff from before
    ):
        super(ReadingA2C, self).__init__()

        self.state_size = state_size
        self.action_size = action_size
        self.n = n
        self.gamma = gamma
        self.device = device
        self.voice_agent = voice_agent
        
        # State tracking
        self.current_state = None

        hidden_layer_size = 256

        # Actor / Policy Network - outputs continuous actions
        self.actor = nn.Sequential(
            nn.Linear(state_size, hidden_layer_size),
            nn.ReLU(),
            nn.Linear(hidden_layer_size, hidden_layer_size),
            nn.ReLU(),
            nn.Linear(hidden_layer_size, action_size),
            nn.Tanh()  # Actions in [-1, 1] for continuous control
        )

        # Critic / Baseline Network
        self.critic = nn.Sequential(
            nn.Linear(state_size, hidden_layer_size),
            nn.ReLU(),
            nn.Linear(hidden_layer_size, hidden_layer_size),
            nn.ReLU(),
            nn.Linear(hidden_layer_size, 1)
        )

        # Optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr_critic)

        # Move to device
        self.actor = self.actor.to(device)
        self.critic = self.critic.to(device)

    def forward(self, state):
        return (self.actor(state), self.critic(state))

    def get_action(self, state, stochastic=True):
        """Get action from current policy"""
        action_vec = self.actor(state)
        
        if not stochastic:
            # Deterministic: return the action directly
            return action_vec, action_vec
        
        # Stochastic: add noise for exploration
        noise = torch.randn_like(action_vec) * 0.1
        action = action_vec + noise
        return action, action_vec

    def calculate_n_step_bootstrap(self, rewards_tensor, values):
        """Calculate n-step bootstrap returns"""
        t = len(rewards_tensor)
        tsteps = torch.arange(t) + self.n
        V_end = torch.zeros_like(tsteps, dtype=values[0].dtype)
        mask = (tsteps < len(values))
        V_end[mask] = (self.gamma ** self.n) * values[tsteps[mask]]

        if self.n == 1:
            G_t_vec = rewards_tensor + (self.gamma * V_end)
        else:
            gamma_vec = self.gamma ** (torch.arange(self.n))
            G_t_vec = []
            for i in range(t):
                bound = min(i + self.n - 1, t)
                G_t_vec.append(torch.sum(gamma_vec[0:bound - i] * rewards_tensor[i:bound]) + V_end[i])

        return G_t_vec

    def train(self, states, actions, rewards):
        """Train the A2C agent"""
        values = [self.critic(state) for state in states]
        G_t_vec = self.calculate_n_step_bootstrap(torch.tensor(rewards), torch.tensor(values))

        # Compute policy and baseline loss
        t = len(rewards)
        policy_loss = 0
        baseline_loss = 0
        
        for i in range(t):
            _, action_vec = self.get_action(states[i], True)
            
            # For continuous actions, use mean squared error
            action_loss = F.mse_loss(action_vec, actions[i])
            
            curr_value = values[i]
            
            # Policy loss with advantage
            advantage = G_t_vec[i] - curr_value.detach()
            policy_loss += advantage * action_loss
            
            # Baseline loss
            baseline_loss += ((G_t_vec[i] - curr_value) ** 2)
        
        policy_loss *= (-1/t)
        baseline_loss *= (1/t)

        return policy_loss, baseline_loss

    def episode_handler(self, env, max_steps, training):
        """Generate one episode"""
        curr_state, _ = env.reset()
        curr_state = torch.tensor(curr_state, dtype=torch.float32)
        
        step = 0
        terminated = False
        state_vec = [curr_state]
        action_vec = []
        reward_vec = []

        # Generate episode
        while (step <= max_steps) and not terminated:
            action, _ = self.get_action(curr_state, training)
            curr_state, reward, terminated, _, _ = env.step(action.detach().numpy())
            curr_state = torch.tensor(curr_state, dtype=torch.float32)
            
            if not terminated:
                state_vec.append(curr_state)
            action_vec.append(action)
            reward_vec.append(reward)
            step += 1

        return state_vec, action_vec, reward_vec

    def run(self, env, max_steps, num_episodes, train):
        """Run training episodes"""
        for curr_ep in range(num_episodes):
            # Generate episode
            state_vec, action_vec, reward_vec = self.episode_handler(env, max_steps, True)

            # Train
            policy_loss, baseline_loss = train(state_vec, action_vec, reward_vec)

            # Update networks
            if policy_loss is not None:
                self.actor_optimizer.zero_grad()
                policy_loss.backward()
                self.actor_optimizer.step()

            if baseline_loss is not None:
                self.critic_optimizer.zero_grad()
                baseline_loss.backward()
                self.critic_optimizer.step()
    
    def collect_state_from_data(self, state_data: dict):
        """Collect state from provided data"""
        self.current_state = state_data
        return state_data
    
    def get_recommended_action(self, state_data: dict):
        """Get recommended action based on current state"""
        if not self.current_state:
            self.current_state = state_data
        
        # Convert state to vector
        state_vector = np.array([
            state_data.get('text_difficulty', 0.5),
            state_data.get('text_length', 0.5),
            state_data.get('text_type', 0.4),
            state_data.get('reading_speed', 1.0),
            state_data.get('pause_frequency', 0.3),
            state_data.get('highlight_intensity', 0.5),
            state_data.get('chunk_size', 0.5),
            state_data.get('user_engagement', 0.5),
            state_data.get('user_comprehension', 0.5),
            state_data.get('session_progress', 0.0),
            state_data.get('action_count', 0),
            state_data.get('recent_commands', 0.0)
        ])
        
        # Pad to expected state size if needed
        if len(state_vector) < self.state_size:
            padding = np.zeros(self.state_size - len(state_vector))
            state_vector = np.concatenate([state_vector, padding])
        
        # Convert to tensor
        state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
        
        # Get action from policy
        with torch.no_grad():
            action, _ = self.get_action(state_tensor, stochastic=False)
        
        return action.squeeze(0).numpy()
    
    def get_recommended_settings(self, state_data: dict) -> dict:
        """Get recommended settings based on current state and text"""
        action = self.get_recommended_action(state_data)
        
        # Map action to settings
        settings = {
            'reading_speed': max(0.5, min(1.5, 1.0 + action[0] * 0.5)),
            'pause_frequency': max(0.1, min(0.8, 0.3 + action[1] * 0.5)),
            'highlight_intensity': max(0.0, min(1.0, 0.5 + action[2] * 0.5)),
            'chunk_size': max(0.1, min(1.0, 0.5 + action[3] * 0.5)),
        }
        
        return settings