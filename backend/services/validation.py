"""
Validation utilities for event operations
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import re
from difflib import SequenceMatcher


class ValidationError(Exception):
    """Validation error exception"""
    pass


# Configurable limits
MIN_EVENT_DURATION_MINUTES = 5
MAX_EVENT_DURATION_HOURS = 8


def validate_event_dates(start_time: datetime, end_time: datetime) -> Tuple[bool, Optional[str]]:
    """
    Validate event dates.
    
    Returns:
        (is_valid, error_message)
    """
    now = datetime.utcnow()
    
    # Check if start time is in the past (allow 5 min grace period)
    grace_period = now - timedelta(minutes=5)
    if start_time < grace_period:
        return False, "Event start time must be in the future."
    
    # Check end time is after start time
    if end_time <= start_time:
        return False, "End time must be after start time."
    
    # Check duration limits
    duration = (end_time - start_time).total_seconds() / 60
    
    if duration < MIN_EVENT_DURATION_MINUTES:
        return False, f"Event must be at least {MIN_EVENT_DURATION_MINUTES} minutes."
    
    if duration > MAX_EVENT_DURATION_HOURS * 60:
        return False, f"Event cannot exceed {MAX_EVENT_DURATION_HOURS} hours."
    
    return True, None


def find_duplicate_events(events: List[Dict[str, Any]], new_title: str, 
                        new_start: datetime, new_end: datetime,
                        exclude_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find potential duplicate events.
    
    Checks:
    - Same title (case-insensitive)
    - Overlapping time
    
    Returns:
        List of potential duplicates
    """
    duplicates = []
    new_title_lower = new_title.lower().strip()
    
    for event in events:
        # Skip if same event
        if exclude_id and event.get("id") == exclude_id:
            continue
        
        event_title = event.get("summary", "").lower().strip()
        
        # Check title similarity
        title_similarity = SequenceMatcher(None, new_title_lower, event_title).ratio()
        
        # Check time overlap
        event_start = event.get("start")
        event_end = event.get("end")
        
        if isinstance(event_start, str):
            event_start = datetime.fromisoformat(event_start)
        if isinstance(event_end, str):
            event_end = datetime.fromisoformat(event_end)
        
        # Check overlap
        times_overlap = (event_start < new_end and event_end > new_start)
        
        # Consider duplicate if:
        # - Same title (>80% similarity) OR
        # - Exact same time
        if title_similarity > 0.8 or times_overlap:
            duplicates.append(event)
    
    return duplicates


def fuzzy_match_event(events: List[Dict[str, Any]], query: str, 
                     reference_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Fuzzy match an event based on natural language query.
    
    Examples:
    - "3pm meeting" -> finds meeting around 3pm
    - "team standup" -> finds event with similar title
    - "that client call" -> finds most recent client call
    
    Returns:
        Best matching event or None
    """
    if not events:
        return None
    
    query_lower = query.lower().strip()
    candidates = []
    
    # Extract time hints from query
    time_hints = extract_time_hints(query_lower)
    
    for event in events:
        score = 0
        event_title = event.get("summary", "").lower()
        event_start = event.get("start")
        
        if isinstance(event_start, str):
            event_start = datetime.fromisoformat(event_start)
        
        # Title similarity
        title_score = SequenceMatcher(None, query_lower, event_title).ratio()
        score += title_score * 0.5
        
        # Time proximity (if reference time provided)
        if reference_time and event_start:
            time_diff_hours = abs((event_start - reference_time).total_seconds() / 3600)
            # Closer times get higher scores
            if time_diff_hours <= 1:
                score += 0.5
            elif time_diff_hours <= 3:
                score += 0.3
        
        # Check for keywords
        keywords = ["meeting", "call", "standup", "review", "sync", "demo"]
        for keyword in keywords:
            if keyword in query_lower and keyword in event_title:
                score += 0.2
        
        candidates.append((event, score))
    
    if not candidates:
        return None
    
    # Sort by score descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return best match if score is reasonable
    best_match, best_score = candidates[0]
    if best_score > 0.3:
        return best_match
    
    return None


def extract_time_hints(query: str) -> Dict[str, Any]:
    """Extract time hints from query"""
    hints = {}
    
    # Look for hour patterns like "3pm", "10am", "2:30pm"
    hour_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', query)
    if hour_match:
        hour = int(hour_match.group(1))
        minute = int(hour_match.group(2)) if hour_match.group(2) else 0
        period = hour_match.group(3)
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        hints['hour'] = hour
        hints['minute'] = minute
    
    # Look for day references
    if 'today' in query:
        hints['day'] = 'today'
    elif 'tomorrow' in query:
        hints['day'] = 'tomorrow'
    
    return hints


def format_validation_error(error_type: str, details: str = None) -> str:
    """Format validation error messages"""
    messages = {
        "past_date": "Events must be scheduled in the future.",
        "invalid_duration": f"Event duration must be between {MIN_EVENT_DURATION_MINUTES} minutes and {MAX_EVENT_DURATION_HOURS} hours.",
        "end_before_start": "End time must be after start time.",
        "duplicate": "This appears to be a duplicate event.",
        "not_found": "I couldn't find that event.",
        "ambiguous": "I found multiple events matching your request. Please be more specific."
    }
    
    message = messages.get(error_type, "Validation failed.")
    if details:
        message += f" {details}"
    
    return message
