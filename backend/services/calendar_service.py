"""
Calendar Service with SQLite Caching
Handles Google Calendar operations with cache layer
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio

from fastapi import HTTPException, status
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.db import database
from backend.services.validation import validate_event_dates, find_duplicate_events
from backend.scheduling.engine import SchedulingEngine, MeetingDurationPredictor, OptimalTimeFinder
from backend.scheduling.learning import AdaptiveScheduler

# Cache TTL in seconds (5 minutes)
CACHE_TTL_SECONDS = 300


class CalendarService:
    """Calendar service with caching layer"""
    
    # Class-level storage for active connections
    connections: Dict[str, Any] = {}
    
    @classmethod
    def _get_google_credentials(cls, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for user"""
        from backend.main import config
        
        # First check session store
        user_session = config.SESSION_STORE.get(user_id)
        if user_session:
            token_data = user_session.get("google_token")
            if token_data:
                return Credentials(
                    token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=config.GOOGLE_CLIENT_ID,
                    client_secret=config.GOOGLE_CLIENT_SECRET
                )
        
        # Use default refresh token
        if config.GOOGLE_REFRESH_TOKEN:
            return Credentials(
                token=None,
                refresh_token=config.GOOGLE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=config.GOOGLE_CLIENT_ID,
                client_secret=config.GOOGLE_CLIENT_SECRET
            )
        
        return None
    
    @classmethod
    def _build_service(cls, user_id: str):
        """Build Google Calendar service"""
        credentials = cls._get_google_credentials(user_id)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Calendar not connected"
            )
        return build("calendar", "v3", credentials=credentials)
    
    @classmethod
    def _is_cache_valid(cls, events: List[Dict[str, Any]]) -> bool:
        """Check if cache is still valid"""
        if not events:
            return False
        
        try:
            latest = max(datetime.fromisoformat(e['updated_at']) for e in events)
            # Make latest naive for comparison
            if latest.tzinfo:
                latest = latest.replace(tzinfo=None)
            age = (datetime.utcnow() - latest).total_seconds()
            return age < CACHE_TTL_SECONDS
        except:
            return False
    
    @classmethod
    async def get_events(cls, user_id: str, time_min: Optional[datetime] = None, 
                        time_max: Optional[datetime] = None, max_results: int = 50,
                        use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get events with cache support
        Pattern: Check cache → If miss/stale → Fetch from Google → Update cache → Return
        """
        # Check cache first
        if use_cache:
            cached_events = database.get_cached_events(user_id)
            if cached_events and cls._is_cache_valid(cached_events):
                # Filter by time range if specified
                if time_min or time_max:
                    # Make time_min/time_max naive for comparison
                    if time_min and time_min.tzinfo:
                        time_min = time_min.replace(tzinfo=None)
                    if time_max and time_max.tzinfo:
                        time_max = time_max.replace(tzinfo=None)
                    filtered = []
                    for e in cached_events:
                        event_start = datetime.fromisoformat(e['start_time'])
                        # Make event_start naive for comparison
                        if event_start.tzinfo:
                            event_start = event_start.replace(tzinfo=None)
                        if time_min and event_start < time_min:
                            continue
                        if time_max and event_start > time_max:
                            continue
                        filtered.append(e)
                    return [cls._format_event_from_cache(e) for e in filtered]
                return [cls._format_event_from_cache(e) for e in cached_events]
        
        # Cache miss or stale - fetch from Google
        # Always invalidate cache to get fresh data
        database.invalidate_user_cache(user_id)
        service = cls._build_service(user_id)
        
        if not time_min:
            # Fetch from start of today (not from now) to include today's past events
            time_min = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if not time_max:
            # Fetch 90 days to include more events
            time_max = time_min + timedelta(days=90)
        
        try:
            events_result = service.events().list(
                calendarId="primary",
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            # Update cache
            database.invalidate_user_cache(user_id)
            for event in events:
                start = event.get("start", {})
                end = event.get("end", {})
                start_time = start.get("dateTime", start.get("date"))
                end_time = end.get("dateTime", end.get("date"))
                
                database.cache_event(
                    user_id=user_id,
                    event_id=event.get("id", ""),
                    title=event.get("summary", "No Title"),
                    description=event.get("description"),
                    start_time=start_time,
                    end_time=end_time
                )
            
            return [cls._format_event(event) for event in events]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch events: {str(e)}"
            )
    
    @staticmethod
    def _format_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google event to response format"""
        start = event.get("start", {})
        end = event.get("end", {})
        
        return {
            "id": event.get("id", ""),
            "summary": event.get("summary", "No Title"),
            "description": event.get("description"),
            "start": datetime.fromisoformat(start.get("dateTime", start.get("date"))),
            "end": datetime.fromisoformat(end.get("dateTime", end.get("date"))),
            "html_link": event.get("htmlLink", "")
        }
    
    @staticmethod
    def _format_event_from_cache(event: Dict[str, Any]) -> Dict[str, Any]:
        """Format cached event to response format"""
        return {
            "id": event["event_id"],
            "summary": event["title"],
            "description": event.get("description"),
            "start": datetime.fromisoformat(event["start_time"]),
            "end": datetime.fromisoformat(event["end_time"]),
            "html_link": ""
        }
    
    @classmethod
    async def create_event(cls, user_id: str, event_data: Dict[str, Any], 
                         skip_validation: bool = False) -> Dict[str, Any]:
        """Create event - always call Google first, then update cache
        
        Args:
            user_id: User ID
            event_data: Event data dict
            skip_validation: If True, skip duplicate/validation checks
        """
        # Validate dates if not skipped
        if not skip_validation:
            start_time = datetime.fromisoformat(event_data.get("start_time"))
            end_time = datetime.fromisoformat(event_data.get("end_time"))
            
            is_valid, error_msg = validate_event_dates(start_time, end_time)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Check for duplicates
            events = await cls.get_events(user_id, use_cache=True)
            duplicates = find_duplicate_events(
                events,
                event_data.get("summary", ""),
                start_time,
                end_time
            )
            
            if duplicates:
                return {
                    "status": "needs_confirmation",
                    "message": "Potential duplicate found",
                    "duplicates": duplicates,
                    "event_data": event_data
                }
        
        service = cls._build_service(user_id)
        
        event = {
            "summary": event_data.get("summary"),
            "description": event_data.get("description"),
            "start": {
                "dateTime": event_data.get("start_time"),
                "timeZone": event_data.get("time_zone", "UTC")
            },
            "end": {
                "dateTime": event_data.get("end_time"),
                "timeZone": event_data.get("time_zone", "UTC")
            }
        }
        
        # Add recurrence if provided (e.g., ["RRULE:FREQ=DAILY"])
        if event_data.get("recurrence"):
            event["recurrence"] = event_data["recurrence"]
        
        try:
            created_event = service.events().insert(
                calendarId="primary",
                body=event
            ).execute()
            
            # Update cache
            start = created_event.get("start", {})
            end = created_event.get("end", {})
            database.cache_event(
                user_id=user_id,
                event_id=created_event.get("id", ""),
                title=created_event.get("summary", ""),
                description=created_event.get("description"),
                start_time=start.get("dateTime", start.get("date")),
                end_time=end.get("dateTime", end.get("date"))
            )
            
            return cls._format_event(created_event)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {str(e)}"
            )
    
    @classmethod
    async def update_event(cls, user_id: str, event_id: str, 
                         event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update event - always call Google first, then update cache"""
        service = cls._build_service(user_id)
        
        try:
            # Get existing event
            existing = service.events().get(
                calendarId="primary",
                eventId=event_id
            ).execute()
            
            # Update fields
            if event_data.get("summary"):
                existing["summary"] = event_data["summary"]
            if event_data.get("description"):
                existing["description"] = event_data["description"]
            if event_data.get("start_time"):
                existing["start"] = {
                    "dateTime": event_data["start_time"],
                    "timeZone": "UTC"
                }
            if event_data.get("end_time"):
                existing["end"] = {
                    "dateTime": event_data["end_time"],
                    "timeZone": "UTC"
                }
            
            updated = service.events().update(
                calendarId="primary",
                eventId=event_id,
                body=existing
            ).execute()
            
            # Update cache
            start = updated.get("start", {})
            end = updated.get("end", {})
            database.cache_event(
                user_id=user_id,
                event_id=updated.get("id", ""),
                title=updated.get("summary", ""),
                description=updated.get("description"),
                start_time=start.get("dateTime", start.get("date")),
                end_time=end.get("dateTime", end.get("date"))
            )
            
            return cls._format_event(updated)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event: {str(e)}"
            )
    
    @classmethod
    async def delete_event(cls, user_id: str, event_id: str, store_undo: bool = True) -> Dict[str, Any]:
        """Delete event - always call Google first, then invalidate cache
        
        Args:
            user_id: User ID
            event_id: Event ID to delete
            store_undo: If True, store event data for undo
        """
        service = cls._build_service(user_id)
        
        try:
            # Get event data before deleting (for undo)
            event_data = None
            if store_undo:
                try:
                    event = service.events().get(
                        calendarId="primary",
                        eventId=event_id
                    ).execute()
                    event_data = {
                        "summary": event.get("summary"),
                        "description": event.get("description"),
                        "start_time": event.get("start", {}).get("dateTime"),
                        "end_time": event.get("end", {}).get("dateTime")
                    }
                except:
                    pass
            
            service.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()
            
            # Invalidate cache for this event
            database.delete_cached_event(user_id, event_id)
            
            # Store for undo if enabled
            undo_token = None
            if event_data:
                undo_token = database.store_action_for_undo(user_id, "delete", event_data)
            
            return {
                "success": True,
                "undo_token": undo_token
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event: {str(e)}"
            )
    
    @classmethod
    async def undo_action(cls, user_id: str, undo_token: str) -> Dict[str, Any]:
        """Undo a delete action within 30 seconds"""
        action = database.get_undo_action(user_id, undo_token)
        
        if not action:
            return {
                "success": False,
                "message": "Undo token expired or not found"
            }
        
        if action.get("action_type") == "delete":
            # Recreate the deleted event
            event_data = action.get("event_data", {})
            new_event = await cls.create_event(user_id, event_data, skip_validation=True)
            database.clear_undo_token(user_id, undo_token)
            return {
                "success": True,
                "message": "Event restored",
                "event": new_event
            }
        
        return {
            "success": False,
            "message": "Unknown action type"
        }
    
    @classmethod
    async def batch_delete_events(cls, user_id: str, event_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple events safely"""
        results = []
        failures = []
        
        for event_id in event_ids:
            try:
                result = await cls.delete_event(user_id, event_id, store_undo=False)
                results.append(event_id)
            except Exception as e:
                failures.append({"event_id": event_id, "error": str(e)})
        
        return {
            "deleted": results,
            "failures": failures,
            "total": len(event_ids),
            "success": len(failures) == 0
        }
    
    @classmethod
    async def check_conflicts(cls, user_id: str, start_time: datetime, 
                            end_time: datetime, exclude_event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for time conflicts"""
        events = await cls.get_events(user_id, 
                                     time_min=start_time - timedelta(hours=1),
                                     time_max=end_time + timedelta(hours=1),
                                     use_cache=True)
        
        conflicts = []
        for event in events:
            if exclude_event_id and event["id"] == exclude_event_id:
                continue
            
            # Check overlap
            if event["start"] < end_time and event["end"] > start_time:
                conflicts.append(event)
        
        return conflicts
    
    @staticmethod
    def suggest_alternative_time(user_id: str, duration_minutes: int, 
                                 preferred_date: datetime) -> datetime:
        """Suggest an alternative time slot using the scheduling engine"""
        
        # Try to get user preferences
        user_profile = database.get_user(user_id)
        preferences = {}
        if user_profile and user_profile.get("preferences"):
            import json
            try:
                preferences = json.loads(user_profile["preferences"])
            except:
                pass
        
        # Get current events
        events = []
        try:
            # Try cache first
            cached = database.get_cached_events(user_id)
            events = cached
        except:
            pass
        
        # Use scheduling engine
        engine = SchedulingEngine(preferences)
        suggestions = engine.suggest_time_slots(events, preferred_date.date().isoformat(), "meeting")
        
        if suggestions:
            return suggestions[0]["start"]
        
        # Fallback to simple logic
        suggested = preferred_date.replace(minute=0, second=0, microsecond=0)
        
        if suggested <= datetime.utcnow():
            suggested = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        return suggested

    @classmethod
    def suggest_time_slots(cls, user_id: str, meeting_title: str, 
                          date_str: str, duration_minutes: int = None) -> List[Dict[str, Any]]:
        """Get intelligent time slot suggestions"""
        
        # Get user preferences
        user_profile = database.get_user(user_id)
        preferences = {}
        if user_profile and user_profile.get("preferences"):
            import json
            try:
                preferences = json.loads(user_profile["preferences"])
            except:
                pass
        
        # Get events
        try:
            events = cls.get_events(user_id, use_cache=True)
        except:
            events = []
        
        # Use scheduling engine
        engine = SchedulingEngine(preferences)
        
        # Calculate duration
        if duration_minutes is None:
            duration_minutes = MeetingDurationPredictor.predict_duration(meeting_title)
        
        # Get suggestions
        try:
            date = datetime.fromisoformat(date_str)
        except:
            date = datetime.utcnow()
        
        slots = OptimalTimeFinder.find_available_slots(events, date, duration_minutes, 
                                                       engine.constraints, num_slots=3)
        
        return [
            {
                "start": slot["start"].isoformat(),
                "end": slot["end"].isoformat(),
                "score": slot["score"]
            }
            for slot in slots
        ]
    


# Singleton instance
calendar_service = CalendarService()
