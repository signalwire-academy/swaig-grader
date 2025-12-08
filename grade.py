#!/usr/bin/env python3
"""
SWAIG Grader - Grade SignalWire AI Agent submissions.
"""

import argparse
import json
import subprocess
import sys
import yaml
from pathlib import Path


def run_swaig_test(agent_file, args=None, timeout=30, agent_class=None):
    """Run swaig-test command."""
    cmd = ["swaig-test", agent_file]
    if agent_class:
        cmd.extend(["--agent-class", agent_class])
    cmd.extend(args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout exceeded"
    except Exception as e:
        return 1, "", str(e)


def check_instantiate(agent_file, config):
    """Check if agent loads without errors."""
    agent_class = config.get("agent_class")
    code, stdout, stderr = run_swaig_test(agent_file, ["--list-tools"], agent_class=agent_class)
    return code == 0, stderr if code != 0 else ""


def check_swml_valid(agent_file, config):
    """Check if SWML is valid."""
    agent_class = config.get("agent_class")
    code, stdout, stderr = run_swaig_test(agent_file, ["--dump-swml", "--raw"], agent_class=agent_class)
    if code != 0:
        return False, stderr
    try:
        swml = json.loads(stdout)
        # Check required paths
        for req in config.get("require", []):
            path = req.get("path", "")
            if not check_path_exists(swml, path):
                return False, f"Missing: {path}"
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"


def check_path_exists(data, path):
    """Check if a dot-notation path exists."""
    parts = path.replace("[", ".").replace("]", "").split(".")
    current = data
    for part in parts:
        if not part:
            continue
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return False
        else:
            return False
    return True


def check_function_exists(agent_file, config):
    """Check if a function is registered."""
    agent_class = config.get("agent_class")
    code, stdout, stderr = run_swaig_test(agent_file, ["--list-tools"], agent_class=agent_class)
    if code != 0:
        return False, stderr
    func_name = config.get("function", "")
    if func_name in stdout:
        return True, ""
    return False, f"Function '{func_name}' not found"


def check_exec(agent_file, config):
    """Execute a function and check output."""
    agent_class = config.get("agent_class")
    func = config.get("function", "")
    args = config.get("args", {})

    cmd_args = ["--exec", func]
    for key, value in args.items():
        cmd_args.extend([f"--{key}", str(value)])

    code, stdout, stderr = run_swaig_test(agent_file, cmd_args, agent_class=agent_class)
    if code != 0:
        return False, stderr

    # Check expected output
    expect = config.get("expect", {})
    stdout_lower = stdout.lower()

    for substring in expect.get("stdout_contains", []):
        if substring.lower() not in stdout_lower:
            return False, f"Output missing: {substring}"

    return True, ""


def check_swml_contains(agent_file, config):
    """Check if SWML output contains specific text."""
    agent_class = config.get("agent_class")
    code, stdout, stderr = run_swaig_test(agent_file, ["--dump-swml", "--raw"], agent_class=agent_class)
    if code != 0:
        return False, stderr

    # Check for required text strings
    for req in config.get("require", []):
        text = req.get("text", "")
        if text and text not in stdout:
            return False, f"SWML missing: {text}"

    return True, ""


CHECK_HANDLERS = {
    "instantiate": check_instantiate,
    "swml_valid": check_swml_valid,
    "function_exists": check_function_exists,
    "exec": check_exec,
    "swml_contains": check_swml_contains,
}


def grade(agent_file, config_file):
    """Run grading and return results."""
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    assignment = config.get("assignment", {})
    checks = config.get("checks", [])
    feedback = config.get("feedback", {})
    
    results = {
        "assignment": assignment,
        "checks": [],
        "score": 0,
        "max_score": 0,
        "percentage": 0.0,
        "passed": False,
        "feedback": []
    }
    
    for check in checks:
        check_type = check.get("type", "")
        handler = CHECK_HANDLERS.get(check_type)
        
        if not handler:
            result = {
                "id": check.get("id", ""),
                "name": check.get("name", ""),
                "max_points": check.get("points", 0),
                "points": 0,
                "passed": False,
                "output": f"Unknown check type: {check_type}"
            }
        else:
            passed, output = handler(agent_file, check)
            result = {
                "id": check.get("id", ""),
                "name": check.get("name", ""),
                "max_points": check.get("points", 0),
                "points": check.get("points", 0) if passed else 0,
                "passed": passed,
                "output": output
            }
        
        results["checks"].append(result)
        if not result["passed"] and result["output"]:
            results["feedback"].append(f"**{result['name']}**: {result['output']}")
    
    # Calculate totals
    results["max_score"] = sum(c["max_points"] for c in results["checks"])
    results["score"] = sum(c["points"] for c in results["checks"])
    results["percentage"] = round(
        results["score"] / results["max_score"] * 100, 1
    ) if results["max_score"] > 0 else 0
    
    passing_score = assignment.get("passing_score", 70)
    results["passed"] = results["percentage"] >= passing_score
    
    # Add pass/fail feedback
    if results["passed"]:
        results["feedback"].insert(0, feedback.get("pass", "Passed!"))
    else:
        results["feedback"].insert(0, feedback.get("fail", "Not yet passing."))
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Grade SWAIG agent submission")
    parser.add_argument("--agent", required=True, help="Path to agent.py")
    parser.add_argument("--config", required=True, help="Path to grading.yaml")
    parser.add_argument("--output", default="results.json", help="Output file")
    args = parser.parse_args()
    
    if not Path(args.agent).exists():
        print(f"Error: Agent file not found: {args.agent}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.config).exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    
    results = grade(args.agent, args.config)
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"Score: {results['score']}/{results['max_score']} ({results['percentage']}%)")
    print(f"Status: {'PASSED' if results['passed'] else 'NOT PASSING'}")
    
    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
