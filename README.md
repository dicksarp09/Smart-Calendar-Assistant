# Smart Calendar Intelligence - AI Calendar Agent

A production-grade AI-powered calendar application with React frontend and FastAPI backend. The system integrates Auth0 authentication, Google Calendar, and an AI agent powered by LangGraph and Groq LLM.

##  Architecture Overview

### Tech Stack

**Frontend:**
- React 18 with Vite
- react-big-calendar for calendar UI
- Zustand for state management
- Auth0 SDK for authentication

**Backend:**
- FastAPI (Python)
- Auth0 JWT verification
- Google Calendar API integration
- LangGraph for AI agent orchestration
- Groq LLM (LLaMA models)

### Project Structure

```
calendar-intelligence/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      # SQLite cache layer
│   ├── services/
│   │   ├── __init__.py
│   │   ├── calendar_service.py  # Cache-aware calendar service
│   │   └── utils.py           # Intent classification & date parsing
│   ├── memory/
│   │   ├── __init__.py
│   │   └── agent_memory.py  # Multi-layer agent memory
│   └── ws/
│       ├── __init__.py
│       └── websocket.py     # WebSocket manager
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Calendar.jsx     # react-big-calendar wrapper
│   │   │   ├── ChatPanel.jsx   # AI chat interface
│   │   │   └── EventModal.jsx  # Create/edit/delete events
│   │   ├── services/
│   │   │   ├── api.js          # Axios API client
│   │   │   └── websocket.js    # WebSocket client
│   │   ├── store/
│   │   │   └── useCalendarStore.js  # Zustand state management
│   │   ├── App.jsx            # Main application
│   │   ├── main.jsx          # Entry point with Auth0
│   │   └── index.css         # Styles
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
└── README.md
```

##  Authentication & Security

### Auth0 Integration
- Frontend uses Auth0 SDK for login
- JWT tokens are attached to every API request via Authorization header
- Backend verifies JWT using PyJWKClient
- User-level access control enforced on all endpoints

### Security Rules
1. Never expose Google tokens to frontend
2. Store tokens securely (in-memory for MVP, use DB for production)
3. All resources enforce user_id ownership

## 🚀 Features

### Phase 1 (MVP)
- ✅ Auth0 login with Google OAuth
- ✅ `/me` endpoint for user verification
- ✅ Fetch Google Calendar events
- ✅ Basic agent: "What's on my calendar today?"

### Phase 2 (CRUD)
- ✅ get_events - Fetch calendar events
- ✅ create_event - Create new events
- ✅ update_event - Modify existing events  
- ✅ delete_event - Remove events

### Phase 3 (Intelligence)
- ✅ Conflict detection before event creation
- ✅ Suggest alternative times when conflicts detected

### Phase 4 (Advanced Agent)
- ✅ Conversation memory (short-term)
- ✅ Multi-step instruction support via LangGraph

### ✅ Current Working Features (v1.0)
- **Calendar Views:** Day, Week, Month with custom time grid
- **Event Management:** Create, edit, delete events via UI or AI
- **AI Assistant:** Natural language queries and event creation
- **Smart Responses:** Free/busy days, event details with dates/times
- **Weekly Overview:** Shows free days vs busy days
- **Recurring Events:** RRULE support (daily, weekly, monthly)
- **Real-time Updates:** WebSocket support for live sync
- **Cache Layer:** SQLite caching for faster responses

## 📦 Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.10+
- Auth0 account
- Google Cloud Console project with Calendar API
- Groq API key

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

5. Configure `.env`:
   ```
   AUTH0_DOMAIN=your-tenant.auth0.com
   AUTH0_AUDIENCE=https://your-api.com
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GROQ_API_KEY=your-groq-api-key
   ENVIRONMENT=development
   ```

