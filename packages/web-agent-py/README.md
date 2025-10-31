# Web Agent Python

Autonomous web browser agent using Playwright for deterministic web automation.

## Features

- Browser automation with Playwright
- Robust selector strategies (ARIA → Role → Text → CSS → XPath)
- Evidence pack generation (screenshots, DOM, HAR, selector maps)
- Task-based execution from YAML/JSON specifications
- Deterministic and reproducible

## Installation

```bash
# Install package
pip install -e .

# Install Playwright browsers
python -m playwright install
```

## Usage

```bash
# Run a task
python agent.py tasks/examples/find_salesforce_pricing.yaml

# With environment variables
AGENT_HEADLESS=false python agent.py tasks/examples/find_salesforce_pricing.yaml
```

## Task Specification

Tasks are defined in YAML or JSON format. See `tasks/examples/` for examples.

## Evidence Pack

Each run creates a timestamped session directory in `runtime/sessions/` containing:

- `evidence/*.png` - Screenshots
- `evidence/dom_after_action.html` - DOM snapshots
- `evidence/network.har` - Network traffic
- `evidence/selectors.json` - Selector attempts and results
- `reasoning.jsonl` - Step-by-step execution log
- `run.json` - Manifest with checksums
- `success.flag` - Present if task completed successfully
