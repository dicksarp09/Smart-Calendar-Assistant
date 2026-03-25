"""
Evaluation Metrics for Calendar Agent
Implements various metrics to evaluate agent performance
"""

from typing import Dict, Any, List, Optional


def evaluate_tool_choice(predicted: Optional[str], expected: Optional[str]) -> float:
    """
    Evaluate if the correct tool was selected.
    
    Args:
        predicted: The tool that was actually used
        expected: The tool that should have been used
        
    Returns:
        1.0 if correct, 0.0 otherwise
    """
    if not predicted or not expected:
        return 0.0
    return 1.0 if predicted.lower() == expected.lower() else 0.0


def evaluate_params(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    """
    Evaluate parameter extraction accuracy.
    
    Args:
        predicted: The parameters that were predicted
        expected: The expected parameters
        
    Returns:
        Score between 0.0 and 1.0
    """
    if not expected:
        return 1.0  # No params to check
    
    if not predicted:
        return 0.0
    
    correct = 0
    total = len(expected)
    
    for key in expected:
        if key in predicted:
            pred_val = str(predicted[key]).lower()
            exp_val = str(expected[key]).lower()
            if pred_val == exp_val:
                correct += 1
    
    return correct / total if total > 0 else 1.0


def evaluate_success(response: Dict[str, Any]) -> float:
    """
    Evaluate if the execution was successful.
    
    Args:
        response: The response from the agent
        
    Returns:
        1.0 if successful, 0.0 otherwise
    """
    if not response:
        return 0.0
    
    # Check for explicit success indicators
    if response.get("status") == "success":
        return 1.0
    
    # Check for error indicators
    if response.get("error") or response.get("action_taken", "").endswith("_failed"):
        return 0.0
    
    # Check if response contains actual content
    if response.get("response"):
        # Make sure it's not an error message
        error_indicators = ["error", "failed", "couldn't", "sorry", "trouble"]
        response_lower = response.get("response", "").lower()
        if any(indicator in response_lower for indicator in error_indicators):
            return 0.0
        return 1.0
    
    return 0.0


def instruction_following(response_text: str, expected_keywords: List[str]) -> float:
    """
    Evaluate if the response follows instructions by checking for expected keywords.
    
    Args:
        response_text: The response from the agent
        expected_keywords: List of keywords that should be in the response
        
    Returns:
        Score between 0.0 and 1.0
    """
    if not expected_keywords or not response_text:
        return 1.0
    
    response_lower = response_text.lower()
    matches = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
    
    return matches / len(expected_keywords)


def trajectory_efficiency(trajectory: List[str]) -> int:
    """
    Calculate the number of steps in the agent trajectory.
    
    Args:
        trajectory: List of steps taken by the agent
        
    Returns:
        Number of steps
    """
    return len(trajectory) if trajectory else 0


def calculate_overall_score(
    tool_score: float,
    param_score: float,
    success_score: float,
    latency: float,
    max_latency: float = 10.0
) -> Dict[str, float]:
    """
    Calculate overall evaluation score.
    
    Args:
        tool_score: Tool choice accuracy (0-1)
        param_score: Parameter extraction accuracy (0-1)
        success_score: Execution success (0-1)
        latency: Response time in seconds
        max_latency: Maximum acceptable latency for scoring
        
    Returns:
        Dictionary with individual and overall scores
    """
    # Latency score (1.0 if under max, scales down otherwise)
    latency_score = max(0.0, 1.0 - (latency / max_latency))
    
    # Overall weighted score
    overall = (
        tool_score * 0.35 +  # Tool choice is most important
        param_score * 0.25 +  # Parameters matter
        success_score * 0.30 +  # Success is critical
        latency_score * 0.10    # Latency is nice to have
    )
    
    return {
        "tool_score": tool_score,
        "param_score": param_score,
        "success_score": success_score,
        "latency_score": latency_score,
        "overall_score": overall
    }