6. Run the backend:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Configure `.env`:
   ```
   VITE_AUTH0_DOMAIN=your-tenant.auth0.com
   VITE_AUTH0_CLIENT_ID=your-auth0-client-id
   VITE_AUTH0_AUDIENCE=https://your-api.com
   VITE_API_URL=http://localhost:8000
   VITE_ENVIRONMENT=development
   ```

5. Run the frontend:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

## 🔁 Data Flow

### Chat → Calendar
1. User sends message to AI agent
2. Backend agent processes using LangGraph
3. Tool executes action (get/create/update/delete)
4. Updated events returned to frontend
5. Zustand store updates
6. Calendar re-renders

### Calendar → Backend
1. User creates/edits/deletes event
2. UI sends update to API
3. Backend updates Google Calendar
4. State syncs across components

## 🧠 Agent Design

The AI agent uses LangGraph for orchestration:

```
parse_intent → execute_tools → generate_response
```

- **Intent Parsing**: Detects user intent (get_events, create_event, etc.)
- **Tool Execution**: Performs calendar operations via Google Calendar API
- **Response Generation**: Uses Groq LLM for natural responses

### Supported Commands

**Query Events:**
- "What events do I have today?"
- "What's on my calendar tomorrow?"
- "Show my weekly overview"
- "Any events next week?"
- "What days have events?"

**Create Events:**
- "Add dentist appointment Friday 2pm"
- "Create meeting Monday 10am"
- "Book haircut Saturday morning"
- "Add doctor visit next week"

**Free Time:**
- "What are my free slots today?"
- "When am I free this week?"
- "Find me a free time tomorrow"

**Manage Events:**
- "Move my 3pm meeting to Friday"
- "Cancel my meeting"

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/me` | Get current user (creates profile) |
| GET | `/events` | List calendar events (cached) |
| POST | `/events` | Create new event |
| PUT | `/events/{id}` | Update event |
| DELETE | `/events/{id}` | Delete event |
| POST | `/events/{id}/undo` | Undo delete (30s window) |
| POST | `/events/batch-delete` | Delete multiple events |
| GET | `/suggestions` | Get smart time slot suggestions |
| POST | `/mcp` | MCP protocol endpoint |
| GET | `/mcp/tools` | List MCP tools |
| POST | `/sync` | Sync calendar to cache |
| POST | `/agent` | AI agent chat |
| WS | `/ws/{user_id}` | WebSocket for real-time updates |

## 🔧 Development

### Running in Development Mode
Set `VITE_ENVIRONMENT=development` in frontend `.env` to use mock tokens.
In development mode:
- Frontend shows "Dev Login" button instead of Auth0 login
- Generates a valid mock JWT token for testing
- Backend validates the token using development mode parsing
- API endpoints require authentication but accept dev tokens

### Google Calendar Setup
1. Go to Google Cloud Console
2. Create a project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs

### Auth0 Setup
1. Create Auth0 tenant
2. Create API with identifier matching `AUTH0_AUDIENCE`
3. Create Application (SPA)
4. Configure allowed callback/logout URLs

# 🗓️  Auth + Read Extensions

## ✅ New Features Added

### 1. Calendar Sync Endpoint
- **Endpoint**: `POST /sync`
- **Purpose**: Force sync events from Google Calendar to local SQLite cache
- **Behavior**: Fetches latest events, updates cache with upsert logic
- **Why Important**: Allows manual cache refresh, ensures data consistency

### 2. Health Check Endpoint
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "ok",
  "services": {
    "api": "running",
    "auth": "connected",
    "google_calendar": "connected or degraded"
  }
}
```
- **Purpose**: Debugging, monitoring, deployment readiness
- **Why Important**: Critical for production monitoring, helps debug integration issues

### 3. User Profile Creation
- **Table**: `users`
- **Fields**: user_id, email, name, timezone, preferences, created_at, updated_at
- **Behavior**: Auto-creates on first login via `/me` endpoint
- **Why Important**: Stores user preferences, enables personalization

---

# 🤖 Basic Agent Intelligence

## ✅ New Features Added

