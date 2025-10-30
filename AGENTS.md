# agents.md — Autonomous Web Browser Agent (Playwright)

**Purpose:** This document is the single source of truth for a local, repo‑first web agent that can autonomously open a real browser, navigate, discover/select DOM elements, act on them, verify outcomes, and produce a signed **evidence pack** (screens, DOM, HAR, selector map, reasoning log) proving it completed the task.

---

## 1) Repo Layout (deterministic)

```text
.
├─ agents.md                         # ← this file
├─ .env.example                      # environment variables template
├─ Makefile                          # convenience targets
├─ packages/
│  ├─ web-agent-py/                  # Python Playwright agent (reference impl)
│  │  ├─ agent.py                    # main agent loop
│  │  ├─ planner.py                  # task → plan decomposition
│  │  ├─ tools/                      # browser + generic tools
│  │  │  ├─ browser.py               # Playwright orchestration
│  │  │  ├─ selectors.py             # robust selector builders + heuristics
│  │  │  └─ storage.py               # evidence pack writer, hashing, signing
│  │  ├─ prompts/
│  │  │  ├─ system_planner.txt
│  │  │  └─ system_executor.txt
│  │  ├─ tasks/                      # input task specs (YAML/JSON)
│  │  │  └─ examples/*.yaml
│  │  ├─ tests/
│  │  │  └─ test_smoke.py
│  │  ├─ pyproject.toml
│  │  └─ README.md
│  └─ web-agent-ui/                  # Minimal Streamlit UI to run & review proofs
│     ├─ app.py
│     └─ requirements.txt
├─ runtime/
│  ├─ sessions/                      # all runs → timestamped folders
│  │  └─ 2025-10-30T17-05-12Z_run-001/
│  │     ├─ evidence/
│  │     │  ├─ 01_nav_home.png
│  │     │  ├─ 02_click_pricing.png
│  │     │  ├─ dom_after_action.html
│  │     │  ├─ network.har
│  │     │  └─ selectors.json        # keyed by action_id → selector details
│  │     ├─ reasoning.jsonl          # step-by-step chain with timestamps
│  │     ├─ run.json                 # metadata + hashed manifest
│  │     └─ success.flag             # zero-byte file = success
│  └─ cache/
└─ scripts/
   ├─ bootstrap_py.sh                # installs Playwright + deps
   ├─ run_task.sh                    # CLI wrapper for a task file
   └─ tree.sh                        # prints tree views for sanity checks
```

---

## 2) Quickstart

```bash
# 1) Python 3.10+ recommended
python -V

# 2) Create venv and install
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r packages/web-agent-ui/requirements.txt
pip install -e packages/web-agent-py

# 3) Install Playwright browsers
python -m playwright install

# 4) Copy env
cp .env.example .env

# 5) Smoke test
pytest packages/web-agent-py/tests -q

# 6) Run a task
./scripts/run_task.sh packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

# 7) Review evidence
./scripts/tree.sh runtime/sessions | less
streamlit run packages/web-agent-ui/app.py
```

---

## 3) Environment Variables (`.env.example`)

```ini
# Headless mode: true|false
AGENT_HEADLESS=true
# Max steps per task
AGENT_MAX_STEPS=30
# Default timeout (ms) for waits
AGENT_TIMEOUT_MS=12000
# Evidence: capture DOM/PNG/HAR at each step
AGENT_CAPTURE_EVIDENCE=true
# OpenAI/Claude style LLM (optional – agent can run w/out LLM using heuristics)
LLM_PROVIDER=none
LLM_MODEL=
LLM_API_KEY=
# Proxy (optional)
HTTP_PROXY=
HTTPS_PROXY=
```

---

## 4) Task Spec Schema (YAML)

**File:** `packages/web-agent-py/tasks/examples/*.yaml`

