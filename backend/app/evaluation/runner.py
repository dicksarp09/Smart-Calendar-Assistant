"""
Evaluation Runner for Calendar Agent
Runs the evaluation pipeline and saves results
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.evaluation.dataset import eval_cases, get_case_count
from app.evaluation.evaluator import run_agent_for_eval
from app.evaluation.metrics import (
    evaluate_tool_choice,
    evaluate_params,
    evaluate_success,
    trajectory_efficiency,
    calculate_overall_score
)


def run_evaluation(output_path: str = None) -> Dict[str, Any]:
    """
    Run the complete evaluation pipeline.
    
    Args:
        output_path: Path to save results JSON file
        
    Returns:
        Dictionary with evaluation results and summary
    """
    print("=" * 60)
    print("Calendar Agent Evaluation Pipeline")
    print("=" * 60)
    print(f"Total test cases: {get_case_count()}")
    print("=" * 60)
    
    results = []
    total_cases = len(eval_cases)
    passed = 0
    failed = 0
    
    for i, case in enumerate(eval_cases, 1):
        case_id = case.get("id", i)
        input_text = case["input"]
        expected_tool = case.get("expected_tool")
        expected_params = case.get("expected_params", {})
        
        print(f"\n[{i}/{total_cases}] Testing: {input_text}")
        
        # Run agent
        result = run_agent_for_eval(input_text)
        
        # Evaluate
        tool_score = evaluate_tool_choice(result.get("tool"), expected_tool)
        param_score = evaluate_params(result.get("params"), expected_params)
        success_score = evaluate_success(result)
        traj_steps = trajectory_efficiency(result.get("trajectory", []))
        latency = result.get("latency", 0)
        
        # Calculate overall score
        scores = calculate_overall_score(tool_score, param_score, success_score, latency)
        
        # Determine pass/fail
        is_pass = tool_score == 1.0 and success_score == 1.0
        if is_pass:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
        
        print(f"    Tool: {result.get('tool')} (expected: {expected_tool}) - {'PASS' if tool_score == 1.0 else 'FAIL'}")
        print(f"    Status: {status} - Latency: {latency:.2f}s")
        
        # Build result record
        result_record = {
            "id": case_id,
            "input": input_text,
            "expected_tool": expected_tool,
            "actual_tool": result.get("tool"),
            "tool_correct": tool_score == 1.0,
            "param_score": param_score,
            "success": success_score == 1.0,
            "latency": latency,
            "trajectory_steps": traj_steps,
            "overall_score": scores["overall_score"],
            "response_preview": result.get("response", "")[:100]
        }
        
        results.append(result_record)
    
    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Cases: {total_cases}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total_cases*100):.1f}%")
    print("=" * 60)
    
    # Calculate aggregate metrics
    avg_latency = sum(r["latency"] for r in results) / len(results)
    avg_score = sum(r["overall_score"] for r in results) / len(results)
    tool_accuracy = sum(1 for r in results if r["tool_correct"]) / len(results)
    
    summary = {
        "total_cases": total_cases,
        "passed": passed,
        "failed": failed,
        "success_rate": passed / total_cases,
        "average_latency": avg_latency,
        "average_score": avg_score,
        "tool_accuracy": tool_accuracy,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Build final output
    output = {
        "summary": summary,
        "results": results
    }
    
    # Save to file
    if output_path:
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    return output


def run_evaluation_by_category(category: str, output_path: str = None) -> Dict[str, Any]:
    """
    Run evaluation for a specific category.
    
    Args:
        category: Category to filter by
        output_path: Path to save results
        
    Returns:
        Evaluation results
    """
    from backend.app.evaluation.dataset import get_cases_by_category
    
    filtered_cases = get_cases_by_category(category)
    print(f"Running {len(filtered_cases)} cases for category: {category}")
    
    # Temporarily replace eval_cases
    global eval_cases
    original_cases = eval_cases
    eval_cases = filtered_cases
    
    result = run_evaluation(output_path)
    
    # Restore original
    eval_cases = original_cases
    
    return result


if __name__ == "__main__":
    # Default output path
    output_file = os.path.join(
        os.path.dirname(__file__),
        "results.json"
    )
    
    # Run evaluation
    results = run_evaluation(output_file)
    
    print("\nDone! Evaluation complete!")
