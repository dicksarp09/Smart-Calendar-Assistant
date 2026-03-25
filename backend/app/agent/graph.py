"""
Agent Graph Module
LangGraph workflow orchestration for calendar operations
"""

import re
import sys
import io
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END

# Fix Windows console encoding for UTF-8 output (best effort)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Best effort - continue if this fails


class AgentState(TypedDict):
    """State for LangGraph agent"""
    user_id: str
    message: str
    conversation_history: List[Dict]
    events: List[Any]
    response: str
    action_taken: Optional[str]
    tool_calls: List[str]


def create_agent_graph():
    """Create LangGraph agent for calendar operations"""
    
    def parse_intent_node(state: AgentState) -> AgentState:
        """Parse user intent from message using classification"""
        from backend.services.utils import classify_intent, parse_date_time, IntentType
        
        message = state["message"]
        print(f"\n=== PARSE_INTENT_NODE === Message: {message}")
        
        # Use intent classification
        intent = classify_intent(message)
        print(f"=== PARSE_INTENT === Intent: {intent}")
        
        tool_calls = []
        
        if intent == IntentType.QUERY:
            # Try to parse date/time from message
            start_time, end_time = parse_date_time(message)
            if start_time:
                state["message"] = message + f" [parsed_dates: {start_time.isoformat()} to {end_time.isoformat()}]"
            tool_calls.append("get_events")
        elif intent == IntentType.ACTION:
            message_lower = message.lower()
            if "create" in message_lower or "add" in message_lower or "schedule" in message_lower:
                tool_calls.append("create_event")
            elif "update" in message_lower or "move" in message_lower or "change" in message_lower:
                tool_calls.append("update_event")
            elif "delete" in message_lower or "remove" in message_lower or "cancel" in message_lower:
                tool_calls.append("delete_event")
            else:
                tool_calls.append("create_event")
        else:
            tool_calls.append("general_query")
        
        print(f"=== PARSE_INTENT === tool_calls: {tool_calls}")
        state["tool_calls"] = tool_calls
        return state
    
    def execute_tools_node(state: AgentState) -> AgentState:
        """Execute tools based on intent"""
        from backend.services.utils import format_events_response, format_error_response, parse_date_time
        from backend.services.calendar_service import calendar_service
        import asyncio
        
        print("\n=== EXECUTE_TOOLS_NODE ===")
        
        try:
            tool_calls = state.get("tool_calls", [])
            user_id = state["user_id"]
            message = state["message"]
            
            print(f"tool_calls: {tool_calls}")
            print(f"user_id: {user_id}")
            print(f"message: {message}")
            
            # Handle create_event
            if "create_event" in tool_calls:
                print("Handling create_event...")
                # Parse date/time from message
                start_time, end_time = parse_date_time(message)
                
                print(f"parse_date_time result: start={start_time}, end={end_time}")
                
                # Fix: If time is midnight (00:00), check for time-of-day hints
                if start_time and start_time.hour == 0:
                    msg_lower = message.lower()
                    if "morning" in msg_lower:
                        start_time = start_time.replace(hour=9, minute=0)
                        end_time = start_time + timedelta(hours=1)
                    elif "afternoon" in msg_lower:
                        start_time = start_time.replace(hour=14, minute=0)
                        end_time = start_time + timedelta(hours=1)
                    elif "evening" in msg_lower:
                        start_time = start_time.replace(hour=18, minute=0)
                        end_time = start_time + timedelta(hours=1)
                    elif "lunch" in msg_lower:
                        start_time = start_time.replace(hour=12, minute=0)
                        end_time = start_time + timedelta(hours=1)
                
                if start_time and end_time:
                    # Extract summary from message
                    msg_lower = message.lower()
                    
                    # Default summary
                    summary = "Meeting"
                    
                    # Try to find event name - remove common phrases
                    words_to_remove = ["add ", "create ", "schedule ", "book ", "new ", 
                                      " on ", " at ", " for ", " in ", " today", " tomorrow",
                                      " next week", " this week", " monday", " tuesday",
                                      " wednesday", " thursday", " friday", " saturday",
                                      " sunday", " every day", " daily", " weekly", " monthly",
                                      " morning", " afternoon", " evening",
                                      " what's ", " what is ", " show ", " do i ",
                                      " is ", " are ", " have ", " get "]
                    
                    temp_msg = msg_lower
                    for word in words_to_remove:
                        temp_msg = temp_msg.replace(word, " ")
                    
                    # Remove time patterns
                    temp_msg = re.sub(r'\d{1,2}(?:am|pm|am\b|pm\b)', '', temp_msg)
                    temp_msg = re.sub(r'\d{1,2}:\d{2}', '', temp_msg)
                    
                    # Get the remaining text as potential summary
                    potential = temp_msg.strip().title()
                    # Clean up: remove extra spaces, capitalize properly
                    potential = ' '.join(potential.split())
                    if potential and len(potential) > 2:
                        summary = potential
                    
                    # Check for recurrence patterns
                    recurrence = None
                    if "every day" in msg_lower or "daily" in msg_lower:
                        recurrence = ["RRULE:FREQ=DAILY"]
                        # For "every day at 9am", use today with that time
                        # Extract time from message if available
                        time_match = re.search(r'at\s+(\d{1,2})(?:am|pm)?', msg_lower)
                        hour = 9  # default
                        if time_match:
                            hour = int(time_match.group(1))
                            if 'pm' in msg_lower and hour != 12:
                                hour += 12
                            elif 'am' in msg_lower and hour == 12:
                                hour = 0
                        
                        start_time = datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)
                    elif "every week" in msg_lower or "weekly" in msg_lower:
                        recurrence = ["RRULE:FREQ=WEEKLY"]
                    elif "every month" in msg_lower or "monthly" in msg_lower:
                        recurrence = ["RRULE:FREQ=MONTHLY"]
                    
                    # Create the event
                    event_data = {
                        "summary": summary,
                        "description": "Created via AI Assistant",
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "time_zone": "UTC"
                    }
                    
                    if recurrence:
                        event_data["recurrence"] = recurrence
                    
                    print(f"Creating event with data: {event_data}")
                    
                    try:
                        created_event = asyncio.run(calendar_service.create_event(user_id, event_data, skip_validation=True))
                        try:
                            print(f"Event created successfully: {created_event}")
                        except:
                            print("Event created successfully")
                        
                        recurrence_text = "" if not recurrence else " (recurring)"
                        state["response"] = f"I've created a new event in your Google Calendar: \n\n* Event: {summary}\n* Date: {start_time.strftime('%Y-%m-%d')}\n* Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}{recurrence_text}\n\nWould you like me to add any attendees or details?"
                        state["action_taken"] = "create_event"
                    except Exception as e:
                        print(f"ERROR creating event: {str(e)}")
                        state["response"] = f"I had trouble creating the event: {str(e)}"
                        state["action_taken"] = "create_event_failed"
                else:
                    print(f"Failed to parse date/time from: {message}")
                    state["response"] = "I couldn't understand the date and time for the meeting. Please specify a date and time."
                    state["action_taken"] = "parse_failed"
                
            # Handle get_events
            elif "get_events" in tool_calls or "general_query" in tool_calls:
                # Try to parse date/time
                start_time, end_time = parse_date_time(state["message"])
                
                # Determine date label
                date_label = "upcoming"
                msg_lower = state["message"].lower()
                if "today" in msg_lower:
                    date_label = "today"
                elif "tomorrow" in msg_lower:
                    date_label = "tomorrow"
                elif "next week" in msg_lower:
                    date_label = "next week"
                elif "this week" in msg_lower:
                    date_label = "this week"
                
                if start_time and end_time:
                    events = asyncio.run(calendar_service.get_events(
                        user_id, time_min=start_time, time_max=end_time
                    ))
                else:
                    events = asyncio.run(calendar_service.get_events(user_id))
                    
                state["events"] = events
                state["response"] = format_events_response(events, date_label)
                state["action_taken"] = "get_events"
                
        except Exception as e:
            error_msg = str(e).lower()
            # Determine which tool was attempted based on tool_calls
            tool_calls = state.get("tool_calls", [])
            if "get_events" in tool_calls:
                state["action_taken"] = "get_events"
            elif "create_event" in tool_calls:
                state["action_taken"] = "create_event_failed"
            elif "update_event" in tool_calls:
                state["action_taken"] = "update_event_failed"
            elif "delete_event" in tool_calls:
                state["action_taken"] = "delete_event_failed"
            else:
                state["action_taken"] = "unknown"
            
            if "auth" in error_msg or "unauthorized" in error_msg:
                state["response"] = format_error_response("auth_failure")
            elif "google" in error_msg or "calendar" in error_msg:
                state["response"] = format_error_response("google_api_failure")
            else:
                state["response"] = format_error_response("unknown", str(e))
        
        return state
    
    def generate_response_node(state: AgentState) -> AgentState:
        """Generate final response using LLM"""
        from backend.services.utils import format_error_response
        
        print("\n=== GENERATE_RESPONSE_NODE ===")
        print(f"response: {state.get('response')}")
        print(f"action_taken: {state.get('action_taken')}")
        
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
            import os
            
            llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                api_key=os.getenv("GROQ_API_KEY", ""),
                temperature=0.7
            )
            
            # Build messages
            system_msg = SystemMessage(content="""You are a helpful calendar assistant. 
You can help users manage their Google Calendar by:
- Getting their upcoming events
- Creating new events
- Updating existing events
- Deleting events

Always be concise and helpful.""")
            
            history = state.get("conversation_history", [])[-5:]
            messages = [system_msg]
            
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))
            
            messages.append(HumanMessage(content=state["message"]))
            
            # Only generate LLM response if:
            # 1. No response was set by execute_tools_node, OR
            # 2. action_taken was not set (tools didn't run), OR  
            # 3. action_taken is "general_query" (fallback case)
            # This prevents hallucinated responses when tools actually ran
            action_taken = state.get("action_taken")
            response = state.get("response")
            
            if not response or action_taken in [None, "", "general_query"]:
                # Tools didn't run or failed - use LLM to generate response
                ai_response = llm.invoke(messages)
                state["response"] = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
                # Also set action_taken based on the intent from parse_intent_node
                tool_calls = state.get("tool_calls", [])
                if "get_events" in tool_calls:
                    state["action_taken"] = "get_events"
                elif "create_event" in tool_calls:
                    state["action_taken"] = "create_event"
                elif "update_event" in tool_calls:
                    state["action_taken"] = "update_event"
                elif "delete_event" in tool_calls:
                    state["action_taken"] = "delete_event"
            # Otherwise, keep the response from execute_tools_node (success or error)
            
        except Exception as e:
            if not state.get("response"):
                state["response"] = format_error_response("unknown", str(e))
        
        return state
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("generate_response", generate_response_node)
    
    workflow.set_entry_point("parse_intent")
    workflow.add_edge("parse_intent", "execute_tools")
    workflow.add_edge("execute_tools", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()


# Create global agent graph instance
agent_graph = create_agent_graph()