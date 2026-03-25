"""
Learning and Adaptation Module
Tracks patterns, learns preferences, and improves suggestions over time
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import json


class PatternRecognition:
    """Recognize patterns from historical data"""
    
    @classmethod
    def analyze_meeting_patterns(cls, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze typical meeting patterns"""
        
        if not events:
            return {
                "typical_start_hour": 10,
                "typical_duration": 30,
                "preferred_days": [1, 2, 3, 4],  # Mon-Thu
                "busiest_hours": [10, 11, 14, 15],
            }
        
        # Analyze start times
        start_hours = []
        durations = []
        days = []
        
        for event in events:
            start = event.get("start")
            end = event.get("end")
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            
            start_hours.append(start.hour)
            durations.append((end - start).total_seconds() / 60)
            days.append(start.weekday())
        
        # Calculate averages
        avg_start_hour = sum(start_hours) / len(start_hours) if start_hours else 10
        avg_duration = sum(durations) / len(durations) if durations else 30
        
        # Find preferred days
        day_counts = defaultdict(int)
        for day in days:
            day_counts[day] += 1
        
        preferred_days = sorted(day_counts.keys(), key=lambda d: day_counts[d], reverse=True)[:4]
        
        # Find busiest hours
        hour_counts = defaultdict(int)
        for hour in start_hours:
            hour_counts[hour] += 1
        
        busiest_hours = sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:4]
        
        return {
            "typical_start_hour": round(avg_start_hour),
            "typical_duration": round(avg_duration),
            "preferred_days": preferred_days,
            "busiest_hours": busiest_hours,
        }
    
    @classmethod
    def detect_recurring_meetings(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect recurring meetings from history"""
        
        # Group by title
        title_events = defaultdict(list)
        
        for event in events:
            title = event.get("summary", "").lower()
            title_events[title].append(event)
        
        recurring = []
        
        for title, evts in title_events.items():
            if len(evts) < 3:
                continue
            
            # Sort by start time
            evts.sort(key=lambda e: e.get("start", ""))
            
            # Check for regular intervals
            intervals = []
            for i in range(1, len(evts)):
                prev = evts[i-1].get("start")
                curr = evts[i].get("start")
                
                if isinstance(prev, str):
                    prev = datetime.fromisoformat(prev)
                if isinstance(curr, str):
                    curr = datetime.fromisoformat(curr)
                
                interval = (curr - prev).days
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if 6 <= avg_interval <= 8:  # Weekly
                    recurring.append({
                        "title": title,
                        "interval": "weekly",
                        "count": len(evts)
                    })
                elif 28 <= avg_interval <= 32:  # Monthly
                    recurring.append({
                        "title": title,
                        "interval": "monthly",
                        "count": len(evts)
                    })
        
        return recurring


class PreferenceLearning:
    """Learn and adapt to user preferences"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.accepted_suggestions = []  # Suggestions user said yes to
        self.rejected_suggestions = []  # Suggestions user said no to
    
    def record_acceptance(self, suggestion: Dict[str, Any]):
        """Record that user accepted a suggestion"""
        self.accepted_suggestions.append({
            **suggestion,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def record_rejection(self, suggestion: Dict[str, Any], reason: str = None):
        """Record that user rejected a suggestion"""
        self.rejected_suggestions.append({
            **suggestion,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_learned_preferences(self) -> Dict[str, Any]:
        """Get learned preferences based on history"""
        prefs = {}
        
        # Analyze accepted suggestions
        if self.accepted_suggestions:
            start_hours = [s.get("hour") for s in self.accepted_suggestions if s.get("hour")]
            if start_hours:
                prefs["preferred_start_hour"] = round(sum(start_hours) / len(start_hours))
            
            # Preferred days
            days = [s.get("weekday") for s in self.accepted_suggestions if s.get("weekday") is not None]
            if days:
                prefs["preferred_days"] = list(set(days))
            
            # Duration preferences
            durations = [s.get("duration") for s in self.accepted_suggestions if s.get("duration")]
            if durations:
                prefs["preferred_duration"] = round(sum(durations) / len(durations))
        
        # Analyze rejected suggestions
        if self.rejected_suggestions:
            # Extract patterns from rejections
            rejection_reasons = [s.get("reason") for s in self.rejected_suggestions if s.get("reason")]
            
            if "friday" in str(rejection_reasons).lower():
                prefs["avoid_friday_afternoon"] = True
            
            if "morning" in str(rejection_reasons).lower():
                prefs["prefer_afternoons"] = True
        
        return prefs
    
    def adjust_recommendation_score(self, slot: Dict[str, Any]) -> float:
        """Adjust recommendation score based on learned preferences"""
        
        score = slot.get("score", 50)
        
        if not self.accepted_suggestions:
            return score
        
        # Boost hours that user typically accepts
        user_prefs = self.get_learned_preferences()
        
        if "preferred_start_hour" in user_prefs:
            pref_hour = user_prefs["preferred_start_hour"]
            slot_hour = slot.get("start", datetime.utcnow()).hour
            if abs(slot_hour - pref_hour) <= 1:
                score += 20
        
        return max(score, 0)


class ContextRulesEngine:
    """Apply context-aware scheduling rules from learned data"""
    
    def __init__(self):
        # Default rules
        self.rules = {
            "avoid_friday_afternoon": True,
            "prefer_mornings": True,
            "preserve_lunch_break": True,
            "avoid_monday_morning": False,
        }
    
    def load_rules_from_db(self, user_id: str, database):
        """Load custom rules from user memory"""
        try:
            import json
            rules_data = database.get_user_memory(user_id, "context_rules")
            if rules_data:
                self.rules.update(json.loads(rules_data))
        except:
            pass
    
    def save_rules_to_db(self, user_id: str, database):
        """Save rules to user memory"""
        try:
            import json
            database.set_user_memory(user_id, "context_rules", json.dumps(self.rules))
        except:
            pass
    
    def update_rule(self, rule_name: str, value: bool):
        """Update a specific rule"""
        self.rules[rule_name] = value
    
    def apply_to_slot(self, slot: datetime) -> Tuple[bool, str]:
        """Check if slot violates any rules"""
        
        # Check Friday afternoon
        if self.rules.get("avoid_friday_afternoon"):
            if slot.weekday() == 4 and slot.hour >= 14:
                return False, "Avoid Friday afternoons"
        
        # Check morning preference
        if self.rules.get("prefer_mornings"):
            if slot.hour >= 13:
                return False, "Prefer mornings"
        
        # Check lunch break
        if self.rules.get("preserve_lunch_break"):
            if 12 <= slot.hour < 13:
                return False, "Preserve lunch break"
        
        # Check Monday morning
        if self.rules.get("avoid_monday_morning"):
            if slot.weekday() == 0 and slot.hour < 10:
                return False, "Avoid Monday mornings"
        
        return True, "OK"
    
    def suggest_best_day(self, events: List[Dict[str, Any]]) -> datetime:
        """Suggest best day to schedule based on patterns"""
        
        if not events:
            # Default to next Tuesday
            today = datetime.utcnow()
            days_ahead = (1 - today.weekday() + 7) % 7 or 7
            return today + timedelta(days=days_ahead)
        
        patterns = PatternRecognition.analyze_meeting_patterns(events)
        
        # Prefer less busy days
        day_counts = defaultdict(int)
        for event in events:
            start = event.get("start")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            day_counts[start.date()] += 1
        
        # Find least booked day
        least_booked = min(day_counts.items(), key=lambda x: x[1])[0]
        return datetime.combine(least_booked, datetime.min.time())


class AdaptiveScheduler:
    """Main adaptive scheduler that combines all learning components"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.pattern_recognition = PatternRecognition()
        self.preference_learning = PreferenceLearning(user_id)
        self.context_rules = ContextRulesEngine()
    
    def optimize_suggestions(self, 
                           slots: List[Dict[str, Any]], 
                           events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize slot suggestions based on learning"""
        
        if not slots:
            return slots
        
        # Analyze patterns
        patterns = self.pattern_recognition.analyze_meeting_patterns(events)
        
        # Get learned preferences
        learned_prefs = self.preference_learning.get_learned_preferences()
        
        # Adjust scores
        optimized = []
        for slot in slots:
            adjusted_score = self.preference_learning.adjust_recommendation_score(slot)
            
            # Apply context rules
            slot_start = slot.get("start")
            if isinstance(slot_start, str):
                slot_start = datetime.fromisoformat(slot_start)
            
            is_valid, reason = self.context_rules.apply_to_slot(slot_start)
            if not is_valid:
                adjusted_score *= 0.1  # Heavily penalize invalid slots
            
            optimized.append({
                **slot,
                "score": adjusted_score,
                "reason": reason if not is_valid else None
            })
        
        # Sort by adjusted score
        optimized.sort(key=lambda x: x["score"], reverse=True)
        
        return optimized
    
    def suggest_for_meeting(self, 
                           meeting_title: str,
                           events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest optimal times for a new meeting"""
        
        from backend.scheduling.engine import MeetingDurationPredictor
        
        # Get duration
        duration = MeetingDurationPredictor.predict_duration(meeting_title)
        
        # Get available slots (simplified)
        # In production, this would use calendar integration
        suggestions = []
        
        # Generate suggestions for next 5 days
        for i in range(5):
            date = datetime.utcnow().date() + timedelta(days=i)
            
            # Simplified: suggest mornings
            for hour in [9, 10, 11, 14, 15]:
                start = datetime.combine(date, datetime.min.time().replace(hour=hour))
                end = start + timedelta(minutes=duration)
                
                suggestions.append({
                    "start": start,
                    "end": end,
                    "score": 50
                })
        
        return self.optimize_suggestions(suggestions, events)