### 1. Intent Classification
- Classifies user input as:
  - `query` → read-only (e.g., "What's on my calendar tomorrow?")
  - `action` → modification (create/update/delete)
- Uses keyword-based classification with rule fallback
- **Why Important**: Enables proper routing, prevents unintended modifications

### 2. Date/Time Parsing
- Converts natural language to ISO format:
  - "tomorrow" → `2026-03-23`
  - "next Monday at 10am" → `2026-03-24T10:00:00`
  - "March 25th" → `2026-03-25`
- Uses deterministic parsing with regex patterns
- **Why Important**: Makes the agent user-friendly, reduces friction

### 3. Error Handling
- Graceful error responses:
  - Invalid date: "I couldn't understand the date. Try something like 'tomorrow' or 'March 25th'."
  - Empty calendar: "Your calendar is empty. Would you like to create an event?"
  - Google API failure: "I'm having trouble connecting to Google Calendar."
  - Auth failure: "There was an authentication issue."
- **Why Important**: Prevents crashes, provides actionable feedback

---

# 🗄️ SQLite Cache Layer

## Why It Matters

- **Reduces API calls**: Cache events locally, fetch from Google only when needed
- **Prevents rate limits**: Google Calendar API has quotas; caching prevents excessive calls
- **Faster UI response**: Serve cached data instantly while fetching updates in background
- **Offline support**: Works partially when internet is unavailable

## How It Works

Pattern: `User request → Check cache → If miss → Fetch from Google → Update cache → Return`

- Cache TTL: 5 minutes
- Tables: `events_cache`, `user_memory`, `agent_behavior`

---

# ⚡ Real-Time Updates (WebSockets)

## Why It Matters

- **Instant sync**: UI updates immediately when events change
- **Multi-device support**: Changes on one device reflect on all devices
- **Better UX**: No need to manually refresh the page
- **Agent integration**: AI can push updates without user interaction

## How It Works

- Backend: `/ws/{user_id}` endpoint broadcasts on event changes
- Frontend: WebSocket client listens and updates Zustand store

---

# 🧠 Agent Memory Architecture

## Why It Matters

- **Personalization**: Agent learns user preferences over time
- **Context awareness**: Remembers past interactions for better responses
- **Smart scheduling**: Learns preferred meeting times and patterns
- **Conflict resolution**: Remembers how user prefers to handle conflicts

## Memory Layers

### 1. Short-term (In-Memory)
- Conversation history
- Current intent
- Pending actions

### 2. Medium-term (SQLite)
- Preferred meeting times
- Default durations
- Frequent attendees

### 3. Long-term (SQLite)
- Scheduling patterns
- Conflict resolution preferences
- Interaction style

---

# 🔒 Safe CRUD Operations

## ✅ New Features Added

### 1. Duplicate Detection
- Checks for same title + overlapping time before creating
- Returns warning + requires confirmation
- **Why Important**: Prevents accidental duplicate events

### 2. Validation Layer
- Validates dates are in future
- Enforces min 5 min / max 8 hour duration
- **Why Important**: Prevents invalid event creation

### 3. Event Identification (Fuzzy Matching)
- Maps natural language to actual event
- Uses time proximity + title similarity
- **Why Important**: Enables commands like "cancel my 3pm meeting"

### 4. Confirmation Flow
- Agent asks "Delete 'X' at Y?" before destructive actions
- **Why Important**: Prevents accidental deletions

### 5. Undo Capability (30 seconds)
- Stores event data for 30s after delete
- Returns undo token for quick restoration
- **Why Important**: Safety net for mistakes

### 6. Batch Operations
- Delete multiple events at once
- Partial failure handling
- **Why Important**: Efficiency for power users

### 7. Recurring Events Support
- Accepts RRULE format (e.g., `["RRULE:FREQ=DAILY"]`)
- Supports daily, weekly, monthly recurrence
- **Why Important**: Enables regular meetings without manual creation

---

# 🧠  Intelligent Scheduling

