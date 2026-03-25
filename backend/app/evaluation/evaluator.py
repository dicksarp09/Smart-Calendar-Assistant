"""
Evaluator for Calendar Agent
Runs the agent and captures results for evaluation
"""

import asyncio
import time
from typing import Dict, Any, Optional
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.graph import create_agent_graph


def run_agent_sync(input_text: str, user_id: str = "test_user") -> Dict[str, Any]:
    """
    Run the agent synchronously with the given input.
    
    Args:
        input_text: The user input to process
        user_id: The user ID to use
        
    Returns:
        Dictionary with response, tool used, parameters, status, and trajectory
    """
    from backend.app.agent.graph import create_agent_graph
    
    # Create agent graph
    agent_graph = create_agent_graph()
    
    # Track trajectory
    trajectory = []
    
    # Run agent
    start_time = time.time()
    
    try:
        result = asyncio.run(agent_graph.ainvoke({
            "message": input_text,
            "user_id": user_id
        }))
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Extract tool used from action_taken or message analysis
        action_taken = result.get("action_taken", "")
        response = result.get("response", "")
        
        # Map action_taken to tool name
        tool_map = {
            "create_event": "create_event",
            "update_event": "update_event",
            "delete_event": "delete_event",
            "get_events": "get_events",
            "create_event_failed": "create_event",
            "parse_failed": "none"
        }
        
        tool_used = tool_map.get(action_taken, action_taken if action_taken else "unknown")
        
        # If tool is unknown, try to detect from response
        if tool_used == "unknown" or tool_used == "":
            if response:
                # Check response for clues about what tool was used
                response_lower = response.lower()
                if any(word in response_lower for word in ["created", "created a new event", "event has been scheduled"]):
                    tool_used = "create_event"
                elif any(word in response_lower for word in ["here are your events", "you have", "found the following", "retrieved your events", "check your google calendar", "events on"]):
                    tool_used = "get_events"
        
        # Extract parameters if possible
        params = extract_params_from_response(result, input_text)
        
        return {
            "response": result.get("response", ""),
            "tool": tool_used,
            "params": params,
            "status": "success" if result.get("response") and "error" not in result.get("response", "").lower() else "failed",
            "trajectory": trajectory,
            "latency": latency,
            "action_taken": action_taken,
            "raw_response": result
        }
        
    except Exception as e:
        end_time = time.time()
        latency = end_time - start_time
        
        return {
            "response": f"Error: {str(e)}",
            "tool": "error",
            "params": {},
            "status": "failed",
            "trajectory": trajectory,
            "latency": latency,
            "error": str(e)
        }


def extract_params_from_response(result: Dict[str, Any], input_text: str) -> Dict[str, Any]:
    """
    Extract parameters from the agent response.
    
    Args:
        result: The agent result
        input_text: The original input
        
    Returns:
        Dictionary of extracted parameters
    """
    params = {}
    input_lower = input_text.lower()
    
    # Extract time
    time_patterns = ["9am", "10am", "11am", "12pm", "1pm", "2pm", "3pm", "4pm", "5pm"]
    for tp in time_patterns:
        if tp in input_lower:
            params["time"] = tp
    
    # Extract day
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day in days:
        if day in input_lower:
            params["day"] = day
    
    # Check for keywords
    if "tomorrow" in input_lower:
        params["day"] = "tomorrow"
    if "today" in input_lower:
        params["day"] = "today"
    if "next week" in input_lower:
        params["period"] = "next_week"
    if "this week" in input_lower:
        params["period"] = "this_week"
    
    return params


def run_agent_for_eval(input_text: str, user_id: str = "test_user") -> Dict[str, Any]:
    """
    Main entry point for running agent in evaluation.
    
    Args:
        input_text: The user input
        user_id: User ID
        
    Returns:
        Evaluation result dictionary
    """
    return run_agent_sync(input_text, user_id)
