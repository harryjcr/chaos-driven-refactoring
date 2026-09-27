# CDR Runner

Orchestrates the Chaos-Driven Refactoring pipeline:

1. **Chaos injection + collapse capture** — load and fault injection against a real target repo in staging.
2. **Root cause classification** — telemetry and logs mapped to a failure category with evidence.
3. **Repository-aware repair** — IBM Bob edits a shallow clone and the real `git diff` becomes the patch.
4. **PR generation + resilience verification** — live mode rebuilds the affected service and re-runs the scenario.

## Quickstart

```bash
cd runner
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -e ".[dev]"

python -m cdr doctor
python -m cdr list-scenarios
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode mock --sink all
```

Mock mode simulates telemetry deterministically so the full pipeline, report generation and
dashboard sync can run without Docker, k6 or Toxiproxy. Live mode starts the Compose lab, records
custom k6 telemetry, injects a Toxiproxy fault, builds Bob's checkoutservice patch as a new image
and runs the identical experiment again. It requires an authenticated Bob Shell and fails closed
if Bob, a required tool or a real patch is missing.

## Configuration

Copy `.env.example` from the repository root and export the variables you need:

| Variable | Purpose |
| --- | --- |
| `BOB_API_KEY` / `BOB_BINARY` | enable IBM Bob repository repair through Bob Shell |
| `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` | enable IBM Granite diagnosis |
| `WATSONX_MODEL_ID` | model id, defaults to `ibm/granite-3-8b-instruct` |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | sync runs to the control room |
| `CDR_GITHUB_REPO` | target repository for generated PRs |
| `CDR_DOCKER_BINARY` / `CDR_K6_BINARY` | override live-mode tool paths |
| `CDR_LIVE_BASE_URL` / `CDR_TOXIPROXY_URL` | override live lab endpoints |

Only models allowed by the hackathon scope are accepted (see `cdr/config.py`).

## Tests

```bash
ruff check .
pytest
```
