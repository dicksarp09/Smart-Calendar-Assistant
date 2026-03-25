"""
Event Schemas
Pydantic models for event-related data
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EventInput(BaseModel):
    """Input schema for creating an event"""
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Start time in ISO format")
    end_time: datetime = Field(..., description="End time in ISO format")
    time_zone: str = Field("UTC", description="Time zone")
    recurrence: Optional[List[str]] = Field(None, description="RRULE recurrence")
    priority: Optional[str] = Field("medium", description="Event priority")


class EventUpdate(BaseModel):
    """Input schema for updating an event"""
    summary: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: Optional[str] = None


class EventResponse(BaseModel):
    """Response schema for event data"""
    id: str
    summary: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    html_link: str = ""
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Response schema for event list"""
    events: List[EventResponse]
    total: int
    has_more: bool = False