"""
Test configuration and fixtures for FastAPI tests
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "sub": "test_user_123",
        "email": "test@example.com",
        "email_verified": True
    }


@pytest.fixture
def mock_calendar_events():
    """Mock calendar events"""
    return [
        {
            "id": "event_1",
            "summary": "Team Meeting",
            "description": "Weekly team sync",
            "start": {"dateTime": "2024-03-25T10:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-25T11:00:00Z", "timeZone": "UTC"}
        },
        {
            "id": "event_2",
            "summary": "Lunch",
            "description": "Lunch with client",
            "start": {"dateTime": "2024-03-25T12:30:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-25T13:30:00Z", "timeZone": "UTC"}
        }
    ]


@pytest.fixture
def mock_calendar_service():
    """Mock calendar service"""
    with patch("backend.services.calendar_service.calendar_service") as mock:
        mock.get_events = AsyncMock(return_value=[])
        mock.create_event = AsyncMock(return_value={"id": "new_event"})
        mock.update_event = AsyncMock(return_value={"id": "updated_event"})
        mock.delete_event = AsyncMock(return_value=True)
        yield mock
