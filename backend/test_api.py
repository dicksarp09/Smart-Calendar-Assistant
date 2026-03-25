"""
Test script for the AI Calendar Agent API
Run this after setting up the backend with mock credentials
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

# Mock token for development testing
MOCK_TOKEN = "mock_test_user"

def get_headers():
    """Get headers with mock token"""
    return {
        "Authorization": f"Bearer {MOCK_TOKEN}",
        "Content-Type": "application/json"
    }

def test_root():
    """Test API root endpoint"""
    print("=" * 50)
    print("Testing: GET /")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_me():
    """Test /me endpoint"""
    print("\n" + "=" * 50)
    print("Testing: GET /me")
    response = requests.get(f"{BASE_URL}/me", headers=get_headers())
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_events():
    """Test /events endpoints"""
    print("\n" + "=" * 50)
    print("Testing: GET /events")
    
    # Calculate time range
    now = datetime.utcnow()
    time_min = now.isoformat()
    time_max = (now + timedelta(days=30)).isoformat()
    
    response = requests.get(
        f"{BASE_URL}/events",
        headers=get_headers(),
        params={"time_min": time_min, "time_max": time_max}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_agent():
    """Test /agent endpoint"""
    print("\n" + "=" * 50)
    print("Testing: POST /agent")
    
    agent_request = {
        "message": "What's on my calendar today?",
        "user_id": "test_user",
        "conversation_history": []
    }
    
    response = requests.post(
        f"{BASE_URL}/agent",
        headers=get_headers(),
        data=json.dumps(agent_request)
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("\n🚀 Starting API Tests...\n")
    
    tests = [
        ("Root Endpoint", test_root),
        ("User Endpoint (/me)", test_me),
        ("Get Events (/events)", test_events),
        ("AI Agent (/agent)", test_agent),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASSED" if result else "❌ FAILED"))
        except Exception as e:
            print(f"Error: {e}")
            results.append((name, f"❌ ERROR: {e}"))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    for name, result in results:
        print(f"{name}: {result}")
    
    passed = sum(1 for _, r in results if "PASSED" in r)
    print(f"\nTotal: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    run_all_tests()
