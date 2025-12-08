# SWAIG Grader

Reusable GitHub Action for grading SignalWire AI Agent assignments using the `swaig-test` CLI.

## Features

- Automated grading of agent submissions
- Multiple check types (instantiate, SWML validation, function execution, etc.)
- Support for multi-agent files with `--agent-class`
- Per-check file targeting for complex assignments
- GitHub Issue integration for results posting
- Next assignment links on perfect scores
- Manual review mode for practical exams
- Artifact upload for grading results

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
    # Skip grading on template repos
    if: |
      github.actor != 'github-classroom[bot]' &&
      !startsWith(github.repository, 'signalwire-academy/template-') &&
      !startsWith(github.repository, 'signalwire-academy/agents-sdk-')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Grade submission
        uses: signalwire-academy/swaig-grader@v1
        with:
          solution-file: solution/agent.py
          grading-config: tests/grading.yaml
          next-assignment: https://classroom.github.com/a/XXXXXX
```

### Practical Exam Workflow

For practical exams that require manual instructor review:

```yaml
- name: Grade practical exam
  uses: signalwire-academy/swaig-grader@v1
  with:
    solution-file: solution/agent.py
    grading-config: tests/grading.yaml
    requires-manual-review: 'true'
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `solution-file` | Path to student solution file | `solution/agent.py` |
| `grading-config` | Path to grading YAML config | `tests/grading.yaml` |
| `python-version` | Python version to use | `3.11` |
| `post-results` | Post results to GitHub Issue | `true` |
| `fail-on-not-passing` | Fail workflow if not passing | `false` |
| `next-assignment` | GitHub Classroom link for next assignment (shown on 100%) | `''` |
| `requires-manual-review` | Tag for manual review instead of auto-closing | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `score` | Points earned |
| `max-score` | Maximum possible points |
| `percentage` | Percentage score |
| `passed` | Boolean pass status (`true`/`false`) |
| `results-json` | Full results as JSON string |

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

### `instantiate`

Verifies the agent loads without errors.

```yaml
- id: loads
  name: "Agent loads successfully"
  points: 10
  type: instantiate
```

### `swml_valid`

Verifies the agent generates valid SWML JSON with required structure.

```yaml
- id: swml
  name: "Valid SWML output"
  points: 10
  type: swml_valid
```

With path validation:

```yaml
- id: swml
  name: "SWML has AI section"
  points: 10
  type: swml_valid
  require:
    - path: "sections.main[0].ai"
```

### `swml_contains`

Checks if SWML output contains specific text strings.

```yaml
- id: has_fillers
  name: "Has speech fillers configured"
  points: 5
  type: swml_contains
  require:
    - text: "speech_fillers"
```

### `function_exists`

Verifies a named SWAIG function is registered.

```yaml
- id: has_func
  name: "Has get_order_status function"
  points: 10
  type: function_exists
  function: get_order_status
```

### `exec`

Executes a function with arguments and checks output.

```yaml
- id: test_order
  name: "Order lookup returns correct data"
  points: 20
  type: exec
  function: get_order_status
  args:
    order_number: "12345"
  expect:
    stdout_contains:
      - shipped
      - "12345"
```

### `multi_agent`

Verifies multiple agent classes exist in a file.

```yaml
- id: has_agents
  name: "Has all required agents"
  points: 15
  type: multi_agent
  agents:
    - GatewayAgent
    - SalesAgent
    - SupportAgent
```

## Advanced Configuration

### Per-Check File Targeting

For assignments with multiple files, specify the file per check:

```yaml
checks:
  - id: gateway_loads
    name: "Gateway agent loads"
    points: 10
    type: instantiate
    file: solution/gateway_agent.py
    agent_class: GatewayAgent

  - id: support_loads
    name: "Support agent loads"
    points: 10
    type: instantiate
    file: solution/support_agent.py
    agent_class: SupportAgent
```

### Agent Class Selection

For files with multiple agent classes:

```yaml
- id: test_sales
  name: "Sales agent pricing function"
  points: 15
  type: exec
  file: solution/multi_agent.py
  agent_class: SalesAgent
  function: get_pricing
  args:
    plan: basic
  expect:
    stdout_contains:
      - "$9.99"
```

## CLI Usage

The grader can also be run locally for testing:

```bash
python grade.py --agent solution/agent.py --config tests/grading.yaml --output results.json
```

## Issue Behavior

- **First run**: Creates a new issue with `grading` label
- **Subsequent runs**: Adds comments to existing grading issue
- **On pass**: Adds `passed` label
- **On 100%** (non-manual-review): Closes the issue, shows next assignment link
- **Manual review mode**: Adds `needs-review` label, keeps issue open

## License

MIT
