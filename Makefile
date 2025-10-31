.PHONY: setup test run ui clean

setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e packages/web-agent-py && pip install -r packages/web-agent-ui/requirements.txt && python -m playwright install

test:
	pytest packages/web-agent-py/tests -q

run:
	python3 packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

ui:
	streamlit run packages/web-agent-ui/app.py

clean:
	rm -rf runtime/sessions/*
