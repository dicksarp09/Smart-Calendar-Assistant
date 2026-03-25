"""
Mass Test Script for Calendar Agent
Tests 25 different questions to validate the agent functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 25 test questions covering different scenarios
TEST_QUESTIONS = [
    # Query questions
    "What events do I have today?",
    "What's on my calendar tomorrow?",
    "Show my weekly overview",
    "What do I have this week?",
    "Any events next week?",
    "Do I have a meeting on Friday?",
    "What's scheduled for March 27?",
    "List my upcoming events",
    "Show me today's schedule",
    "What meetings do I have?",
    
    # Action questions - create
    "Add dentist appointment Friday 2pm",
    "Schedule team standup every day at 9am",
    "Create meeting Monday 10am",
    "Book haircut Saturday morning",
    "Add doctor visit next week",
    
    # Questions about free time
    "What are my free slots today?",
    "When am I free this week?",
    "Find me a free time tomorrow",
    "Am I busy on Friday?",
    "What times are available next week?",
    
    # Edge cases
    "What's my calendar like?",
    "Do I have anything scheduled?",
    "Show me all events",
    "What days have events?",
    "Any meetings this month?",
]

def test_agent():
    """Run all 25 test questions against the agent"""
    print("=" * 60)
    print("Calendar Agent - Mass Testing")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Number of questions: {len(TEST_QUESTIONS)}")
    print("=" * 60)
    
    results = []
    passed = 0
    failed = 0
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/25] Question: {question}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/agent",
                json={"message": question},
                timeout=30
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get("response", "No response")
                action_taken = data.get("action_taken", "none")
                
                print(f"    Status: ✓ PASS ({response.status_code})")
                print(f"    Time: {elapsed:.2f}s")
                print(f"    Action: {action_taken}")
                print(f"    Response: {agent_response[:150]}...")
                
                passed += 1
                results.append({
                    "question": question,
                    "status": "PASS",
                    "status_code": response.status_code,
                    "action": action_taken,
                    "response": agent_response,
                    "time": elapsed
                })
            else:
                print(f"    Status: ✗ FAIL ({response.status_code})")
                print(f"    Error: {response.text[:100]}")
                
                failed += 1
                results.append({
                    "question": question,
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "error": response.text,
                    "time": elapsed
                })
                
        except requests.exceptions.Timeout:
            print(f"    Status: ✗ FAIL (Timeout)")
            failed += 1
            results.append({
                "question": question,
                "status": "FAIL",
                "error": "Request timeout",
                "time": 30
            })
        except Exception as e:
            print(f"    Status: ✗ FAIL ({str(e)[:50]})")
            failed += 1
            results.append({
                "question": question,
                "status": "FAIL",
                "error": str(e),
                "time": 0
            })
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Questions: {len(TEST_QUESTIONS)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(TEST_QUESTIONS)*100):.1f}%")
    print("=" * 60)
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: test_results.json")
    
    return results

if __name__ == "__main__":
    test_agent()
