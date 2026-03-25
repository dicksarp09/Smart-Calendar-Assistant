"""
Agent Memory Layer
Multi-layer memory system for the AI Calendar Agent
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.db import database


class AgentMemory:
    """Agent memory with multiple layers"""
    
    # Short-term memory (in-memory session)
    _session_memory: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def set_short_term(cls, user_id: str, key: str, value: Any) -> None:
        """Set short-term (session) memory"""
        if user_id not in cls._session_memory:
            cls._session_memory[user_id] = {}
        cls._session_memory[user_id][key] = value
    
    @classmethod
    def get_short_term(cls, user_id: str, key: Optional[str] = None) -> Any:
        """Get short-term memory"""
        if user_id not in cls._session_memory:
            return None if key else {}
        
        if key:
            return cls._session_memory[user_id].get(key)
        return cls._session_memory[user_id]
    
    @classmethod
    def clear_short_term(cls, user_id: str) -> None:
        """Clear short-term memory for user"""
        if user_id in cls._session_memory:
            del cls._session_memory[user_id]
    
    @classmethod
    def add_conversation(cls, user_id: str, role: str, content: str) -> None:
        """Add to conversation history (short-term)"""
        if user_id not in cls._session_memory:
            cls._session_memory[user_id] = {"conversation": []}
        
        if "conversation" not in cls._session_memory[user_id]:
            cls._session_memory[user_id]["conversation"] = []
        
        cls._session_memory[user_id]["conversation"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20 messages
        if len(cls._session_memory[user_id]["conversation"]) > 20:
            cls._session_memory[user_id]["conversation"] = \
                cls._session_memory[user_id]["conversation"][-20:]
    
    @classmethod
    def get_conversation(cls, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history"""
        conv = cls.get_short_term(user_id, "conversation")
        return conv if conv else []
    
    @classmethod
    def set_pending_action(cls, user_id: str, action: str, data: Dict[str, Any]) -> None:
        """Set pending action (short-term)"""
        cls.set_short_term(user_id, "pending_action", {
            "action": action,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @classmethod
    def get_pending_action(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get pending action"""
        return cls.get_short_term(user_id, "pending_action")
    
    @classmethod
    def clear_pending_action(cls, user_id: str) -> None:
        """Clear pending action"""
        if user_id in cls._session_memory:
            cls._session_memory[user_id].pop("pending_action", None)
    
    # Medium-term memory (SQLite user_memory table)
    @classmethod
    def set_preference(cls, user_id: str, key: str, value: str) -> None:
        """Set user preference (medium-term)"""
        database.set_user_memory(user_id, key, value)
    
    @classmethod
    def get_preference(cls, user_id: str, key: str) -> Optional[str]:
        """Get user preference"""
        memory = database.get_user_memory(user_id, key)
        return memory.get("value") if memory else None
    
    @classmethod
    def get_all_preferences(cls, user_id: str) -> Dict[str, str]:
        """Get all user preferences"""
        return database.get_user_memory(user_id)
    
    @classmethod
    def update_meeting_preferences(cls, user_id: str, preferred_times: List[str] = None,
                                   default_duration: int = 60) -> None:
        """Update meeting preferences"""
        if preferred_times:
            database.set_user_memory(user_id, "preferred_meeting_times", 
                                    ",".join(preferred_times))
        database.set_user_memory(user_id, "default_meeting_duration", str(default_duration))
    
    @classmethod
    def get_meeting_preferences(cls, user_id: str) -> Dict[str, Any]:
        """Get meeting preferences"""
        prefs = database.get_user_memory(user_id)
        return {
            "preferred_times": prefs.get("preferred_meeting_times", "").split(","),
            "default_duration": int(prefs.get("default_meeting_duration", "60"))
        }
    
    # Long-term memory (SQLite agent_behavior table)
    @classmethod
    def learn_pattern(cls, user_id: str, pattern_type: str, 
                     pattern_data: Dict[str, Any], confidence: float = 0.5) -> None:
        """Learn a behavior pattern (long-term)"""
        import json
        database.update_behavior_pattern(
            user_id=user_id,
            pattern_type=pattern_type,
            pattern_data=json.dumps(pattern_data),
            confidence=confidence
        )
    
    @classmethod
    def get_patterns(cls, user_id: str) -> List[Dict[str, Any]]:
        """Get behavior patterns"""
        return database.get_behavior_patterns(user_id)
    
    @classmethod
    def learn_scheduling_pattern(cls, user_id: str, event_summary: str, 
                                hour: int, day_of_week: int) -> None:
        """Learn scheduling pattern"""
        import json
        
        # Get existing patterns
        patterns = cls.get_patterns(user_id)
        scheduling_patterns = [p for p in patterns if p["pattern_type"] == "scheduling_hours"]
        
        if scheduling_patterns:
            # Update existing
            existing = scheduling_patterns[0]
            import json
            data = json.loads(existing["pattern_data"])
            if hour not in data.get("hours", []):
                data["hours"] = data.get("hours", []) + [hour]
            if day_of_week not in data.get("days", []):
                data["days"] = data.get("days", []) + [day_of_week]
            
            # Increase confidence
            new_confidence = min(1.0, existing["confidence"] + 0.1)
            cls.learn_pattern(user_id, "scheduling_hours", data, new_confidence)
        else:
            # Create new
            cls.learn_pattern(user_id, "scheduling_hours", 
                            {"hours": [hour], "days": [day_of_week]}, 0.5)
    
    @classmethod
    def learn_conflict_resolution(cls, user_id: str, resolution_type: str) -> None:
        """Learn conflict resolution preference"""
        import json
        
        patterns = cls.get_patterns(user_id)
        conflict_patterns = [p for p in patterns if p["pattern_type"] == "conflict_resolution"]
        
        if conflict_patterns:
            existing = conflict_patterns[0]
            data = json.loads(existing["pattern_data"])
            if resolution_type not in data.get("types", []):
                data["types"] = data.get("types", []) + [resolution_type]
            new_confidence = min(1.0, existing["confidence"] + 0.1)
            cls.learn_pattern(user_id, "conflict_resolution", data, new_confidence)
        else:
            cls.learn_pattern(user_id, "conflict_resolution", 
                            {"types": [resolution_type]}, 0.5)
    
    @classmethod
    def get_conflict_resolution_preference(cls, user_id: str) -> str:
        """Get preferred conflict resolution method"""
        import json
        patterns = cls.get_patterns(user_id)
        for p in patterns:
            if p["pattern_type"] == "conflict_resolution":
                data = json.loads(p["pattern_data"])
                types = data.get("types", [])
                return types[-1] if types else "suggest_alternative"
        return "suggest_alternative"
    
    # Full memory snapshot
    @classmethod
    def get_full_memory(cls, user_id: str) -> Dict[str, Any]:
        """Get complete memory state for user"""
        return {
            "short_term": {
                "conversation": cls.get_conversation(user_id),
                "pending_action": cls.get_pending_action(user_id)
            },
            "medium_term": {
                "preferences": cls.get_all_preferences(user_id),
                "meeting_prefs": cls.get_meeting_preferences(user_id)
            },
            "long_term": {
                "patterns": cls.get_patterns(user_id)
            }
        }
    
    @classmethod
    def clear_all_memory(cls, user_id: str) -> None:
        """Clear all memory layers for user"""
        cls.clear_short_term(user_id)
        # Note: Medium and long-term are preserved intentionally


# Singleton
agent_memory = AgentMemory()
