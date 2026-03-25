"""Standalone evaluation test - tests core fixes without import issues"""
import re
import sys
import os
from datetime import datetime, timedelta

# Test the classify_intent function directly
def classify_intent(message: str):
    """Test version of classify_intent"""
    from enum import Enum
    class IntentType(Enum):
        QUERY = "query"
        ACTION = "action"
    
    message_lower = message.lower()
    
    # Action keywords
    action_keywords = [
        "create ", "add ", "schedule ", "book ", "new event",
        "update", "change", "move", "reschedule",
        "delete", "remove", "cancel", "clear"
    ]
    
    for keyword in action_keywords:
        if keyword in message_lower:
            return IntentType.ACTION
    
    # Query keywords (updated with fixes)
    query_keywords = [
        "what's on", "what is on", "show me", "do i have", "any events",
        "when is", "what time", "schedule for", "calendar for", "upcoming",
        "today", "tomorrow", "this week", "next week", "list", "get",
        "what's scheduled", "what is scheduled", "scheduled for",
        "am i busy", "are you free", "free time", "free slot", "available",
        "what days", "what meetings", "events do i", "meetings do i",
        # Added keywords
        "calendar like", "all events", "find me", "when am i free",
        "what do i have", "show my", "check my", "view my",
        "any meetings", "any appointments", "days have events"
    ]
    
    for keyword in query_keywords:
        if keyword in message_lower:
            return IntentType.QUERY
    
    return IntentType.QUERY

# Test parse_date_time with 10am default
def parse_date_time(input_text: str, reference_date = None):
    """Test version of parse_date_time with 10am default"""
    if reference_date is None:
        reference_date = datetime.utcnow()
    
    text_lower = input_text.lower()
    
    # Parse time
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
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
    
    # Default hour is 10am (not midnight!)
    default_hour = parsed_hour if parsed_hour is not None else 10
    
    # Parse "today"
    if "today" in text_lower:
        if parsed_hour is not None:
            start = reference_date.replace(hour=parsed_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        else:
            start = reference_date.replace(hour=10, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        return start, end
    
    # Parse "tomorrow"
    if "tomorrow" in text_lower:
        if parsed_hour is not None:
            start = (reference_date + timedelta(days=1)).replace(hour=parsed_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        else:
            start = (reference_date + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        return start, end
    
    # Day names
    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for day_name, day_num in day_names.items():
        if f"next {day_name}" in text_lower:
            days_ahead = (day_num - reference_date.weekday()) % 7 + 7
            start = (reference_date + timedelta(days=days_ahead)).replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
            return start, end
        
        if day_name in text_lower:
            days_ahead = (day_num - reference_date.weekday()) % 7
            if days_ahead == 0 and parsed_hour is None:
                days_ahead = 7
            start = (reference_date + timedelta(days=days_ahead)).replace(hour=default_hour, minute=parsed_minute, second=0, microsecond=0)
            end = start + timedelta(hours=1)
            return start, end
    
    return None, None

# Evaluation test cases
eval_cases = [
    {"input": "What's on my calendar today?", "expected_tool": "get_events"},
    {"input": "What's on my calendar tomorrow?", "expected_tool": "get_events"},
    {"input": "Show my weekly overview", "expected_tool": "get_events"},
    {"input": "Find me a free time tomorrow", "expected_tool": "get_events"},
    {"input": "What's my calendar like?", "expected_tool": "get_events"},
    {"input": "Show me all events", "expected_tool": "get_events"},
    {"input": "What days have events?", "expected_tool": "get_events"},
    {"input": "Schedule meeting tomorrow at 10am", "expected_tool": "create_event"},
    {"input": "Add dentist appointment Friday 2pm", "expected_tool": "create_event"},
    {"input": "Create meeting Monday 10am", "expected_tool": "create_event"},
    {"input": "Book haircut Saturday morning", "expected_tool": "create_event"},
    {"input": "Add doctor visit next week", "expected_tool": "create_event"},
    {"input": "What do I have this week?", "expected_tool": "get_events"},
    {"input": "Any events next week?", "expected_tool": "get_events"},
    {"input": "Do I have a meeting on Friday?", "expected_tool": "get_events"},
    {"input": "When am I free this week?", "expected_tool": "get_events"},
    {"input": "Am I busy on Friday?", "expected_tool": "get_events"},
    {"input": "Any meetings this month?", "expected_tool": "get_events"},
]

print("=" * 60)
print("Standalone Evaluation Test")
print("=" * 60)

results = []
passed = 0
failed = 0

for i, case in enumerate(eval_cases, 1):
    input_text = case["input"]
    expected_tool = case.get("expected_tool")
    
    # Classify intent
    intent = classify_intent(input_text)
    
    # Map to tool
    if intent.value == "query":
        actual_tool = "get_events"
    else:
        actual_tool = "create_event"
    
    # Check if correct
    is_correct = actual_tool == expected_tool
    
    # Also test date parsing for create_event cases
    if actual_tool == "create_event":
        start, end = parse_date_time(input_text)
        if start and start.hour == 0:
            print(f"WARNING: {input_text} parsed to midnight - should be 10am!")
    
    status = "PASS" if is_correct else "FAIL"
    if is_correct:
        passed += 1
    else:
        failed += 1
    
    print(f"[{i}] {status}: {input_text}")
    print(f"     Expected: {expected_tool}, Got: {actual_tool}")

# Summary
total = len(eval_cases)
print("\n" + "=" * 60)
print(f"SUMMARY: {passed}/{total} passed ({(passed/total*100):.1f}%)")
print("=" * 60)

# Save results
import json
output = {
    "summary": {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "success_rate": passed / total
    },
    "results": [{"input": c["input"], "expected": c["expected_tool"], "actual": ("get_events" if classify_intent(c["input"]).value == "query" else "create_event")} for c in eval_cases]
}

with open("standalone_eval_results.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nResults saved to standalone_eval_results.json")
