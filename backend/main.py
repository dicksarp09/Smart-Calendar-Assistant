"""
Calendar Intelligence - Backend Main Application
FastAPI server with Auth0 authentication and Google Calendar integration
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.auth.middleware import get_current_user, get_current_user_optional, require_user_id
from backend.app.auth.auth0 import TokenPayload
from backend.services.calendar_service import calendar_service
from backend.services.utils import parse_date_time, format_events_response, format_error_response, classify_intent, IntentType


# Lifespan event handler for startup/shutdown
extract_config = lambda key, default="": os.getenv(key, default)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("\n" + "=" * 50)
    print(" Calendar Intelligence - Backend Initialization")
    print("=" * 50)
    google_config = extract_config("GOOGLE_CLIENT_ID")
    groq_config = extract_config("GROQ_API_KEY")
    auth0_config = extract_config("AUTH0_DOMAIN")
    print(f"Google Calendar: {'Configured' if google_config else 'Not configured'}")
    print(f"Groq LLM: {'Configured' if groq_config else 'Not configured'}")
    print(f"Auth0: {'Configured' if auth0_config else 'Not configured'}")
    print("=" * 50 + "\n")
    yield
    # Shutdown
    print("Shutting down...")


# Initialize FastAPI app with lifespan
app = FastAPI(title="Calendar Intelligence API", version="1.0.0", lifespan=lifespan)

# Configuration
class Config:
    """Application configuration"""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-s62m25igz6sdix66.eu.auth0.com")
    AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://calendar-api")
    SESSION_STORE: Dict[str, Any] = {}

config = Config()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EventInput(BaseModel):
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: str = Field(..., description="Start time in ISO format")
    end_time: str = Field(..., description="End time in ISO format")
    time_zone: str = Field("UTC", description="Time zone")
    recurrence: Optional[List[str]] = Field(None, description="RRULE recurrence")

class EventResponse(BaseModel):
    id: str
    summary: str
    description: Optional[str]
    start: str
    end: str

class AgentRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

# Import agent graph
try:
    from backend.app.agent.graph import create_agent_graph
    agent_graph = create_agent_graph()
    print("OK: Agent graph loaded")
except Exception as e:
    print(f"WARNING: Agent graph not available: {e}")
    agent_graph = None

# Health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "Calendar Intelligence API"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "google_configured": bool(config.GOOGLE_CLIENT_ID),
        "groq_configured": bool(config.GROQ_API_KEY),
        "auth0_configured": bool(config.AUTH0_DOMAIN)
    }

# Get events endpoint
@app.get("/events")
async def get_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    user_id: str = Depends(require_user_id)
):
    """Get calendar events - requires authentication"""
    t_min = datetime.fromisoformat(time_min) if time_min else None
    t_max = datetime.fromisoformat(time_max) if time_max else None
    
    # user_id is now required from the token
    
    events = await calendar_service.get_events(
        user_id, 
        time_min=t_min, 
        time_max=t_max
    )
    
    # Convert events to dict format for response
    from datetime import datetime
    events_response = []
    for e in events:
        event_dict = {}
        if hasattr(e, 'dict'):
            event_dict = e.dict()
        elif isinstance(e, dict):
            event_dict = e
        else:
            event_dict = str(e)
        
        # Convert datetime objects to ISO strings
        if 'start' in event_dict and isinstance(event_dict['start'], datetime):
            event_dict['start'] = event_dict['start'].isoformat()
        if 'end' in event_dict and isinstance(event_dict['end'], datetime):
            event_dict['end'] = event_dict['end'].isoformat()
            
        events_response.append(event_dict)
    
    return {"events": events_response}

# Create event endpoint
@app.post("/events")
async def create_event(
    event_data: EventInput,
    user_id: str = Depends(require_user_id)
):
    """Create a new calendar event with conflict detection - requires authentication"""
    
    # Check for conflicts
    conflicts = await calendar_service.check_conflicts(
        user_id,
        event_data.start_time,
        event_data.end_time
    )
    
    if conflicts:
        return {
            "status": "conflict",
            "conflicts": conflicts,
            "suggestion": "Try a different time slot"
        }
    
    # Create event
    event = await calendar_service.create_event(
        user_id,
        event_data.dict()
    )
    
    return {"status": "success", "event": event}

# Update event endpoint
@app.put("/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: EventInput,
    user_id: str = Depends(require_user_id)
):
    """Update an existing calendar event - requires authentication"""
    
    event = await calendar_service.update_event(
        user_id,
        event_id,
        event_data.dict()
    )
    
    return {"status": "success", "event": event}

# Delete event endpoint
@app.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    user_id: str = Depends(require_user_id)
):
    """Delete a calendar event - requires authentication"""
    
    result = await calendar_service.delete_event(
        user_id,
        event_id
    )
    
    return result

# Agent endpoint for AI interactions
@app.post("/agent")
async def agent(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user_optional)
):
    """AI Agent endpoint for natural language calendar interactions"""
    body = await request.json()
    message = body.get("message", "")
    
    # Use user_id from token or fall back to test_user for development
    if current_user is not None:
        user_id = current_user.sub
    else:
        user_id = body.get("user_id", "test_user")
    
    if not agent_graph:
        return {"response": "AI agent is not available", "error": "Agent not configured"}
    
    try:
        # Run the agent graph
        result = await agent_graph.ainvoke({
            "message": message,
            "user_id": user_id
        })
        
        return result
    except Exception as e:
        print(f"Agent error: {e}")
        return {"response": f"I encountered an error: {str(e)}", "error": str(e)}

# WebSocket for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time event updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({"status": "ok", "message": "Connected"})
    except WebSocketDisconnect:
        pass

# Print initialization status
def print_init_status():
    print("=" * 50)
    print(" Calendar Intelligence - Backend Initialization")
    print("=" * 50)
    print(f"✅ Google Calendar: {'Configured' if config.GOOGLE_CLIENT_ID else 'Not configured'}")
    print(f"   Client ID: {config.GOOGLE_CLIENT_ID[:20]}..." if config.GOOGLE_CLIENT_ID else "   Client ID: Not set")
    print(f"✅ Groq LLM: {'Configured' if config.GROQ_API_KEY else 'Not configured'}")
    if config.GROQ_API_KEY:
        print(f"   API Key: {config.GROQ_API_KEY[:20]}...")
    print(f"✅ Auth0: {'Configured' if config.AUTH0_DOMAIN else 'Not configured'}")
    print(f"   Domain: {config.AUTH0_DOMAIN}")
    print("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