```yaml
version: 1
id: find_salesforce_pricing
goal: >-
  Navigate to https://www.salesforce.com and find the primary Pricing page CTA button.
  Click into Pricing, extract the button's selector(s), verify page title contains 'Pricing',
  then capture a screenshot and DOM, and return proof artifacts.
constraints:
  max_steps: 20
  site_allowlist:
    - "salesforce.com"
  block_dialogs: true
success_criteria:
  - Reached a URL that matches /pricing/i
  - Captured a screenshot of the pricing page
  - Collected at least one robust selector for the Pricing CTA
deliverables:
  - screenshot
  - dom
  - selector_map
  - har
  - reasoning_log
start:
  url: "https://www.salesforce.com/"
accommodations:
  # resilience knobs
  slow_network_ms: 0
  retries_per_action: 2
  wait_for_idle_network_ms: 2000
extract:
  selectors:
    - name: PricingCTA
      strategies:
        - aria: "Pricing"
        - text: "Pricing"
        - role: "link[name=/pricing/i]"
        - css: "a[href*='pricing']"
        - xpath: "//a[contains(translate(., 'PRICING', 'pricing'), 'pricing')]"
  fields:
    - name: PageTitle
      method: document.title
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
    type: assert
    condition: url_includes
    value: "pricing"
  - id: a5
    type: capture
    what: [screenshot, dom, har]
  - id: a6
    type: extract
    what: [PageTitle, PricingCTA]
```

> The agent accepts either YAML or JSON. Values are deterministic; no placeholders.

---

## 5) Agent Loop (deterministic autonomy)

**Phases:** `plan → act → observe → reason → decide → finish`

**Stop conditions:** success criteria met, max_steps reached, or repeated dead‑end.

**Pseudocode (Python):**

```python
for step in range(AGENT_MAX_STEPS):
    action = planner.next_action(state)
    observation = executor.run(action)
    evidence.capture(action, observation)
    state = reasoner.update(state, action, observation)
    if evaluator.satisfied(state, success_criteria):
        evidence.mark_success()
        break
```

---

## 6) Robust Selector Strategy

1. **Priority order:** ARIA → Role → Visible Text → Data‑Test‑ID → CSS → XPATH.
2. **Stabilizers:** requires visibility, attached to DOM, stable bounding box, click center.
3. **Heuristics:**

   * Prefer `getByRole(name=...)` and `getByText()` when available.
   * If multiple matches, score by proximity to heading/landmark, clickability, and element weight.
   * If shadow DOM, pierce using `evalOnSelectorAll` and composed path.
   * Re‑attempt with alternative strategy on failure; record all candidates in `selectors.json`.
4. **Proof:** For each click, store the exact selector used, outerHTML snippet, and a crop of the clicked area.

**Example (stored in `selectors.json`):**

```json
{
  "a3": {
    "name": "PricingCTA",
    "attempts": [
      {"strategy": "aria", "query": "Pricing", "ok": true},
      {"strategy": "css",  "query": "a[href*='pricing']", "ok": true}
    ],
    "final": {"strategy": "aria", "query": "Pricing"}
  }
}
```

---

## 7) Evidence Pack & Verification

Every run writes `runtime/sessions/<ts>_run-XXX/`:

* `evidence/*.png` — step‑level screenshots (and cropped target regions)
* `evidence/dom_after_action.html` — full DOM dump post action
* `evidence/network.har` — HAR for the run
* `evidence/selectors.json` — all candidate + chosen selectors
* `reasoning.jsonl` — compact JSONL; each line `{ts, step, action, thought, result}`
* `run.json` — parameters, git commit hash, env, timing, file checksums (SHA256)
* `success.flag` — existence means success

**Verifier script (concept):**

```bash
python - <<'PY'
import json,sys,os,glob
root = sys.argv[1]
assert os.path.exists(os.path.join(root,'success.flag'))
assert glob.glob(os.path.join(root,'evidence','*.png'))
with open(os.path.join(root,'evidence','selectors.json')) as f:
    s = json.load(f)
assert any(a.get('final') for a in s.values())
print('OK')
PY runtime/sessions/$(ls runtime/sessions | tail -1)
```

---

## 8) Minimal Reference Implementation (Python + Playwright)

**`packages/web-agent-py/tools/browser.py`** (excerpt):

