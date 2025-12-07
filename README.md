# SWAIG Grader

Reusable GitHub Action for grading SignalWire AI Agent assignments.

## Usage

In your assignment template's workflow:

```yaml
name: Grade Submission

on:
  push:
    branches: [main]
    paths:
      - 'solution/**'
  workflow_dispatch:

permissions:
  contents: read
  issues: write

jobs:
  grade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Grade submission
        uses: signalwire-academy/swaig-grader@v1
        with:
          solution-file: solution/agent.py
          grading-config: tests/grading.yaml
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `solution-file` | Path to student solution | `solution/agent.py` |
| `grading-config` | Path to grading YAML | `tests/grading.yaml` |
| `python-version` | Python version | `3.11` |
| `post-results` | Post to GitHub Issue | `true` |
| `fail-on-not-passing` | Fail workflow if not passing | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `score` | Points earned |
| `max-score` | Maximum points |
| `percentage` | Percentage score |
| `passed` | Boolean pass status |
| `results-json` | Full results as JSON |

## Grading Configuration

Create `tests/grading.yaml`:

```yaml
assignment:
  id: L1.7
  name: "Lab 1.7: Order Functions"
  level: 1
  type: lab
  passing_score: 70

checks:
  - id: instantiate
    name: "Agent Instantiation"
    points: 10
    type: instantiate
    file: solution/agent.py

  - id: swml_valid
    name: "SWML Generation"
    points: 10
    type: swml_valid

  - id: func_exists
    name: "Function: get_order_status"
    points: 15
    type: function_exists
    function: get_order_status

  - id: test_order
    name: "Test: Order lookup"
    points: 20
    type: exec
    function: get_order_status
    args:
      order_number: "12345"
    expect:
      stdout_contains:
        - shipped

feedback:
  pass: |
    Excellent work! All checks passed.
  fail: |
    Some checks failed. Review the details above.
```

## Check Types

| Type | Description |
|------|-------------|
| `instantiate` | Agent loads without errors |
| `swml_valid` | Generates valid SWML JSON |
| `swml_contains` | SWML contains required text |
| `function_exists` | Named function exists |
| `exec` | Execute function and check output |
| `multi_agent` | Multiple agents exist in file |

## License

MIT
