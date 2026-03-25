"""
Calendar Cache Module
SQLite-based caching for calendar events
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.db import database

# Cache TTL in seconds (5 minutes)
CACHE_TTL_SECONDS = 300


class CalendarCache:
    """SQLite-based calendar cache"""
    
    @classmethod
    def get_events(cls, user_id: str) -> List[Dict[str, Any]]:
        """Get cached events"""
        return database.get_cached_events(user_id)
    
    @classmethod
    def set_events(cls, user_id: str, events: List[Dict[str, Any]]) -> None:
        """Cache events"""
        for event in events:
            database.cache_event(
                user_id=user_id,
                event_id=event.get("id", ""),
                title=event.get("summary", ""),
                description=event.get("description"),
                start_time=str(event.get("start", "")),
                end_time=str(event.get("end", ""))
            )
    
    @classmethod
    def invalidate(cls, user_id: str, event_id: str = None) -> None:
        """Invalidate cache"""
        if event_id:
            database.delete_cached_event(user_id, event_id)
        else:
            database.clear_user_cache(user_id)
    
    @classmethod
    def is_valid(cls, user_id: str) -> bool:
        """Check if cache is valid"""
        cached = database.get_cached_events(user_id)
        if not cached:
            return False
        
        # Check timestamp
        for event in cached:
            cached_at = event.get("cached_at")
            if cached_at:
                cached_time = datetime.fromisoformat(cached_at)
                age = (datetime.utcnow() - cached_time).total_seconds()
                if age > CACHE_TTL_SECONDS:
                    return False
        
        return True


class CalendarSync:
    """Calendar synchronization and WebSocket triggers"""
    
    @staticmethod
    async def notify_event_created(user_id: str, event: Dict[str, Any]) -> None:
        """Notify WebSocket clients of new event"""
        from backend.ws import notify_event_created
        await notify_event_created(user_id, event)
    
    @staticmethod
    async def notify_event_updated(user_id: str, event: Dict[str, Any]) -> None:
        """Notify WebSocket clients of updated event"""
        from backend.ws import notify_event_updated
        await notify_event_updated(user_id, event)
    
    @staticmethod
    async def notify_event_deleted(user_id: str, event_id: str) -> None:
        """Notify WebSocket clients of deleted event"""
        from backend.ws import notify_event_deleted
        await notify_event_deleted(user_id, event_id)