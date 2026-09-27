# CDR — Chaos-Driven Refactoring

**Break the system on purpose. Ship the architecture that survives it.**

CDR closes the APM-to-code gap. Existing tools diagnose resilience problems in three silos that
never talk to each other: chaos engineering finds the failure, APM finds the root cause, and AI
coding agents write code — but only when a human asks. CDR runs the full loop autonomously:

1. **Inject chaos + capture the collapse** — k6 load and Toxiproxy faults against a real
   repository (Online Boutique) running in staging.
2. **Classify the root cause** — telemetry and logs mapped to a failure category with evidence
   (concurrency, memory leak, unresilient dependency, database saturation).
3. **Repair with repository context** — IBM Bob reads the affected service in a shallow clone,
   applies the minimal refactor and returns the real repository diff.
4. **Generate the PR and verify resilience** — the patch is applied and the exact same chaos
   scenario is re-executed to prove the system no longer collapses.

## Repository layout

| Path | Contents |
| --- | --- |
| `dashboard/` | Next.js 16 control room: run timeline, before/after telemetry, diagnosis, diff, verification |
| `runner/` | Python pipeline: live chaos, classification, IBM Bob repair, rebuild + verification |
| `infra/` | Staging lab: Online Boutique subset (Docker Compose), k6 load, Toxiproxy faults |
| `supabase/` | Postgres schema + RLS policies for run history |
| `bob_sessions/` | Exported IBM Bob 2.0 task histories (hackathon evidence) |
| `docs/` | Architecture, deployment, metrics, Bob usage, judging map, demo script |

## Quickstart

### Control room (mock data works out of the box)

```bash
cd dashboard
npm install
npm run dev          # http://localhost:3000
```

Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` to read live runs from
Supabase; without them the UI renders deterministic demo data.

### Submit a repository for analysis

Open the dashboard and use **Analyze a repository**: the run is queued in Supabase and executed
by the worker.

```bash
cd runner
python -m cdr watch          # processes queued analyses (mock mode by default)
python -m cdr watch --pace 6 # adds a pause per phase, useful to watch progress live
```

The API route needs `SUPABASE_SERVICE_ROLE_KEY` on Vercel (server-side only); the worker needs
`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` locally. The dashboard refreshes active runs every
5 seconds and shows a progress bar with the current phase (queued → chaos → classification →
diagnosis → verification). IBM Bob Shell is the primary runtime repair agent: it reads the cloned
repository, applies the real resilience diff and is required for live verification. watsonx Granite
and deterministic rules are fallback analyzers for mock runs — see `docs/BOB_USAGE.md`.

### Runner (no Docker required in mock mode)

```bash
cd runner
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode mock --sink all
```

### Chaos staging (live mode)

```bash
cd runner
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode live --sink all
```

See `infra/README.md` for fault injection commands, `docs/DEPLOYMENT.md` for the full environment
setup and [`docs/LIVE_EVIDENCE.md`](docs/LIVE_EVIDENCE.md) for the measured Bob repair.

## How IBM Bob 2.0 is used

Bob 2.0 is the development partner that builds CDR — agent mode for the core pipeline, parallel
tasks and subagents for dashboard/runner workstreams, and document understanding to digest the
research papers and hackathon brief. Every task session summary is exported to `bob_sessions/`
as required by the hackathon. Details: `docs/BOB_USAGE.md`.

## Metrics that matter

p95/p99 latency, error rate and time-to-collapse are captured before and after the fix under an
identical load profile; diagnosis time is compared against the manual SRE estimate. Definitions
and business-value framing: `docs/METRICS.md`.

## Hackathon

Built for the **IBM Bob 2.0 Hackathon** (lablab.ai, September 25–27, 2026). Judging criteria
mapping: `docs/JUDGING_MAP.md`.

## For AI agents and contributors

- [`AGENTS.md`](AGENTS.md) — complete agent guide: commands, verification steps, conventions,
  architecture summary, environment variables and gotchas.
- [`obsidian-vault/`](obsidian-vault/Home.md) — linked knowledge base ("brain"). Open the
  folder as an Obsidian vault or read the markdown: product, architecture, pipeline, operations,
  IBM Bob integration, hackathon context, roadmap and glossary.

## License

MIT — see `LICENSE`.
