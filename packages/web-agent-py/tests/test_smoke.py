"""Smoke tests for web agent."""
import subprocess
import glob
import os
import sys
from pathlib import Path


def test_smoke():
    """Test that agent can run and create success flag."""
    # Get project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent.parent
    
    # Change to project root for execution
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run agent with example task
        result = subprocess.run([
            sys.executable,
            'packages/web-agent-py/agent.py',
            'packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml'
        ], capture_output=True, text=True, timeout=120)
        
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # Check for success flags
        runs = sorted(glob.glob('runtime/sessions/*/success.flag'))
        assert runs, 'No successful run created'
        
        # Verify evidence was created
        latest_run = Path(runs[-1]).parent
        assert (latest_run / 'evidence').exists(), 'Evidence directory not created'
        assert (latest_run / 'run.json').exists(), 'Manifest not created'
        assert (latest_run / 'reasoning.jsonl').exists(), 'Reasoning log not created'
        
        # Check for screenshots
        screenshots = list((latest_run / 'evidence').glob('*.png'))
        assert screenshots, 'No screenshots captured'
        
        # Check for selectors.json
        assert (latest_run / 'evidence' / 'selectors.json').exists(), 'Selectors not captured'
        
    finally:
        os.chdir(original_dir)


if __name__ == '__main__':
    test_smoke()
    print("✅ Smoke test passed!")
