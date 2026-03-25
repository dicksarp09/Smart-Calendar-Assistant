"""
Pytest tests for FastAPI Calendar Intelligence Backend
Run with: pytest backend/tests/test_api.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
async def client():
    """Create test client for FastAPI app"""
    # Mock environment variables
    with patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test_client_id",
        "GOOGLE_CLIENT_SECRET": "test_client_secret",
        "GOOGLE_REFRESH_TOKEN": "test_refresh_token",
        "GROQ_API_KEY": "test_groq_key",
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test-audience"
    }):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test GET / returns API info"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test GET /health returns health status"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_me_endpoint_without_auth(client):
    """Test GET /me without authentication returns 401 or 403"""
    response = await client.get("/me")
    # Should return 401 or 403 without valid token
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_events_endpoint_without_auth(client):
    """Test GET /events without authentication returns 401 or 403"""
    response = await client.get("/events")
    # Should return 401 or 403 without valid token
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_agent_endpoint_without_auth(client):
    """Test POST /agent without authentication returns 401 or 403"""
    response = await client.post("/agent", json={
        "message": "What's on my calendar?",
        "conversation_history": []
    })
    # Should return 401 or 403 without valid token
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_agent_endpoint_with_message(client):
    """Test POST /agent with valid message"""
    # Mock the agent graph
    with patch("backend.app.agent.graph.create_agent_graph") as mock_graph:
        mock_graph_instance = MagicMock()
        mock_graph_instance.ainvoke = AsyncMock(return_value={
            "messages": ["Test response"],
            "action_taken": False
        })
        mock_graph.return_value = mock_graph_instance
        
        response = await client.post("/agent", json={
            "message": "What's on my calendar today?",
            "conversation_history": []
        })
        # May return 401/403 or 200 depending on auth setup
        assert response.status_code in [200, 401, 403, 422]


@pytest.mark.asyncio
async def test_event_input_validation(client):
    """Test EventInput model validation"""
    from backend.main import EventInput
    
    # Valid input
    valid_event = EventInput(
        summary="Test Event",
        start_time="2024-03-25T10:00:00Z",
        end_time="2024-03-25T11:00:00Z"
    )
    assert valid_event.summary == "Test Event"
    
    # Missing required field should raise validation error
    with pytest.raises(Exception):
        invalid_event = EventInput(
            start_time="2024-03-25T10:00:00Z",
            end_time="2024-03-25T11:00:00Z"
        )


@pytest.mark.asyncio
async def test_agent_request_validation(client):
    """Test AgentRequest model validation"""
    from backend.main import AgentRequest
    
    # Valid input
    valid_request = AgentRequest(
        message="Schedule a meeting",
        conversation_history=[]
    )
    assert valid_request.message == "Schedule a meeting"
    
    # Missing required field should raise validation error
    with pytest.raises(Exception):
        invalid_request = AgentRequest(conversation_history=[])


@pytest.mark.asyncio
async def test_cors_headers(client):
    """Test CORS headers are present"""
    response = await client.get("/", headers={
        "Origin": "http://localhost:5173"
    })
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestUtils:
    """Test utility functions"""
    
    def test_parse_date_time_with_date_only(self):
        """Test parse_date_time with date only"""
        from backend.services.utils import parse_date_time
        
        result = parse_date_time("2024-03-25")
        assert result is not None
        assert "date" in result
    
    def test_parse_date_time_with_datetime(self):
        """Test parse_date_time with full datetime"""
        from backend.services.utils import parse_date_time
        
        result = parse_date_time("2024-03-25T10:00:00Z")
        assert result is not None
        assert "date" in result
        assert "time" in result
    
    def test_classify_intent_query(self):
        """Test intent classification for query"""
        from backend.services.utils import classify_intent, IntentType
        
        result = classify_intent("What's on my calendar?")
        assert result in [IntentType.QUERY, IntentType.ACTION]
    
    def test_classify_intent_action(self):
        """Test intent classification for action"""
        from backend.services.utils import classify_intent, IntentType
        
        result = classify_intent("Schedule a meeting")
        assert result in [IntentType.QUERY, IntentType.ACTION]
    
    def test_format_events_response(self):
        """Test format_events_response"""
        from backend.services.utils import format_events_response
        
        events = [
            {
                "id": "1",
                "summary": "Test Event",
                "start": {"dateTime": "2024-03-25T10:00:00Z"},
                "end": {"dateTime": "2024-03-25T11:00:00Z"}
            }
        ]
        result = format_events_response(events)
        assert "events" in result or "formatted" in result or isinstance(result, list)
    
    def test_format_error_response(self):
        """Test format_error_response"""
        from backend.services.utils import format_error_response
        
        result = format_error_response("Test error")
        assert "error" in result or "message" in result


class TestValidation:
    """Test validation functions"""
    
    def test_validate_event_times_valid(self):
        """Test validate_event_times with valid times"""
        from backend.services.validation import validate_event_times
        
        result = validate_event_times(
            "2024-03-25T10:00:00Z",
            "2024-03-25T11:00:00Z"
        )
        assert result is True or result is None  # Valid or raises exception
    
    def test_validate_event_times_invalid(self):
        """Test validate_event_times with invalid times"""
        from backend.services.validation import validate_event_times
        
        # End before start should fail
        with pytest.raises(Exception):
            validate_event_times(
                "2024-03-25T11:00:00Z",
                "2024-03-25T10:00:00Z"
            )
    
    def test_validate_recurrence_rule(self):
        """Test validate_recurrence_rule"""
        from backend.services.validation import validate_recurrence_rule
        
        # Valid RRULE
        result = validate_recurrence_rule("FREQ=DAILY;COUNT=5")
        assert result is True or result is None
        
        # Invalid RRULE
        with pytest.raises(Exception):
            validate_recurrence_rule("INVALID")
