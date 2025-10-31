#!/bin/bash
# Run a task with the web agent

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <task_file.yaml>"
    echo "Example: $0 packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml"
    exit 1
fi

TASK_FILE="$1"

if [ ! -f "$TASK_FILE" ]; then
    echo "Error: Task file not found: $TASK_FILE"
    exit 1
fi

echo "🚀 Running task: $TASK_FILE"
echo ""

# Use python3 from PATH or virtual environment if activated
PYTHON=${PYTHON:-python3}

$PYTHON packages/web-agent-py/agent.py "$TASK_FILE"
