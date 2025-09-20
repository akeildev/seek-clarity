# Settings Manager for MCP Tools Feedback Loop
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SettingType(Enum):
    READING_SPEED = "reading_speed"
    PAUSE_FREQUENCY = "pause_frequency"
    HIGHLIGHT_INTENSITY = "highlight_intensity"
    CHUNK_SIZE = "chunk_size"
    VOICE_SETTINGS = "voice_settings"

@dataclass
class SettingChange:
    setting_type: SettingType
    old_value: Any
    new_value: Any
    timestamp: float
    source: str  # 'a2c', 'mcp_feedback', 'user_override'
    confidence: float = 1.0

class SettingsManager:
    """Manages settings changes and feedback loop integration"""
    
    def __init__(self, voice_agent=None):
        self.voice_agent = voice_agent
        self.setting_history: List[SettingChange] = []
        self.current_settings = self._get_default_settings()
        self.feedback_queue = asyncio.Queue()
        self.is_processing_feedback = False
        
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'reading_speed': 1.0,
            'pause_frequency': 0.3,
            'highlight_intensity': 0.5,
            'chunk_size': 0.5,
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.5,
                'style': 0.0,
                'use_speaker_boost': True
            }
        }
    
    async def apply_mcp_feedback(self, feedback_data: Dict[str, Any]):
        """Apply settings changes from MCP tools feedback"""
        await self.feedback_queue.put({
            'type': 'mcp_feedback',
            'data': feedback_data,
            'timestamp': time.time()
        })
        
        if not self.is_processing_feedback:
            asyncio.create_task(self._process_feedback_queue())
    
    async def apply_a2c_recommendations(self, recommendations: Dict[str, Any]):
        """Apply settings changes from A2C agent"""
        await self.feedback_queue.put({
            'type': 'a2c_recommendation',
            'data': recommendations,
            'timestamp': time.time()
        })
        
        if not self.is_processing_feedback:
            asyncio.create_task(self._process_feedback_queue())
    
    async def _process_feedback_queue(self):
        """Process feedback queue asynchronously"""
        self.is_processing_feedback = True
        
        try:
            while not self.feedback_queue.empty():
                feedback = await self.feedback_queue.get()
                await self._handle_feedback(feedback)
        finally:
            self.is_processing_feedback = False
    
    async def _handle_feedback(self, feedback: Dict[str, Any]):
        """Handle individual feedback item"""
        feedback_type = feedback['type']
        data = feedback['data']
        
        if feedback_type == 'mcp_feedback':
            await self._handle_mcp_feedback(data)
        elif feedback_type == 'a2c_recommendation':
            await self._handle_a2c_recommendation(data)
    
    async def _handle_mcp_feedback(self, feedback_data: Dict[str, Any]):
        """Handle MCP tools feedback"""
        # Parse feedback from MCP tools
        settings_changes = self._parse_mcp_feedback(feedback_data)
        
        # Apply changes
        for setting_type, new_value in settings_changes.items():
            await self._apply_setting_change(
                setting_type, 
                new_value, 
                'mcp_feedback',
                confidence=0.8  # MCP feedback has high confidence
            )
    
    async def _handle_a2c_recommendation(self, recommendations: Dict[str, Any]):
        """Handle A2C agent recommendations"""
        # Apply A2C recommendations
        for setting_name, new_value in recommendations.items():
            if setting_name in ['reading_speed', 'pause_frequency', 'highlight_intensity', 'chunk_size']:
                setting_type = SettingType(setting_name)
                await self._apply_setting_change(
                    setting_type,
                    new_value,
                    'a2c',
                    confidence=0.9  # A2C recommendations have high confidence
                )
    
    def _parse_mcp_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MCP tools feedback into settings changes"""
        settings_changes = {}
        
        # This would parse the actual feedback from your MCP tools
        # For now, return empty dict - you'll implement this based on your MCP tool output
        
        # Example parsing (you'll customize this):
        if 'reading_analysis' in feedback_data:
            analysis = feedback_data['reading_analysis']
            
            if 'suggested_speed' in analysis:
                settings_changes['reading_speed'] = analysis['suggested_speed']
            
            if 'suggested_pauses' in analysis:
                settings_changes['pause_frequency'] = analysis['suggested_pauses']
        
        return settings_changes
    
    async def _apply_setting_change(self, setting_type: SettingType, new_value: Any, 
                                  source: str, confidence: float = 1.0):
        """Apply a setting change and log it"""
        old_value = self.current_settings.get(setting_type.value)
        
        # Apply the change
        self.current_settings[setting_type.value] = new_value
        
        # Log the change
        change = SettingChange(
            setting_type=setting_type,
            old_value=old_value,
            new_value=new_value,
            timestamp=time.time(),
            source=source,
            confidence=confidence
        )
        self.setting_history.append(change)
        
        # Apply to voice agent if available
        if self.voice_agent:
            await self._apply_to_voice_agent(setting_type, new_value)
    
    async def _apply_to_voice_agent(self, setting_type: SettingType, new_value: Any):
        """Apply setting change to voice agent"""
        if not self.voice_agent:
            return
        
        if setting_type == SettingType.READING_SPEED:
            self.voice_agent.current_reading_speed = new_value
        elif setting_type == SettingType.PAUSE_FREQUENCY:
            self.voice_agent.current_pause_frequency = new_value
        elif setting_type == SettingType.HIGHLIGHT_INTENSITY:
            self.voice_agent.current_highlight_intensity = new_value
        elif setting_type == SettingType.CHUNK_SIZE:
            self.voice_agent.current_chunk_size = new_value
        elif setting_type == SettingType.VOICE_SETTINGS:
            self.voice_agent.update_elevenlabs_settings(new_value)
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return self.current_settings.copy()
    
    def get_setting_history(self, setting_type: Optional[SettingType] = None) -> List[SettingChange]:
        """Get setting change history"""
        if setting_type:
            return [change for change in self.setting_history if change.setting_type == setting_type]
        return self.setting_history.copy()
    
    def get_recent_changes(self, minutes: int = 10) -> List[SettingChange]:
        """Get recent setting changes"""
        cutoff_time = time.time() - (minutes * 60)
        return [change for change in self.setting_history if change.timestamp > cutoff_time]
    
    def get_setting_trend(self, setting_type: SettingType, window_minutes: int = 30) -> Dict[str, Any]:
        """Get trend analysis for a specific setting"""
        cutoff_time = time.time() - (window_minutes * 60)
        recent_changes = [
            change for change in self.setting_history 
            if change.setting_type == setting_type and change.timestamp > cutoff_time
        ]
        
        if not recent_changes:
            return {'trend': 'stable', 'changes': 0, 'avg_value': self.current_settings[setting_type.value]}
        
        # Calculate trend
        values = [change.new_value for change in recent_changes]
        avg_value = sum(values) / len(values)
        
        # Simple trend calculation
        if len(values) >= 2:
            if values[-1] > values[0]:
                trend = 'increasing'
            elif values[-1] < values[0]:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'changes': len(recent_changes),
            'avg_value': avg_value,
            'current_value': self.current_settings[setting_type.value],
            'recent_changes': recent_changes[-5:]  # Last 5 changes
        }
    
    def export_settings(self) -> str:
        """Export current settings as JSON"""
        return json.dumps({
            'current_settings': self.current_settings,
            'setting_history': [
                {
                    'setting_type': change.setting_type.value,
                    'old_value': change.old_value,
                    'new_value': change.new_value,
                    'timestamp': change.timestamp,
                    'source': change.source,
                    'confidence': change.confidence
                }
                for change in self.setting_history
            ]
        }, indent=2)
    
    def import_settings(self, settings_json: str):
        """Import settings from JSON"""
        data = json.loads(settings_json)
        self.current_settings = data['current_settings']
        
        # Reconstruct setting history
        self.setting_history = []
        for change_data in data['setting_history']:
            change = SettingChange(
                setting_type=SettingType(change_data['setting_type']),
                old_value=change_data['old_value'],
                new_value=change_data['new_value'],
                timestamp=change_data['timestamp'],
                source=change_data['source'],
                confidence=change_data['confidence']
            )
            self.setting_history.append(change)

# Example usage
async def main():
    """Example of how to use the settings manager"""
    manager = SettingsManager()
    
    # Simulate MCP feedback
    mcp_feedback = {
        'reading_analysis': {
            'suggested_speed': 1.2,
            'suggested_pauses': 0.4
        }
    }
    
    await manager.apply_mcp_feedback(mcp_feedback)
    
    # Simulate A2C recommendations
    a2c_recommendations = {
        'reading_speed': 1.1,
        'highlight_intensity': 0.7
    }
    
    await manager.apply_a2c_recommendations(a2c_recommendations)
    
    # Get current settings
    print("Current settings:", manager.get_current_settings())
    
    # Get trend analysis
    trend = manager.get_setting_trend(SettingType.READING_SPEED)
    print("Reading speed trend:", trend)

if __name__ == "__main__":
    asyncio.run(main())
