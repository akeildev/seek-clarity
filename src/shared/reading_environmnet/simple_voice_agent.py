# Simple Voice Command + Text Analysis Agent for Hackathon
"""
import asyncio
from reading_agent import ReadingAgent, QueryData


class SimpleVoiceAgent:
    """Simple reading agent that uses voice commands + basic text analysis"""
    
    def __init__(self):
        self.agent = ReadingAgent()
        self.commands = []
        self.progress = 0.0
        self.current_settings = {
            'reading_speed': 1.0,
            'pause_frequency': 0.3,
            'highlight_intensity': 0.5,
            'chunk_size': 0.5
        }
        
    def analyze_text_simple(self, text_content):
        """Basic text analysis without LLM - perfect for hackathon"""
        if not text_content:
            return {
                'text_difficulty': 0.5,
                'text_type': 0.4,
                'text_length': 0.5
            }
            
        words = text_content.split()
        word_count = len(words)
        
        # Simple difficulty based on word length
        avg_word_length = sum(len(word) for word in words) / word_count
        text_difficulty = min(1.0, avg_word_length / 8.0)
        
        # Simple type detection
        text_lower = text_content.lower()
        if any(word in text_lower for word in ['@', 'dear', 'sincerely', 'regards']):
            text_type = 0.1  # Email
        elif any(word in text_lower for word in ['chapter', 'section', 'figure', 'table', 'reference', 'abstract']):
            text_type = 0.8  # Academic
        elif any(word in text_lower for word in ['breaking', 'reported', 'according to', 'sources']):
            text_type = 0.6  # News
        else:
            text_type = 0.4  # General
        
        # Simple length normalization
        text_length = min(1.0, word_count / 1000.0)
        
        return {
            'text_difficulty': text_difficulty,
            'text_type': text_type,
            'text_length': text_length
        }
    
    def add_voice_command(self, command):
        """Add a voice command and update engagement/comprehension scores"""
        self.commands.append(command)
        
        # Keep only last 10 commands
        if len(self.commands) > 10:
            self.commands = self.commands[-10:]
    
    def calculate_engagement(self):
        """Calculate engagement from voice commands"""
        if not self.commands:
            return 0.5
            
        positive_commands = ['faster', 'slower', 'continue', 'more', 'yes', 'good', 'great', 'keep going']
        negative_commands = ['stop', 'pause', 'skip', 'enough', 'quit', 'no', 'bad', 'stop reading']
        
        positive_count = sum(1 for cmd in self.commands if any(pos in cmd.lower() for pos in positive_commands))
        negative_count = sum(1 for cmd in self.commands if any(neg in cmd.lower() for neg in negative_commands))
        
        if positive_count + negative_count == 0:
            return 0.5
        
        return positive_count / (positive_count + negative_count)
    
    def calculate_comprehension(self):
        """Calculate comprehension from voice commands"""
        if not self.commands:
            return 0.5
            
        confusion_commands = ['explain', 'what', 'why', 'how', 'repeat', 'clarify', 'confused', 'huh', 'again']
        confidence_commands = ['got it', 'understand', 'clear', 'makes sense', 'continue', 'okay', 'yes', 'perfect']
        
        confusion_count = sum(1 for cmd in self.commands if any(conf in cmd.lower() for conf in confusion_commands))
        confidence_count = sum(1 for cmd in self.commands if any(conf in cmd.lower() for conf in confidence_commands))
        
        if confusion_count + confidence_count == 0:
            return 0.5
        
        return confidence_count / (confusion_count + confidence_count)
    
    def update_progress(self, progress):
        """Update reading progress (0.0 to 1.0)"""
        self.progress = max(0.0, min(1.0, progress))
    
    async def process_text_and_command(self, text_content, voice_command=None):
        """Process text and voice command to get recommendations"""
        
        # Add voice command if provided
        if voice_command:
            self.add_voice_command(voice_command)
        
        # Analyze text
        text_analysis = self.analyze_text_simple(text_content)
        
        # Calculate user behavior from commands
        engagement = self.calculate_engagement()
        comprehension = self.calculate_comprehension()
        
        # Create query data
        query_data = QueryData(
            # Text Analysis (from simple heuristics)
            text_difficulty=text_analysis['text_difficulty'],
            text_type=text_analysis['text_type'],
            text_length=text_analysis['text_length'],
            
            # User Behavior (from voice commands)
            user_engagement=engagement,
            user_comprehension=comprehension,
            recent_commands=self.commands[-5:],  # Last 5 commands
            text_progress=self.progress,
            
            # Current Settings
            current_reading_speed=self.current_settings['reading_speed'],
            current_pause_frequency=self.current_settings['pause_frequency'],
            current_highlight_intensity=self.current_settings['highlight_intensity'],
            current_chunk_size=self.current_settings['chunk_size']
        )
        
        # Get recommendations
        result = await self.agent.process_query(query_data)
        
        # Update current settings with recommendations
        self.current_settings.update(result['recommendations'])
        
        return result
    
    def get_current_settings(self):
        """Get current reading settings"""
        return self.current_settings.copy()
    
    def reset_session(self):
        """Reset for new reading session"""
        self.commands = []
        self.progress = 0.0
        self.current_settings = {
            'reading_speed': 1.0,
            'pause_frequency': 0.3,
            'highlight_intensity': 0.5,
            'chunk_size': 0.5
        }

# Demo function
async def demo_voice_agent():
    """Demo the simple voice agent"""
    print("🎤 Simple Voice Agent Demo")
    print("=" * 40)
    
    agent = SimpleVoiceAgent()
    
    # Sample text
    sample_text = """
    Machine learning algorithms utilize complex mathematical frameworks to process 
    large datasets and identify patterns. These algorithms require significant 
    computational resources and careful parameter tuning to achieve optimal performance.
    """
    
    print(f"📄 Text: {sample_text.strip()}")
    print()
    
    # Simulate voice commands
    commands = [
        "read this text",
        "go faster", 
        "explain that part",
        "repeat the last sentence",
        "continue reading",
        "slow down a bit",
        "that makes sense",
        "keep going"
    ]
    
    for i, command in enumerate(commands):
        print(f"🗣️  User: {command}")
        
        # Process command
        result = await agent.process_text_and_command(sample_text, command)
        
        # Show recommendations
        rec = result['recommendations']
        print(f"🤖 Agent: Speed {rec['recommended_reading_speed']:.2f}, "
              f"Pauses {rec['recommended_pause_frequency']:.2f}, "
              f"Highlight {rec['recommended_highlight_intensity']:.2f}")
        
        # Show engagement/comprehension
        print(f"📊 Engagement: {result['state_analysis']['user_engagement']:.2f}, "
              f"Comprehension: {result['state_analysis']['user_comprehension']:.2f}")
        print()
    
    print("✅ Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo_voice_agent())
"""