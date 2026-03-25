"""
Scheduling Engine - Intelligent Scheduling Module
Provides constraint-aware scheduling, smart suggestions, and optimization
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re


class SchedulingConstraints:
    """Handle scheduling constraints"""
    
    # Default working hours (can be overridden by user profile)
    DEFAULT_WORK_START = 9  # 9 AM
    DEFAULT_WORK_END = 17  # 5 PM
    
    # Buffer time between meetings (minutes)
    DEFAULT_BUFFER_MINUTES = 15
    
    # Meeting priority levels
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    
    @classmethod
    def get_user_constraints(cls, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Get user-specific constraints"""
        return {
            "work_start": user_preferences.get("work_start", cls.DEFAULT_WORK_START),
            "work_end": user_preferences.get("work_end", cls.DEFAULT_WORK_END),
            "buffer_minutes": user_preferences.get("buffer_minutes", cls.DEFAULT_BUFFER_MINUTES),
            "avoid_friday_afternoon": user_preferences.get("avoid_friday_afternoon", False),
            "prefer_mornings": user_preferences.get("prefer_mornings", True),
            "min_meeting_duration": user_preferences.get("min_meeting_duration", 15),
            "max_meeting_duration": user_preferences.get("max_meeting_duration", 240),
        }
    
    @classmethod
    def is_within_working_hours(cls, event_start: datetime, event_end: datetime,
                               constraints: Dict[str, Any]) -> bool:
        """Check if event is within working hours"""
        work_start = constraints.get("work_start", cls.DEFAULT_WORK_START)
        work_end = constraints.get("work_end", cls.DEFAULT_WORK_END)
        
        start_hour = event_start.hour
        end_hour = event_end.hour
        
        return start_hour >= work_start and end_hour <= work_end
    
    @classmethod
    def expand_with_buffer(cls, events: List[Dict[str, Any]], 
                          buffer_minutes: int) -> List[Dict[str, Any]]:
        """Expand events by buffer time"""
        buffered = []
        for event in events:
            start = event.get("start")
            end = event.get("end")
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            
            buffered_start = start - timedelta(minutes=buffer_minutes)
            buffered_end = end + timedelta(minutes=buffer_minutes)
            
            buffered.append({
                **event,
                "buffered_start": buffered_start,
                "buffered_end": buffered_end
            })
        
        return buffered
    
    @classmethod
    def is_available(cls, start: datetime, end: datetime, 
                    events: List[Dict[str, Any]], 
                    buffer_minutes: int) -> bool:
        """Check if time slot is available considering buffer"""
        for event in events:
            event_start = event.get("buffered_start", event.get("start"))
            event_end = event.get("buffered_end", event.get("end"))
            
            if isinstance(event_start, str):
                event_start = datetime.fromisoformat(event_start)
            if isinstance(event_end, str):
                event_end = datetime.fromisoformat(event_end)
            
            # Check overlap
            if start < event_end and end > event_start:
                return False
        
        return True
    
    @classmethod
    def check_friday_afternoon(cls, event_time: datetime) -> bool:
        """Check if time is Friday afternoon (should avoid)"""
        return event_time.weekday() == 4 and event_time.hour >= 14
    
    @classmethod
    def is_preferred_time(cls, event_time: datetime, 
                         constraints: Dict[str, Any]) -> bool:
        """Check if time matches user preferences"""
        # Check Friday afternoon avoidance
        if constraints.get("avoid_friday_afternoon") and cls.check_friday_afternoon(event_time):
            return False
        
        # Check morning preference
        if constraints.get("prefer_mornings"):
            if event_time.hour < 9 or event_time.hour >= 12:
                return False
        
        return True


class MeetingDurationPredictor:
    """Predict meeting duration based on context"""
    
    # Duration rules based on meeting types
    DURATION_RULES = {
        "standup": 15,
        "daily": 15,
        "sync": 30,
        "1:1": 30,
        "one-on-one": 30,
        "pairing": 60,
        "review": 45,
        "demo": 45,
        "planning": 60,
        "sprint": 60,
        "all-hands": 60,
        "town hall": 60,
        "retrospective": 60,
        "retro": 60,
        "interview": 60,
        "call": 30,
        "meeting": 30,
        "workshop": 90,
        "training": 90,
        "session": 60,
    }
    
    # Base duration per attendee (minutes)
    ATTENDEE_BASE_TIME = 5
    
    @classmethod
    def predict_duration(cls, title: str, attendee_count: int = 1) -> int:
        """Predict meeting duration in minutes"""
        title_lower = title.lower()
        
        # Check for exact matches
        for keyword, duration in cls.DURATION_RULES.items():
            if keyword in title_lower:
                # Add time for additional attendees
                extra_time = min(attendee_count * cls.ATTENDEE_BASE_TIME, 30)
                return min(duration + extra_time, 240)  # Cap at 4 hours
        
        # Default duration
        return 30 + min(attendee_count * cls.ATTENDEE_BASE_TIME, 30)


