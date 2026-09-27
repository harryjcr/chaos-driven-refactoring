# Deployment

## Components

| Component | Platform | Notes |
| --- | --- | --- |
| Dashboard | Vercel | Root directory: `dashboard/` |
| Database, realtime, storage | Supabase | Free tier is enough for the demo |
| Runner | Local machine with Docker Desktop | IBM Cloud Code Engine as a stretch deployment |
| AI repair | IBM Bob Shell | Primary repository-aware repair path; Bobcoins capped per run |

## 1. Supabase

1. Create a project at supabase.com and open the SQL editor.
2. Run `supabase/migrations/0001_init.sql`. It creates an isolated `cdr` schema (useful when
   sharing a Supabase project with other applications) plus RLS policies and grants.
3. Expose the schema in PostgREST: project settings → API → Exposed schemas, add `cdr`.
4. Collect the project URL, the `anon` key (dashboard) and the `service_role` key (runner only).

## 2. Dashboard on Vercel

1. Import `LuisRz1/chaos-driven-refactoring` in Vercel.
2. Set the root directory to `dashboard/`.
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_SUPABASE_SCHEMA` (defaults to `cdr`)
4. Deploy. Without Supabase variables the dashboard falls back to deterministic demo data, so the
   URL always renders.

## 3. Runner

```bash
cd runner
python -m venv .venv
.venv/Scripts/activate
pip install -e .
cp ../.env.example .env   # then fill in only what you need
python -m cdr doctor
```

Environment variables:

| Variable | Purpose |
| --- | --- |
| `BOB_API_KEY`, `BOB_BINARY` | enable IBM Bob repair through Bob Shell |
| `WATSONX_API_KEY`, `WATSONX_PROJECT_ID` | enable Granite diagnosis (otherwise rule-based fallback) |
| `WATSONX_MODEL_ID` | must stay within hackathon scope (`ibm/granite-3-8b-instruct` by default) |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | sync runs to the control room |
| `SUPABASE_SCHEMA` | exposed schema for run tables (defaults to `cdr`) |
| `CDR_GITHUB_REPO`, `GITHUB_TOKEN` | target for generated PRs (`--create-pr`) |
| `CDR_DOCKER_BINARY`, `CDR_K6_BINARY` | override live tool paths |
| `CDR_LIVE_BASE_URL`, `CDR_TOXIPROXY_URL` | override live lab endpoints |

## 4. Chaos lab (live mode)

```bash
cd runner
python -m cdr run --scenario scenarios/checkout-latency-cascade.yaml --mode live --sink all
```

The runner starts Compose, executes k6, injects and removes the Toxiproxy fault, builds the real
Bob-patched checkoutservice image and repeats the experiment. Docker Desktop and k6 must already
be installed, and Bob Shell must be authenticated with `BOB_API_KEY`. Live mode fails before
starting chaos when Bob is unavailable, so a successful live run is always attributable to a real
Bob patch. Fault injection and manual cleanup commands are documented in `infra/README.md`.

## 5. IBM Cloud Code Engine (stretch)

The runner is container-ready: package `runner/` with a slim Python image, push to IBM Cloud
Container Registry and deploy a job/app in Code Engine using the hackathon-provisioned account
and credits. Keep watsonx credentials in Code Engine secrets, never in the repository.

## Security checklist

- Never commit `.env` files or credentials. IBM scans submission repositories and deactivates
  accounts that leak Bob or IBM Cloud credentials.
- The service role key is server-side only (runner); the dashboard uses the anon key with RLS.
- Out-of-scope watsonx models are blocked in code (`runner/cdr/config.py`).
- Generated PRs are opt-in via `--create-pr`.
