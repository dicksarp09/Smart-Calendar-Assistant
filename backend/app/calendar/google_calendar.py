"""
Calendar Module - Google Calendar Integration
Google Calendar API wrapper with caching
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.db import database


class GoogleCalendarService:
    """Google Calendar API wrapper"""
    
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    @classmethod
    def _get_credentials(cls, user_id: str) -> Optional[Credentials]:
        """Get Google credentials for user"""
        # In production, fetch from secure storage
        # For now, use refresh token from env
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "")
        
        if not refresh_token:
            return None
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "")
        )
        
        return creds
    
    @classmethod
    def _build_service(cls, user_id: str):
        """Build Google Calendar service"""
        creds = cls._get_credentials(user_id)
        return build("calendar", "v3", credentials=creds)
    
    @classmethod
    def get_events(cls, user_id: str, time_min: datetime = None, 
                   time_max: datetime = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar"""
        service = cls._build_service(user_id)
        
        now = datetime.utcnow()
        if time_min is None:
            time_min = now
        if time_max is None:
            time_max = now + timedelta(days=30)
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])
    
    @classmethod
    def create_event(cls, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event"""
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
        
        if event_data.get("recurrence"):
            event["recurrence"] = event_data["recurrence"]
        
        created = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()
        
        return cls._format_event(created)
    
    @classmethod
    def update_event(cls, user_id: str, event_id: str, 
                    event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing event"""
        service = cls._build_service(user_id)
        
        # Get existing
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
        
        return cls._format_event(updated)
    
    @classmethod
    def delete_event(cls, user_id: str, event_id: str) -> bool:
        """Delete an event"""
        service = cls._build_service(user_id)
        
        service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()
        
        return True
    
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