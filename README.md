# Custom Web Agent Browser Doer

Autonomous web browser agent using Playwright for deterministic web automation and evidence collection.

## Overview

This project implements a complete web automation agent that can:
- Navigate websites autonomously
- Use robust selector strategies (ARIA → Role → Text → CSS → XPath)
- Generate evidence packs (screenshots, DOM, HAR, selector maps, reasoning logs)
- Execute tasks from YAML/JSON specifications
- Provide a Streamlit UI for reviewing evidence

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sfboss/custom_web_agent_browser_doer.git
cd custom_web_agent_browser_doer
```

2. Run the bootstrap script:
```bash
./scripts/bootstrap_py.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Install Playwright browsers

3. Activate the virtual environment:
```bash
source .venv/bin/activate
```

### Running Tasks

Execute a task from the command line:

```bash
# Using the helper script
./scripts/run_task.sh packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

# Or directly with Python
python packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml
```

### Viewing Evidence

Start the Streamlit UI to review evidence packs:

```bash
streamlit run packages/web-agent-ui/app.py
```

Then open your browser to `http://localhost:8501`

## Project Structure

```
.
├── AGENTS.md                         # Complete specification
├── .env.example                      # Environment variables template
├── Makefile                          # Convenience targets
├── packages/
│   ├── web-agent-py/                 # Python agent implementation
│   │   ├── agent.py                  # Main agent loop
│   │   ├── planner.py                # Task decomposition
│   │   ├── tools/                    # Browser + utilities
│   │   │   ├── browser.py            # Playwright orchestration
│   │   │   ├── selectors.py          # Robust selector builders
│   │   │   └── storage.py            # Evidence pack writer
│   │   ├── prompts/                  # System prompts
│   │   ├── tasks/examples/           # Example task specs
│   │   ├── tests/                    # Test suite
│   │   └── pyproject.toml            # Package config
│   └── web-agent-ui/                 # Streamlit evidence viewer
│       ├── app.py
│       └── requirements.txt
├── runtime/
│   ├── sessions/                     # Task execution results
│   └── cache/
└── scripts/                          # Helper scripts
    ├── bootstrap_py.sh               # Setup script
    ├── run_task.sh                   # Task runner
    └── tree.sh                       # Directory tree viewer
```

## Task Specification

Tasks are defined in YAML or JSON format. Example:

```yaml
version: 1
id: find_salesforce_pricing
goal: Navigate to Salesforce and find the pricing page
start:
  url: "https://www.salesforce.com/"
extract:
  selectors:
    - name: PricingCTA
      strategies:
        - aria: "Pricing"
        - text: "Pricing"
        - css: "a[href*='pricing']"
actions:
  - id: a1
    type: goto
    target: ${start.url}
  - id: a2
    type: wait_for
    condition: network_idle
  - id: a3
    type: find_and_click
    target_selector_names: [PricingCTA]
  - id: a4
    type: capture
    what: [screenshot, dom, har]
```

See `packages/web-agent-py/tasks/examples/` for more examples.

## Evidence Pack

Each task execution creates a timestamped session directory containing:

- `evidence/*.png` - Screenshots at each step
- `evidence/dom_after_action.html` - DOM snapshots
- `evidence/network.har` - Network traffic recording
- `evidence/selectors.json` - Selector attempts and results
- `reasoning.jsonl` - Step-by-step execution log (JSONL)
- `run.json` - Manifest with checksums and metadata
- `success.flag` - Present if task completed successfully

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
AGENT_HEADLESS=true        # Run browser in headless mode
AGENT_MAX_STEPS=30         # Maximum steps per task
AGENT_TIMEOUT_MS=12000     # Default timeout in milliseconds
AGENT_CAPTURE_EVIDENCE=true # Capture evidence at each step
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest packages/web-agent-py/tests -v

# Run smoke test only
pytest packages/web-agent-py/tests/test_smoke.py -v
```

## Development

### Using Make

The Makefile provides convenient targets:

```bash
make setup    # Initial setup (venv + dependencies + browsers)
make test     # Run tests
make run      # Run example task
make ui       # Start Streamlit UI
make clean    # Clean runtime sessions
```

### Creating New Tasks

1. Create a YAML file in `packages/web-agent-py/tasks/examples/`
2. Define the goal, start URL, selectors, and actions
3. Run the task: `./scripts/run_task.sh path/to/your-task.yaml`
4. Review evidence in the UI

## Architecture

The agent follows a deterministic execution model:

1. **Plan** - Load task specification
2. **Act** - Execute actions sequentially
3. **Observe** - Capture browser state
4. **Reason** - Log decisions and results
5. **Decide** - Check success criteria
6. **Finish** - Generate evidence pack

### Selector Strategy Priority

1. ARIA roles and labels
2. Visible text
3. Data test IDs
4. CSS selectors
5. XPath expressions

The agent tries each strategy in order until one succeeds.

## License

See repository for license information.

## Contributing

Contributions are welcome! Please see the repository for guidelines.

## Acknowledgments

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [Streamlit](https://streamlit.io/) - Evidence viewer UI
- Python 3.12+
