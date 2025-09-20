# Integration Example - How to use the complete system
import asyncio
import json
from voice_agent import VoiceAgent
from settings_manager import SettingsManager, SettingType

async def main():
    """Complete example of how to integrate everything"""
    
    # 1. Initialize the voice agent
    print("Initializing Voice Agent...")
    agent = VoiceAgent(device="cpu")
    
    # 2. Initialize settings manager
    settings_manager = SettingsManager(agent)
    
    # 3. Example text content
    text_content = """
    This is a complex academic paper about machine learning and natural language processing. 
    The paper discusses various approaches to text analysis and reading comprehension. 
    It contains technical terminology and complex sentence structures that may require 
    different reading speeds and pause patterns for optimal comprehension.
    """
    
    # 4. Simulate user commands
    user_commands = ["read this", "go slower", "highlight important parts"]
    
    print("Processing text with A2C agent...")
    
    # 5. Process text and get recommendations
    result = await agent.process_text(text_content, user_commands)
    
    print("A2C Settings:", result['a2c_settings'])
    print("ElevenLabs Settings:", result['elevenlabs_settings'])
    print("State Info:", result['state_info'])
    
    # 6. Simulate MCP tools feedback
    print("\nSimulating MCP tools feedback...")
    mcp_feedback = {
        'reading_analysis': {
            'text_difficulty': 0.8,
            'suggested_speed': 0.9,  # Slower for difficult text
            'suggested_pauses': 0.6,  # More pauses for complex content
            'comprehension_score': 0.7
        },
        'user_behavior': {
            'engagement_level': 0.8,
            'confusion_indicators': ['slower', 'repeat'],
            'preferred_style': 'academic'
        }
    }
    
    # Apply MCP feedback through settings manager
    await settings_manager.apply_mcp_feedback(mcp_feedback)
    
    # 7. Get updated settings
    current_settings = settings_manager.get_current_settings()
    print("Updated settings after MCP feedback:", current_settings)
    
    # 8. Simulate more user interaction
    print("\nSimulating more user interaction...")
    more_commands = ["faster", "less highlighting"]
    
    # Process again with new commands
    result2 = await agent.process_text(text_content, more_commands)
    print("Updated A2C Settings:", result2['a2c_settings'])
    
    # 9. Get trend analysis
    print("\nTrend Analysis:")
    speed_trend = settings_manager.get_setting_trend(SettingType.READING_SPEED)
    print("Reading Speed Trend:", speed_trend)
    
    # 10. Export settings for persistence
    settings_export = settings_manager.export_settings()
    print("\nExported Settings (first 200 chars):", settings_export[:200] + "...")
    
    # 11. Show how to integrate with ElevenLabs
    print("\nElevenLabs Integration:")
    print("Current ElevenLabs settings:", agent.elevenlabs_settings)
    
    # Update ElevenLabs settings independently
    agent.update_elevenlabs_settings({
        'stability': 0.7,
        'similarity_boost': 0.8,
        'style': 0.2
    })
    print("Updated ElevenLabs settings:", agent.elevenlabs_settings)
    
    # 12. Show complete current state
    print("\nComplete Current State:")
    complete_state = agent.get_current_settings()
    print(json.dumps(complete_state, indent=2))

def demonstrate_mcp_integration():
    """Show how MCP tools would integrate"""
    print("\n" + "="*50)
    print("MCP TOOLS INTEGRATION GUIDE")
    print("="*50)
    
    print("""
    1. ELEVEN LABS INTEGRATION (Independent):
       - ElevenLabs settings are completely separate from A2C
       - You can change voice, stability, similarity_boost independently
       - These don't affect the A2C agent's reading recommendations
       
    2. MCP TOOLS FEEDBACK LOOP:
       - Your MCP tools analyze text and user behavior
       - They send feedback to settings_manager.apply_mcp_feedback()
       - Settings manager applies changes to voice_agent
       - A2C agent gets updated state and makes new recommendations
       
    3. SETTINGS CHANGE FLOW:
       MCP Tools → Settings Manager → Voice Agent → A2C Agent
       
    4. EXAMPLE MCP TOOL FEEDBACK FORMAT:
       {
           'reading_analysis': {
               'text_difficulty': 0.8,
               'suggested_speed': 0.9,
               'suggested_pauses': 0.6
           },
           'user_behavior': {
               'engagement_level': 0.8,
               'confusion_indicators': ['slower', 'repeat']
           }
       }
       
    5. TO CHANGE SETTINGS FROM MCP TOOLS:
       - Call settings_manager.apply_mcp_feedback(feedback_data)
       - Settings will be automatically applied to voice_agent
       - A2C agent will use updated settings in next recommendation
    """)

if __name__ == "__main__":
    asyncio.run(main())
    demonstrate_mcp_integration()