class OptimalTimeFinder:
    """Find optimal time slots for meetings"""
    
    @classmethod
    def find_available_slots(cls, events: List[Dict[str, Any]], 
                           date: datetime,
                           duration_minutes: int,
                           constraints: Dict[str, Any],
                           num_slots: int = 3) -> List[Dict[str, Any]]:
        """Find top N available time slots"""
        slots = []
        
        work_start = constraints.get("work_start", 9)
        work_end = constraints.get("work_end", 17)
        buffer = constraints.get("buffer_minutes", 15)
        
        # Expand events with buffer
        buffered_events = SchedulingConstraints.expand_with_buffer(events, buffer)
        
        # Check each hour of the day
        current = date.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=work_end, minute=0, second=0, microsecond=0)
        
        while current + timedelta(minutes=duration_minutes) <= end_of_day:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check constraints
            if (SchedulingConstraints.is_within_working_hours(slot_start, slot_end, constraints) and
                SchedulingConstraints.is_available(slot_start, slot_end, buffered_events, 0)):
                
                # Score the slot
                score = cls._score_slot(slot_start, constraints, events)
                
                slots.append({
                    "start": slot_start,
                    "end": slot_end,
                    "score": score
                })
            
            current += timedelta(minutes=30)  # Check every 30 min
        
        # Sort by score and return top N
        slots.sort(key=lambda x: x["score"], reverse=True)
        return slots[:num_slots]
    
    @classmethod
    def _score_slot(cls, slot_time: datetime, constraints: Dict[str, Any],
                   events: List[Dict[str, Any]]) -> float:
        """Score a time slot (higher is better)"""
        score = 100.0
        
        # Prefer mornings if not preferred
        if not constraints.get("prefer_mornings", True):
            if slot_time.hour < 12:
                score += 20
        
        # Prefer times with less context switching
        hour = slot_time.hour
        if 9 <= hour < 11 or 14 <= hour < 16:
            score += 15
        
        # Nearby events check
        nearby_count = 0
        for event in events:
            event_start = event.get("start")
            if isinstance(event_start, str):
                event_start = datetime.fromisoformat(event_start)
            
            hours_diff = abs((event_start - slot_time).total_seconds() / 3600)
            if hours_diff < 2:
                nearby_count += 1
        
        # Prefer isolated slots
        score -= nearby_count * 5
        
        return max(score, 0)


class SchedulingEngine:
    """Main scheduling engine that coordinates all components"""
    
    def __init__(self, user_preferences: Dict[str, Any] = None):
        self.constraints = SchedulingConstraints.get_user_constraints(
            user_preferences or {}
        )
    
    def suggest_time_slots(self, events: List[Dict[str, Any]], 
                          date_str: str,
                          meeting_title: str,
                          attendee_count: int = 1) -> List[Dict[str, Any]]:
        """Generate recommended time slots"""
        # Parse date
        try:
            target_date = datetime.fromisoformat(date_str)
        except:
            target_date = datetime.utcnow()
        
        # Predict duration
        duration = MeetingDurationPredictor.predict_duration(meeting_title, attendee_count)
        
        # Find slots
        return OptimalTimeFinder.find_available_slots(
            events, target_date, duration, self.constraints, num_slots=3
        )
    
    def create_with_constraints(self, event_data: Dict[str, Any], 
                               events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create event with constraint validation"""
        start = event_data.get("start_time")
        end = event_data.get("end_time")
        
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        
        # Check working hours
        if not SchedulingConstraints.is_within_working_hours(start, end, self.constraints):
            return {
                "status": "conflict",
                "message": "Event is outside working hours",
                "suggestion": self.suggest_time_slots(events, start.date().isoformat(), 
                                                     event_data.get("summary", "meeting"))
            }
        
        # Check buffer/availability
        buffer = self.constraints.get("buffer_minutes", 15)
        if not SchedulingConstraints.is_available(start, end, events, buffer):
            return {
                "status": "conflict",
                "message": "Time slot conflicts with existing meeting",
                "suggestion": self.suggest_time_slots(events, start.date().isoformat(),
                                                     event_data.get("summary", "meeting"))
            }
        
        return {
            "status": "ok",
            "message": "Event passes all constraints"
        }
    
    def resolve_conflict(self, events: List[Dict[str, Any]], 
                        priority: str,
                        new_event_start: datetime,
                        new_event_end: datetime) -> Tuple[bool, str, Optional[Dict]]:
        """Resolve scheduling conflict based on priority"""
        if priority == SchedulingConstraints.PRIORITY_HIGH:
            # High priority - find alternative time
            suggestions = self.suggest_time_slots(
                events, 
                new_event_start.date().isoformat(),
                "meeting"
            )
            return False, "High priority - use suggested times instead", suggestions[0] if suggestions else None
        
        elif priority == SchedulingConstraints.PRIORITY_LOW:
            # Low priority - can be moved
            return True, "Low priority event will be rescheduled", None
        
        else:
            # Medium - ask user
            return False, "Medium priority - please confirm", None