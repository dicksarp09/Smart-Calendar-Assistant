"""
Multi-Person Scheduling Module
Handles attendee availability, round-robin, and meeting clustering
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict


class AttendeeAvailability:
    """Handle attendee availability checking"""
    
    @classmethod
    def find_mutually_available_slots(cls, 
                                      attendees: List[Dict[str, Any]],
                                      date: datetime,
                                      duration_minutes: int) -> List[Dict[str, Any]]:
        """Find time slots where all attendees are available"""
        # This would typically fetch free/busy from Google Calendar
        # For now, we simulate based on existing events
        
        all_events = []
        for attendee in attendees:
            events = attendee.get("events", [])
            all_events.extend(events)
        
        # Find slots that work for everyone
        available_slots = []
        work_start = 9
        work_end = 17
        
        current = date.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=work_end, minute=0, second=0, microsecond=0)
        
        while current + timedelta(minutes=duration_minutes) <= end_of_day:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if all attendees are free
            is_free = True
            for event in all_events:
                event_start = event.get("start")
                event_end = event.get("end")
                
                if isinstance(event_start, str):
                    event_start = datetime.fromisoformat(event_start)
                if isinstance(event_end, str):
                    event_end = datetime.fromisoformat(event_end)
                
                if slot_start < event_end and slot_end > event_start:
                    is_free = False
                    break
            
            if is_free:
                available_slots.append({
                    "start": slot_start,
                    "end": slot_end,
                    "attendees": len(attendees)
                })
            
            current += timedelta(minutes=30)
        
        return available_slots
    
    @classmethod
    def suggest_attendees(cls, 
                         possible_attendees: List[Dict[str, Any]],
                         required_count: int,
                         events: List[Dict[str, Any]],
                         date: datetime) -> List[Dict[str, Any]]:
        """Suggest best attendees based on availability"""
        availability_scores = []
        
        for attendee in possible_attendees:
            # Calculate how many events they have on the given date
            attendee_events = [
                e for e in events 
                if e.get("attendee_email") == attendee.get("email")
            ]
            
            score = 100 - (len(attendee_events) * 10)  # Fewer events = better
            availability_scores.append((attendee, score))
        
        # Sort by availability
        availability_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [att for att, _ in availability_scores[:required_count]]


class RoundRobinScheduler:
    """Handle fair distribution of meetings"""
    
    def __init__(self):
        self.meeting_history = defaultdict(list)  # user_id -> list of meeting times
    
    def record_meeting(self, user_id: datetime, meeting_time: datetime):
        """Record that a meeting was scheduled"""
        self.meeting_history[user_id].append(meeting_time)
    
    def get_fair_slot(self, 
                     participants: List[str],
                     preferred_date: datetime,
                     duration_minutes: int) -> Optional[datetime]:
        """Find slot that distributes meetings fairly"""
        
        # Count recent meetings for each participant
        recent_cutoff = datetime.utcnow() - timedelta(days=14)
        
        meeting_counts = {}
        for participant in participants:
            count = sum(
                1 for t in self.meeting_history[participant] 
                if t > recent_cutoff
            )
            meeting_counts[participant] = count
        
        # Find least booked participant and prioritize their available times
        min_meetings = min(meeting_counts.values()) if meeting_counts else 0
        least_booked = [p for p, c in meeting_counts.items() if c == min_meetings]
        
        # Return first available slot on preferred date
        work_start = 9
        work_end = 17
        
        current = preferred_date.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_of_day = preferred_date.replace(hour=work_end, minute=0, second=0, microsecond=0)
        
        while current + timedelta(minutes=duration_minutes) <= end_of_day:
            return current
        
        return None


class MeetingClustering:
    """Group meetings to reduce calendar fragmentation"""
    
    @classmethod
    def cluster_meetings(cls, 
                        events: List[Dict[str, Any]], 
                        max_days: int = 5) -> List[List[datetime]]:
        """Group events by day to minimize fragmentation"""
        
        # Group events by day
        day_events = defaultdict(list)
        
        for event in events:
            start = event.get("start")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            
            day_key = start.date()
            day_events[day_key].append(event)
        
        # Calculate scores for each day
        day_scores = []
        for day, day_evts in day_events.items():
            # More events on a day = better clustering potential
            score = len(day_evts)
            day_scores.append((day, score))
        
        # Sort by score descending
        day_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top days as clusters
        return [day for day, _ in day_scores[:max_days]]
    
    @classmethod
    def suggest_day_for_new_meeting(cls,
                                   events: List[Dict[str, Any]],
                                   preferred_days: List[int] = None) -> Optional[datetime]:
        """Suggest best day to add a new meeting"""
        
        if preferred_days is None:
            preferred_days = [0, 1, 2, 3, 4]  # Mon-Fri
        
        # Count events per day
        day_counts = defaultdict(int)
        
        for event in events:
            start = event.get("start")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            
            if start.weekday() in preferred_days:
                day_counts[start.date()] += 1
        
        # Find day with least events
        if not day_counts:
            # Default to next weekday
            today = datetime.utcnow()
            next_day = today + timedelta(days=1)
            while next_day.weekday() not in preferred_days:
                next_day += timedelta(days=1)
            return next_day
        
        least_booked_day = min(day_counts.items(), key=lambda x: x[1])[0]
        return datetime.combine(least_booked_day, datetime.min.time())


class ContextAwareScheduler:
    """Apply context-aware scheduling rules"""
    
    # Default context rules
    DEFAULT_RULES = {
        "avoid_friday_afternoon": True,
        "prefer_mornings": True,
        "avoid_monday_morning": False,  # People are catching up
        "preserve_lunch_break": True,  # Block 12-1pm
    }
    
    @classmethod
    def apply_rules(cls, 
                   start: datetime, 
                   end: datetime,
                   rules: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Check if time slot follows context rules"""
        
        if rules is None:
            rules = cls.DEFAULT_RULES
        
        # Check Friday afternoon
        if rules.get("avoid_friday_afternoon"):
            if start.weekday() == 4 and start.hour >= 14:
                return False, "Friday afternoons should be avoided"
        
        # Check Monday morning
        if rules.get("avoid_monday_morning"):
            if start.weekday() == 0 and start.hour < 10:
                return False, "Monday mornings should be avoided"
        
        # Check lunch break
        if rules.get("preserve_lunch_break"):
            lunch_start = start.replace(hour=12, minute=0)
            lunch_end = start.replace(hour=13, minute=0)
            if start < lunch_end and end > lunch_start:
                return False, "Preserve lunch break (12-1pm)"
        
        # Check working hours
        if start.hour < 9 or end.hour > 17:
            return False, "Outside working hours"
        
        return True, "OK"
    
    @classmethod
    def get_recommended_times(cls, date: datetime) -> List[Tuple[int, int]]:
        """Get recommended time ranges for a given date"""
        
        if date.weekday() == 4:  # Friday
            return [(9, 12), (14, 16)]
        elif date.weekday() == 0:  # Monday
            return [(10, 12), (14, 17)]
        else:
            return [(9, 12), (14, 17)]  # Default: mornings and afternoons