## ✅ New Features Added

### 1. Working Hours Constraint
- Configurable work_start / work_end in user profile
- Events outside hours flagged
- **Why Important**: Respects personal boundaries

### 2. Buffer Time Between Meetings
- 15-minute buffer enforced between events
- Expanded availability checks
- **Why Important**: Prevents back-to-back meeting fatigue

### 3. Meeting Duration Prediction
- Predicts duration from meeting title
- "standup" → 15 min, "review" → 45 min, etc.
- **Why Important**: Saves user time setting durations

### 4. Optimal Time Finder
- Ranks available slots by score
- Considers working hours, buffers, preferences
- Returns top 3 suggestions
- **Why Important**: Smart suggestions, not just available times

### 5. Priority System
- High/medium/low priority events
- Low priority can be auto-rescheduled
- Conflict resolution based on priority
- **Why Important**: Protects important meetings

### 6. Adaptive Learning
- Tracks accepted/rejected suggestions
- Pattern recognition from history
- Context-aware rules engine
- **Why Important**: Improves suggestions over time

### 7. Multi-Person Scheduling
- Attendee availability checking
- Round-robin for fair distribution
- Meeting clustering to reduce fragmentation
- **Why Important**: Enables group scheduling

---

# ✅ AI Agent Testing Results

## Mass Test Results (25 Questions)

**Test Date:** March 2026  
**Total Questions:** 25  
**Passed:** 25 (100%)  
**Average Response Time:** ~3.5 seconds

### Key Features Working:

- ✅ Query events (today, tomorrow, this week, next week, specific dates)
- ✅ Create events with natural language dates (Friday 2pm, Monday 10am)
- ✅ Weekly overview with FREE/BUSY days breakdown
- ✅ Free time slots detection
- ✅ All-day events support
- ✅ Recurring events (RRULE format)
- ✅ Conflict detection
- ✅ Smart time suggestions

### Test Questions Breakdown:

| # | Question Type | Example | Status |
|---|--------------|---------|--------|
| 1-10 | Query Events | "What events do I have today?" | ✅ PASS |
| 11-15 | Create Events | "Add dentist Friday 2pm" | ✅ PASS |
| 16-20 | Free Time | "When am I free this week?" | ✅ PASS |
| 21-25 | Edge Cases | "Show me all events" | ✅ PASS |

### Sample Responses:

**Weekly Overview:**
```
You have FREE time on: Tuesday-March 24, Wednesday-March 25, Thursday-March 26

But you have meetings on:
• Monday-March 23:
  - Meeting (03:00 PM - 04:00 PM)
• Friday-March 27:
  - Dentist Appointment (02:00 PM - 03:00 PM)
```

**Event Creation:**
```
I've created a new event in your Google Calendar:

* Event: Dentist Appointment
* Date: 2026-03-27
* Time: 02:00 PM - 03:00 PM
```

---

# 🔒 PHASE 7: Security & Observability

## ✅ New Features Added

### 1. Rate Limiting
- Per-user, per-endpoint limiting (100 requests/minute)
- Returns 429 status when exceeded
- **Why Important**: Prevents abuse, ensures fair usage

### 2. Audit Logging
- Logs all CRUD + agent actions with user_id + timestamp
- Integrated with central logger
- **Why Important**: Compliance, security auditing

### 3. Data Encryption
- Fernet (symmetric) encryption for sensitive data
- Encrypts user preferences, scheduling rules
- **Why Important**: Data at rest protection

### 4. Prometheus Metrics
- `/metrics` endpoint for scraping
- Tracks events, cache, agent queries, latency
- **Why Important**: Production monitoring

### 5. MCP (Model Context Protocol)
- Agent uses MCP to call tools, never directly
- 6 calendar tools registered: get_events, create_event, update_event, delete_event, find_available_slots, check_conflicts
- Standardized protocol for tool access
- **Why Important**: Security - agent cannot bypass tool layer

---

## 📄 License