```python
from playwright.sync_api import sync_playwright
import os, time

class Browser:
    def __init__(self, headless=True, timeout_ms=12000):
        self.headless = headless
        self.timeout = timeout_ms
        self.pw = None
        self.ctx = None
        self.page = None

    def __enter__(self):
        self.pw = sync_playwright().start()
        browser = self.pw.chromium.launch(headless=self.headless)
        self.ctx = browser.new_context(record_har_path=None)
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(self.timeout)
        return self

    def __exit__(self, *exc):
        if self.ctx: self.ctx.close()
        if self.pw: self.pw.stop()

    def goto(self, url: str):
        self.page.goto(url)

    def wait_network_idle(self, idle_ms=2000):
        self.page.wait_for_timeout(idle_ms)

    def screenshot(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.page.screenshot(path=path, full_page=True)

    def dump_dom(self, path: str):
        html = self.page.content()
        open(path,'w',encoding='utf-8').write(html)

    def find_click(self, selectors: list[dict]):
        # Try strategies in order
        for sel in selectors:
            try:
                st = sel['strategy']; q = sel['query']
                if   st == 'aria': el = self.page.get_by_role("link", name=q)
                elif st == 'text': el = self.page.get_by_text(q, exact=False)
                elif st == 'css':  el = self.page.locator(q).first
                elif st == 'xpath': el = self.page.locator(f"xpath={q}").first
                else: continue
                el.scroll_into_view_if_needed()
                el.click()
                return sel
            except Exception:
                continue
        raise RuntimeError('No selector strategy succeeded')
```

**`packages/web-agent-py/agent.py`** (excerpt):

```python
import os, json, time, yaml, hashlib, pathlib
from tools.browser import Browser

RUNTIME = pathlib.Path('runtime/sessions')

def sha256(p):
    import hashlib
    return hashlib.sha256(open(p,'rb').read()).hexdigest()

def run(task_path: str):
    task = yaml.safe_load(open(task_path)) if task_path.endswith('.yaml') else json.load(open(task_path))
    ts = time.strftime('%Y-%m-%dT%H-%M-%SZ', time.gmtime())
    out = RUNTIME / f"{ts}_run-001"
    ev  = out / 'evidence'; out.mkdir(parents=True, exist_ok=True); ev.mkdir(parents=True, exist_ok=True)

    with Browser(headless=os.getenv('AGENT_HEADLESS','true')=='true', timeout_ms=int(os.getenv('AGENT_TIMEOUT_MS','12000'))) as b:
        # a1: goto
        b.goto(task['start']['url'])
        b.wait_network_idle(task['accommodations'].get('wait_for_idle_network_ms', 2000))
        # a3: find_and_click
        strategies = task['extract']['selectors'][0]['strategies']
        chosen = b.find_click([{'strategy': s.split(':')[0], 'query': s.split(':',1)[1].strip()} if ':' in s else {'strategy': list(s.keys())[0], 'query': list(s.values())[0]} for s in [
            {'aria': 'Pricing'}, {'text': 'Pricing'}, {'css': "a[href*='pricing']"}
        ]])
        # capture
        b.screenshot(str(ev/ '02_after_click.png'))
        b.dump_dom(str(ev/ 'dom_after_action.html'))

    # manifest
    manifest = {
        'task_id': task['id'], 'evidence': sorted([str(p) for p in ev.glob('*')]),
    }
    open(out/'run.json','w').write(json.dumps(manifest, indent=2))
    # success flag
    open(out/'success.flag','w').close()
    print(out)

if __name__ == '__main__':
    import sys
    run(sys.argv[1])
```

**`packages/web-agent-ui/app.py`** (excerpt):

```python
import streamlit as st, json, glob
st.set_page_config(page_title='Web Agent Evidence Viewer', layout='wide')
root = 'runtime/sessions'
run_dirs = sorted(glob.glob(f"{root}/*/"))
st.sidebar.header('Runs')
choice = st.sidebar.selectbox('Pick run', run_dirs[::-1])
if choice:
    st.subheader(choice)
    cols = st.columns(2)
    pngs = sorted(glob.glob(f"{choice}/evidence/*.png"))
    for p in pngs:
        st.image(p, caption=p, use_column_width=True)
    st.download_button('Download selectors.json', data=open(f"{choice}/evidence/selectors.json","rb").read(), file_name='selectors.json')
```

