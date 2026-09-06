# Relay — Job Evidence Desk

A read-only workspace for collecting real job listings, comparing quoted evidence against your chosen skills, and exporting a review you can inspect. The same service is available to MCP clients — not just the browser.

[Project walkthrough: user journey, dependencies and implementation steps](https://coder058.github.io/profile/projects/relay.html).

**[Open the workspace](https://relay-ten-zeta.vercel.app/)** · [Backend API](https://relay-backend-r3ux6b3uwa-ew.a.run.app/docs) · [MCP endpoint](https://relay-backend-r3ux6b3uwa-ew.a.run.app/tools/mcp)

## What you can actually do

- Read and filter the latest public Arbeitnow API page, with source and fetch time. This is limited board coverage, not a comprehensive search engine.
- Search uses whole tokens and explicit aliases: React does not match reactions, and SQL does not match MySQL. Literal mentions still need human interpretation.
- Count literal skill mentions across that bounded result and open every count back to its listing and quote lines. It is not a demand score or market estimate.
- Paste another listing, choose your own skills, and compare exact quotes with numbered normalized source text.
- Group canonical-URL duplicates while retaining alternate descriptions and their SHA-256 content fingerprints.
- Inspect literal wording about experience, location, compensation and work authorization. A mention can be optional, negated, or unrelated to a requirement; the app never decides eligibility.
- Export Markdown and a re-importable JSON workspace. Optionally save a device-local copy using an explicit button. Reviews are not stored in the application's database.
- Connect an actual MCP client using Streamable HTTP or stdio. No paid model or API key is required.

## Architecture and boundaries

React/TypeScript UI → stateless FastAPI job endpoints → deterministic evidence service and a fixed, bounded public-board reader. The official `mcp==2.1.1` Python SDK exposes those same services as `search_job_board`, `summarize_job_board`, `review_job_evidence`, and `export_job_review`.

The web UI uses HTTP, not an LLM pretending to operate tools. No arbitrary URL fetch, shell execution, private applicant database, application submission, credential handling or hiring score is part of this workflow. Board outages return an explicit error, never synthetic fallback vacancies. Large inputs are rejected before JSON parsing; MCP HTTP checks Host and Origin against an allowlist.

Source text is untrusted content. Browser rendering uses React text nodes, not raw HTML. A content hash identifies a snapshot, not its truth. Hosting can retain standard request metadata; do not paste CVs, credentials or private correspondence into this public service. Device-local storage is not private on a shared device.

The old fixture-based safety lab remains at `/#lab`. Its database, simulated providers, approvals and traces are **not connected to the job tools** and must not be described as production agent governance.

## Run locally

From `backend`, create/activate a Python virtual environment, install `requirements.txt`, then run `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. From `frontend`, run `npm ci` and `npm run dev`.

For stdio, launch `python -m app.mcp.jobs_server` from `backend` using that environment's interpreter. For HTTP, use `http://127.0.0.1:8000/tools/mcp`. Public deployment uses the endpoint linked above. Set `RELAY_CORS_ORIGINS` and `RELAY_MCP_HOSTS` to exact allowed frontend origins/backend hosts on a different deployment. `VITE_API_BASE_URL` selects the browser's backend API; otherwise Vite proxies locally.

### Connect from Cursor (local)

This is how a reviewer or a company engineer would attach the same tools to an MCP client. It is not a hosted customer install.

```json
{
  "mcpServers": {
    "relay": {
      "command": "python",
      "args": ["-m", "app.mcp.jobs_server"],
      "cwd": "/absolute/path/to/relay/backend"
    }
  }
}
```

Point `command` at the virtualenv interpreter that has `requirements.txt` installed. The tools are read-only. They do not apply to jobs, store CVs or fetch arbitrary URLs.

## Verification and limits

[Observed job-search walkthrough](JOB_SEARCH_WALKTHROUGH.md): a real query,
an unsuitable first result, a revised query and source-preserving export.
This is maintainer testing, not user-adoption evidence.

Run `python -m pytest -q` in `backend`; run `npm run build` in `frontend`. As checked on 2026-08-29, 48 backend tests pass, including aggregate source retention, validation, duplicate retention, board-cache, official SDK in-memory, real subprocess stdio and real HTTP tests. The protocol tests use explicitly synthetic listings; they do not prove employer vacancy status or production readiness. Browser checks additionally used current public listings, opened aggregate sources and reviewed their actual quotes.

Literal matching is intentionally limited: spelling aliases are explicit, and semantic equivalence is not inferred. Text signals currently cover selected English, Spanish and German terms, not every language. There is no user authentication, applicant tracking or automatic refresh of pasted listings. Operational limits are uncalibrated bounds, documented in code, not performance claims.

---

Earlier experiments: [historical safety lab](HISTORICAL_SAFETY_LAB.md). This is separate from the job-evidence product.

