"""
Utility functions for the Calendar Agent
Includes date/time parsing and intent classification
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from enum import Enum


class IntentType(Enum):
    """User intent types"""
    QUERY = "query"      # Read-only (e.g., "What's on my calendar?")
    ACTION = "action"    # Requires modification (create/update/delete)


def classify_intent(message: str) -> IntentType:
    """
    Classify user input into query or action intent.
    
    Returns:
        IntentType.QUERY for read-only queries
        IntentType.ACTION for modification requests
    """
    message_lower = message.lower()
    
    # Action keywords (modification) - check FIRST with higher priority
    action_keywords = [
        "create ", "add ", "schedule ", "book ", "new event",
        "update", "change", "move", "reschedule",
        "delete", "remove", "cancel", "clear"
    ]
    
    # Check for action keywords FIRST
    for keyword in action_keywords:
        if keyword in message_lower:
            return IntentType.ACTION
    
    # Query keywords (read-only) - only if no action keywords found
    query_keywords = [
        "what's on", "what is on", "show me", "do i have", "any events",
        "when is", "what time", "schedule for", "calendar for", "upcoming",
        "today", "tomorrow", "this week", "next week", "list", "get",
        "what's scheduled", "what is scheduled", "scheduled for",
        "am i busy", "are you free", "free time", "free slot", "available",
        "what days", "what meetings", "events do i", "meetings do i",
        # Additional query patterns that were failing
        "calendar like", "all events", "find me", "when am i free",
        "what do i have", "show my", "check my", "view my",
        "any meetings", "any appointments", "days have events"
    ]
    
    for keyword in query_keywords:
        if keyword in message_lower:
            return IntentType.QUERY
    
    # Default to QUERY if unclear
    return IntentType.QUERY


def parse_date_time(input_text: str, reference_date: Optional[datetime] = None) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse natural language date/time to ISO format.
    
    Args:
        input_text: Natural language like "tomorrow", "next Monday at 10am"
        reference_date: Reference date (defaults to now)
    
    Returns:
        Tuple of (start_datetime, end_datetime) or (None, None) if parsing fails
    """
    if reference_date is None:
        reference_date = datetime.utcnow()
    
    text_lower = input_text.lower()
    
    # Parse time patterns first (e.g., "at 10am", "at 2:30pm", "2pm", "2:30pm")
    # First try pattern with "at" prefix
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
    # If not found, try pattern without "at" prefix
    if not time_match:
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)(?:\b|$)', text_lower)
    
    parsed_hour = None
    parsed_minute = 0
    if time_match:
        parsed_hour = int(time_match.group(1))
        parsed_minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        if period == 'pm' and parsed_hour != 12:
            parsed_hour += 12
        elif period == 'am' and parsed_hour == 12:
            parsed_hour = 0
    
    # Default time if no time specified - use 10am as default
    default_hour = parsed_hour if parsed_hour is not None else 10
    
    # Parse "today" (with specific time if mentioned, otherwise 10am)
    if "today" in text_lower:
        if parsed_hour is not None:
            start = reference_date.replace(hour=parsed_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        else:
            start = reference_date.replace(hour=10, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        return start, end
    
    # Parse "tomorrow" (with specific time if mentioned, otherwise 10am)
    if "tomorrow" in text_lower:
        if parsed_hour is not None:
            start = (reference_date + timedelta(days=1)).replace(hour=parsed_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        else:
            start = (reference_date + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        return start, end
    
    # Parse "next week"
    if "next week" in text_lower:
        days_until_next_week = (7 - reference_date.weekday()) % 7 + 7
        start = (reference_date + timedelta(days=days_until_next_week)).replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        return start, end
    
    # Parse "this week"
    if "this week" in text_lower:
        days_until_end = 7 - reference_date.weekday()
        start = reference_date.replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
        end = start + timedelta(days=days_until_end)
        return start, end
    
    # Parse day names (like "Tuesday" or "next Tuesday")
    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    # Default time if no time specified - use 10am as default
    default_hour = parsed_hour if parsed_hour is not None else 10
    
    for day_name, day_num in day_names.items():
        if f"next {day_name}" in text_lower:
            days_ahead = (day_num - reference_date.weekday()) % 7 + 7
            start = (reference_date + timedelta(days=days_ahead)).replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
            return start, end
        
        if day_name in text_lower:
            days_ahead = (day_num - reference_date.weekday()) % 7
            if days_ahead == 0 and parsed_hour is None:
                days_ahead = 7  # If today and no specific time, assume next occurrence
            start = (reference_date + timedelta(days=days_ahead)).replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
            return start, end
    
    # Parse specific date formats (e.g., "March 25th", "25th March")
    date_patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?',
        r'(\d{4})-(\d{2})-(\d{2})',  # ISO format
    ]
    
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                if len(match.groups()) == 3 and pattern.endswith(r'\d{2})'):
                    # ISO format
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    start = datetime(year, month, day, default_hour, 0, 0)
                    end = start + timedelta(hours=1)
                    return start, end
                elif len(match.groups()) == 2:
                    # Month day format
                    if match.group(1).isdigit():
                        day, month_name = int(match.group(1)), match.group(2)
                    else:
                        month_name, day = match.group(1), int(match.group(2))
                    
                    month = month_map.get(month_name)
                    if month:
                        year = reference_date.year
                        if month < reference_date.month:
                            year += 1
                        start = datetime(year, month, day, default_hour, 0, 0)
                        end = start + timedelta(hours=1)
                        return start, end
            except (ValueError, IndexError):
                pass
    
    # Parse time patterns (e.g., "at 10am", "at 2:30pm")
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        # Try to find a date in the input
        start, end = parse_date_time(input_text.replace(time_match.group(0), "").strip(), reference_date)
        if start:
            start = start.replace(hour=hour, minute=minute)
            end = start + timedelta(hours=1)
            return start, end
    
    # Could not parse
    return None, None


def format_events_response(events: list, date_label: str = "upcoming") -> str:
    """
    Format events into a readable response.
    
    Args:
        events: List of event dictionaries
        date_label: Label for the date (e.g., "tomorrow", "this week")
    
    Returns:
        Formatted string response
    """
    if not events:
        return f"You don't have any events {date_label}."
    
    # For weekly queries, show busy vs free days
    if date_label in ["this week", "next week"] and len(events) > 0:
        return format_weekly_response(events, date_label)
    
    if len(events) == 1:
        event = events[0]
        start = event.get("start")
        end = event.get("end")
        
        if isinstance(start, datetime) and isinstance(end, datetime):
            # Check if it's an all-day event (same date with 00:00 start)
            if start.strftime('%H:%M') == '00:00' and end.strftime('%H:%M') == '00:00':
                time_str = f"All day on {start.strftime('%B %d, %Y')}"
            else:
                time_str = f"{start.strftime('%B %d at %I:%M %p')} to {end.strftime('%I:%M %p')}"
        else:
            time_str = "all day"
        
        return f"You have 1 event {date_label}:\n\n{event.get('summary', 'Untitled')} – {time_str}"
    
    # Multiple events
    response = [f"You have {len(events)} events {date_label}:\n"]
    
    for i, event in enumerate(events, 1):
        start = event.get("start")
        end = event.get("end")
        
        if isinstance(start, datetime) and isinstance(end, datetime):
            # Check if it's an all-day event (same date with 00:00 start)
            if start.strftime('%H:%M') == '00:00' and end.strftime('%H:%M') == '00:00':
                time_str = f"All day on {start.strftime('%B %d, %Y')}"
            else:
                time_str = f"{start.strftime('%B %d at %I:%M %p')} to {end.strftime('%I:%M %p')}"
        else:
            time_str = "all day"
        
        response.append(f"{i}. {event.get('summary', 'Untitled')} – {time_str}")
    
    return "\n".join(response)


def format_weekly_response(events: list, date_label: str) -> str:
    """Format weekly events to show busy vs free days"""
    # Group events by date
    busy_days = {}
    for event in events:
        start = event.get("start")
        if isinstance(start, datetime):
            date_key = start.strftime('%Y-%m-%d')
            if date_key not in busy_days:
                busy_days[date_key] = []
            
            end = event.get("end")
            if isinstance(start, datetime) and isinstance(end, datetime):
                if start.strftime('%H:%M') == '00:00' and end.strftime('%H:%M') == '00:00':
                    time_str = "All day"
                else:
                    time_str = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
            else:
                time_str = "All day"
            
            busy_days[date_key].append(f"{event.get('summary', 'Meeting')} ({time_str})")
    
    # Determine the week range
    if events:
        first_event = events[0]
        start = first_event.get("start")
        if isinstance(start, datetime):
            # Find Monday of that week
            monday = start - timedelta(days=start.weekday())
            
            # Collect all days of the week
            all_days = []
            free_days = []
            for i in range(7):
                day = monday + timedelta(days=i)
                day_str = day.strftime('%Y-%m-%d')
                day_name = day.strftime('%A')
                day_date = day.strftime('%B %d')
                all_days.append((day_str, day_name, day_date))
                
                if day_str not in busy_days:
                    free_days.append(f"{day_name}-{day_date}")
            
            # Build response
            response = []
            
            if free_days:
                response.append(f"You have FREE time on: {', '.join(free_days)}")
            
            # Show busy days with events
            if busy_days:
                response.append("\nBut you have meetings on:")
                for day_str, day_name, day_date in all_days:
                    if day_str in busy_days:
                        response.append(f"• {day_name}-{day_date}:")
                        for event_str in busy_days[day_str]:
                            response.append(f"  - {event_str}")
            
            return "\n".join(response)
    
    return f"You don't have any events {date_label}."


def format_error_response(error_type: str, details: str = None) -> str:
    """
    Format error responses in a user-friendly way.
    
    Args:
        error_type: Type of error
        details: Additional details
    
    Returns:
        User-friendly error message
    """
    error_messages = {
        "invalid_date": "I couldn't understand the date. Try something like 'tomorrow' or 'March 25th'.",
        "empty_calendar": "Your calendar is empty. Would you like to create an event?",
        "google_api_failure": "I'm having trouble connecting to Google Calendar. Please try again later.",
        "auth_failure": "There was an authentication issue. Please log in again.",
        "not_found": "I couldn't find what you're looking for. Could you try rephrasing?",
        "unknown": "Something went wrong. Please try again."
    }
    
    message = error_messages.get(error_type, error_messages["unknown"])
    
    if details:
        message += f" ({details})"
    
    return message
