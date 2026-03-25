"""Quick test to verify tool selection fixes"""
import sys
sys.path.insert(0, 'c:/Users/Dickson/Desktop/Calendar Intelligence')

from app.evaluation.evaluator import run_agent_sync

# Test cases that were failing before
test_cases = [
    "What's on my calendar today?",
    "What's on my calendar tomorrow?",
    "Show my weekly overview",
    "Find me a free time tomorrow",
    "What's my calendar like?",
    "Show me all events",
    "What days have events?",
]

print("Testing tool selection fixes...")
print("-" * 50)

for test in test_cases:
    result = run_agent_sync(test)
    tool = result['tool']
    action = result.get('action_taken', 'N/A')
    status = "PASS" if tool == "get_events" else "FAIL"
    print(f"{status}: '{test}'")
    print(f"   Tool: {tool}, Action: {action}")
    print()
