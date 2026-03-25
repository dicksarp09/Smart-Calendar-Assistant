"""
Evaluation Dataset for Calendar Agent
Contains test cases with ground truth for evaluation
"""

# Test cases for evaluating the calendar agent
# Each case has input, expected tool, and optionally expected parameters
eval_cases = [
    # ============ CREATE EVENTS ============
    {
        "id": 1,
        "input": "Schedule meeting tomorrow at 10am",
        "expected_tool": "create_event",
        "expected_params": {
            "time": "10:00"
        },
        "category": "create"
    },
    {
        "id": 2,
        "input": "Add dentist appointment Friday 2pm",
        "expected_tool": "create_event",
        "expected_params": {
            "day": "friday",
            "time": "14:00"
        },
        "category": "create"
    },
    {
        "id": 3,
        "input": "Create meeting Monday 10am",
        "expected_tool": "create_event",
        "expected_params": {
            "day": "monday",
            "time": "10:00"
        },
        "category": "create"
    },
    {
        "id": 4,
        "input": "Book haircut Saturday morning",
        "expected_tool": "create_event",
        "expected_params": {
            "day": "saturday",
            "time": "09:00"
        },
        "category": "create"
    },
    {
        "id": 5,
        "input": "Add doctor visit next week",
        "expected_tool": "create_event",
        "expected_params": {
            "time": "09:00"  # default time
        },
        "category": "create"
    },
    
    # ============ QUERY EVENTS ============
    {
        "id": 6,
        "input": "What's on my calendar today?",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 7,
        "input": "What's on my calendar tomorrow?",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 8,
        "input": "Show my weekly overview",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 9,
        "input": "What do I have this week?",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 10,
        "input": "Any events next week?",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 11,
        "input": "Do I have a meeting on Friday?",
        "expected_tool": "get_events",
        "category": "query"
    },
    {
        "id": 12,
        "input": "What's scheduled for March 27?",
        "expected_tool": "get_events",
        "category": "query"
    },
    
    # ============ FREE TIME QUERIES ============
    {
        "id": 13,
        "input": "What are my free slots today?",
        "expected_tool": "get_events",
        "category": "free_time"
    },
    {
        "id": 14,
        "input": "When am I free this week?",
        "expected_tool": "get_events",
        "category": "free_time"
    },
    {
        "id": 15,
        "input": "Find me a free time tomorrow",
        "expected_tool": "get_events",
        "category": "free_time"
    },
    {
        "id": 16,
        "input": "Am I busy on Friday?",
        "expected_tool": "get_events",
        "category": "free_time"
    },
    
    # ============ EDGE CASES ============
    {
        "id": 17,
        "input": "What's my calendar like?",
        "expected_tool": "get_events",
        "category": "edge"
    },
    {
        "id": 18,
        "input": "Do I have anything scheduled?",
        "expected_tool": "get_events",
        "category": "edge"
    },
    {
        "id": 19,
        "input": "Show me all events",
        "expected_tool": "get_events",
        "category": "edge"
    },
    {
        "id": 20,
        "input": "What days have events?",
        "expected_tool": "get_events",
        "category": "edge"
    },
    {
        "id": 21,
        "input": "Any meetings this month?",
        "expected_tool": "get_events",
        "category": "edge"
    },
]


def get_cases_by_category(category: str = None):
    """Get test cases filtered by category"""
    if category:
        return [c for c in eval_cases if c.get("category") == category]
    return eval_cases


def get_case_count():
    """Get total number of test cases"""
    return len(eval_cases)


def get_categories():
    """Return list of all unique categories."""
    return list(set(case.get("category", "unknown") for case in eval_cases))