---

## 9) Planner & Reasoner (LLM‑optional)

* **LLM‑free mode:** deterministic rules: if URL lacks `pricing` → search in‑page anchors; if none → open hamburger; retry alternative selectors; consider keyboard navigation.
* **LLM‑assisted mode:** supply compact state (URL, visible headings/links) to a small model; ask for next action and selector hypotheses. Ensure actions conform to a strict schema to avoid prompt‑drift.

**Action schema (JSON):**

```json
{
  "type": "click|goto|type|press|wait_for|assert|extract|capture",
  "target": "string (url or selector name)",
  "alt_selectors": [ {"strategy":"aria|text|css|xpath","query":"..."} ],
  "assert": {"kind":"url_includes|title_matches|element_exists","value":"..."}
}
```

---

## 10) CLI

```bash
# Run any task
python packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

# Run headful for debugging
AGENT_HEADLESS=false python packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

# Print trees (uses `tree` if present, else Python fallback)
./scripts/tree.sh .
```

---

## 11) Tests (Pytest smoke)

**`packages/web-agent-py/tests/test_smoke.py`** (concept):

```python
import subprocess, glob, os

def test_smoke():
    subprocess.check_call([
        'python','packages/web-agent-py/agent.py','packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml'
    ])
    runs = sorted(glob.glob('runtime/sessions/*/success.flag'))
    assert runs, 'no successful run created'
```

---

## 12) Hardening

* **Navigation guards:** allowlist domains; block dialogs/popups; enforce same‑tab.
* **Anti‑flakiness:** wait for `domcontentloaded` + visibility; retry with backoff; action timeouts.
* **Selector drift:** store `outerHTML` & bounding box; fall back to text contains; re‑score candidates.
* **Identity:** deterministic user‑agent; persistent context only when required.
* **Ethics:** respect robots.txt; no account creation or PII entry; rate‑limit interactions.

---

## 13) Example Tasks (drop‑in)

* `find_salesforce_pricing.yaml` — as above
* `find_salesforce_trust_status.yaml` — open `https://status.salesforce.com`, pick an instance by name (e.g., `NA115`), capture current status tile + selector map
* `find_github_repo_star_button.yaml` — open a known repo, capture the star button selector and click count

---

## 14) Makefile

```makefile
.PHONY: setup test run ui clean
setup:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e packages/web-agent-py && pip install -r packages/web-agent-ui/requirements.txt && python -m playwright install

test:
	pytest packages/web-agent-py/tests -q

run:
	python packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml

ui:
	streamlit run packages/web-agent-ui/app.py

clean:
	rm -rf runtime/sessions/*
```

---

## 15) What “Done” Looks Like (acceptance)

1. `success.flag` exists for the run.
2. `selectors.json` contains a `final` selector for each click action.
3. Evidence includes at least one full‑page screenshot + DOM + HAR.
4. `run.json` lists file checksums and git commit hash.
5. `pytest` smoke passes locally and in CI (GitHub Actions ubuntu‑latest).

---

## 16) Optional: MCP‑style Interface (future‑proof)

Expose the agent as a local JSON‑RPC or MCP server with two tools:

* `run_task(task_path)` → returns run folder & summary
* `last_runs(n)` → metadata for recent runs

This keeps the core usable from VS Code, web UIs, or other orchestrators.

---

## 17) Operational Tips

* Keep tasks tiny, domain‑scoped, and verifiable.
* Prefer ARIA/role selectors; treat CSS/XPath as fallbacks.
* Always capture proof first; then optimize speed.
* Use `AGENT_HEADLESS=false` when authoring new tasks.
* Commit `tasks/examples/*.yaml` to grow your library of web goals.

---

**End of agents.md**
