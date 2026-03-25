"""Evaluation test that loads modules without app/__init__.py"""
import json
import sys
import os
import importlib.util

# Load modules directly without going through __init__
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load dataset directly
dataset = load_module('dataset', 'app/evaluation/dataset.py')

# Load metrics directly  
metrics = load_module('metrics', 'app/evaluation/metrics.py')

# Load evaluator - needs to import graph which has encoding fix
sys.path.insert(0, '.')

# Import the agent graph 
from app.agent.graph import create_agent_graph

# Create agent
agent_graph = create_agent_graph()

def run_test(input_text):
    """Run agent for a single test case"""
    import asyncio
    result = asyncio.run(agent_graph.ainvoke({
        "message": input_text,
        "user_id": "test_user"
    }))
    return result

# Run evaluation
eval_cases = dataset.eval_cases
results = []
passed = 0
failed = 0

print("=" * 60)
print("Calendar Agent Evaluation")
print("=" * 60)

for i, case in enumerate(eval_cases, 1):
    input_text = case["input"]
    expected_tool = case.get("expected_tool")
    
    print(f"\n[{i}] {input_text}")
    
    try:
        result = run_test(input_text)
        actual_tool = result.get('action_taken', 'unknown')
        
        # Evaluate
        tool_score = metrics.evaluate_tool_choice(actual_tool, expected_tool)
        success_score = metrics.evaluate_success(result)
        
        is_pass = tool_score == 1.0 and success_score == 1.0
        if is_pass:
            passed += 1
        else:
            failed += 1
            
        print(f"  Tool: {actual_tool} vs {expected_tool} -> {tool_score}")
        print(f"  Status: {'PASS' if is_pass else 'FAIL'}")
        
        results.append({
            "id": case.get("id", i),
            "input": input_text,
            "expected_tool": expected_tool,
            "actual_tool": actual_tool,
            "tool_correct": tool_score == 1.0,
            "success": success_score == 1.0
        })
    except Exception as e:
        print(f"  ERROR: {e}")
        failed += 1

# Summary
total = len(eval_cases)
print("\n" + "=" * 60)
print(f"SUMMARY: {passed}/{total} passed ({(passed/total*100):.1f}%)")
print("=" * 60)

# Save results
output = {
    "summary": {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "success_rate": passed / total
    },
    "results": results
}

with open("app/evaluation/results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to app/evaluation/results.json")
