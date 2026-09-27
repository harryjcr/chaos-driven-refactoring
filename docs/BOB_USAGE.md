# How IBM Bob 2.0 is used

Bob 2.0 is both the development partner that builds CDR and the primary runtime repair agent.
During a live run, IBM Bob Shell reads the cloned target repository, applies the resilience fix,
and the runner verifies the resulting service under the identical chaos scenario. watsonx.ai
Granite and deterministic rules remain fallbacks for mock or Bob-unavailable runs.

## Bob Shell (headless automation)

Bob Shell 2.x brings Bob to the terminal and is used for scripted, evidence-producing tasks.

```powershell
# install (Windows)
powershell -c "irm -Uri https://bob.ibm.com/download/bobshell.ps1 | iex"   # choose npm

# authenticate with an Inference API key
[Environment]::SetEnvironmentVariable('BOB_API_KEY', '<key>', 'User')

# run a headless task and capture JSON evidence in bob_sessions/
powershell -ExecutionPolicy Bypass -File scripts/bob-task.ps1 `
  -Name "queue-unit-tests" -MaxCost 2 `
  -Prompt "Work in this repository root. Add runner/tests/test_queue.py ... "
```

`scripts/bob-task.ps1` wraps `bob run --trust --accept-license --format json --mode agent
--max-cost <n>` and stores the full JSON result (task id, duration, Bobcoins spent, tool calls,
final message) as `bob_sessions/bobshell-<name>-<timestamp>.json`.

Budget tracking: every task runs with an explicit `--max-cost`; the JSON evidence records
`session_costs` so the team can keep the 50-Bobcoin trial budget under control. Tasks completed
so far are indexed in `bob_sessions/README.md`.

## Where Bob sits in the "analyze a repository" flow

Bob 2.0 participates in both planes:

| Plane | Tool | Role |
| --- | --- | --- |
| Development (build time) | **IBM Bob 2.0 (IDE + Shell)** | Implements the submission form, `/api/runs` route, Supabase queue, `cdr watch` worker and every pipeline module; reviews and debugs the result. Evidence: `bob_sessions/`. |
| Runtime (analysis time) | **IBM Bob Shell (default) / watsonx Granite (alternative)** | The worker shallow-clones the submitted repository and Bob runs one agent session that reads the real code, identifies where the failure class originates in that codebase and applies the minimal fix. The patch shown in the dashboard is the real `git diff` of Bob's edits; `target_files` and `files_changed` come from git, so they always exist in the repository. Each session consumes Bobcoins and the run stores `bob_task_id` and `bobcoins` for the diagnosis and the patch. If `BOB_API_KEY` is absent, the pipeline falls back to a plan-mode analysis with watsonx Granite or deterministic rules and a template patch. |

Analyzer selection (`CDR_ANALYZER`): `auto` (default: Bob → watsonx → rules), `bob`, `watsonx`
or `rules`. Guardrails: `CDR_BOB_MAX_COST` caps the Bobcoins spent per analysis and
`CDR_CLONE_REPOS=0` disables repository cloning.

When the dashboard queues a repo URL, the worker (built with Bob) clones it, Bob performs the
repository-aware diagnosis and the resulting patch is verified by re-running the chaos scenario.
During judging, show Bob implementing this exact flow in the exported sessions and the demo
video — that is the "application of technology" evidence.

## Feature mapping

| Bob 2.0 capability | Where it is used in CDR |
| --- | --- |
| **Agent mode** | End-to-end implementation of the runner pipeline (models → telemetry → classifier → diagnoser → patcher → verifier) and the dashboard pages |
| **Parallel tasks** | Dashboard workstream and runner workstream advanced simultaneously; infra compose/k6/Toxiproxy developed in parallel with the Supabase schema |
| **Subagents** | Scoped work: Go/Python diff templates per failure category, k6 script, SQL policies, README/docs passes |
| **Document understanding** | Ingested the hackathon brief, the CDR context document, and the ChaosEater / AIOpsLab papers to keep the pitch and metrics aligned with the research state of the art |

## Workflow per phase

1. **Phase 1 — chaos capture**: Bob generates the compose subset, the k6 scenario and the
   Toxiproxy wiring; reviews the address graph (`checkoutservice → toxiproxy → emailservice`).
2. **Phase 2 — classification**: Bob implements the deterministic signal-to-category rules and
   their tests.
3. **Phase 3 — diagnosis**: Bob writes the watsonx client (IAM token flow, generation endpoint,
   blocked-model guard) and the rule-based fallback.
4. **Phase 4 — patch + verification**: Bob composes the diff templates per category, the
   verification math and the Supabase sink.
5. **Control room**: Bob builds the Next.js pages, charts and mock data fallback.

## Exporting task sessions for judging (mandatory)

For every relevant task, in Bob IDE:

1. Open **Views → More Actions → History** and confirm the correct project workspace.
2. Select the task; open the task header to show the **task session consumption summary**.
3. Screenshot the summary (Bobcoins used) and save it into `bob_sessions/`.
4. Use **Export task history** to download the markdown file and store it in `bob_sessions/`.
5. Repeat for all tasks that contributed to the submission.

Naming convention and rules: `bob_sessions/README.md`.

## Bobcoin budget plan

Each participant receives **40 Bobcoins**. Plan before the event starts:

- Reserve ~60% for phase 1–4 implementation tasks (the core of the submission).
- Reserve ~25% for dashboard and infra parallel tasks.
- Keep ~15% for debugging and final polish before the video recording.
- Prefer subagents for well-scoped work; avoid re-prompting large agent sessions for small fixes.

## Compliance reminders

- Remove all credentials and API keys before exporting sessions into the repository.
- Do not use out-of-scope watsonx models (blocked in `runner/cdr/config.py`).
- The repository is MIT-licensed and every artifact is original work from this team.
