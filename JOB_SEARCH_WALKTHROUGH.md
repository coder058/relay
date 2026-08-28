# Observed job-search walkthrough

Checked 28 August 2026 against the public HTTP MCP service using
`scripts/verify_job_mcp.py`. This is a maintainer-run task observation, not
independent user feedback, customer adoption or a benchmark.

## Task and observations

Task: find a backend-development listing and carry its source through review
and Markdown export, without submitting an application.

- Searching `Python` returned 25 matches in the fetched board snapshot. The
  first was [Application Product Manager - AI System Transformations](https://www.arbeitnow.com/jobs/companies/celonis/application-product-manager-ai-system-transformations-munich-223676).
  That is an important false positive for a developer's intended search:
  mentioning a language does not make a listing a developer role.
- Revised the search to `backend`. The same board snapshot returned 17 matches;
  the first was [Senior Software Engineer - Integrations - AI/ML](https://www.arbeitnow.com/jobs/companies/clickhouse/senior-software-engineer-integrations-ai-ml-493224).
  Search, evidence review and Markdown export completed through the real MCP
  tools. The title is senior; this is not a recommendation to an early-career
  applicant or proof of eligibility.
- Both reviews retained `not_submitted` and `not_determined`. No application,
  message, paid model call or account mutation was performed.

Board snapshot timestamp: `2026-08-28T20:34:58.509199+00:00`.
Backend listing normalized source SHA-256:
`e70fe6f619aaac18de46cd252897feccaad0f51328ddcc395fc705bbeb245920`.
Counts belong to that snapshot, not all jobs in the market. A content hash
proves snapshot identity, not that a vacancy remains open.

## Revision and remaining gap

The smoke-check script now accepts `--query`, so role-specific searches can be
repeated without editing code. Literal search is still not semantic matching.
Users must inspect seniority, location, work authorization and the employer's
current listing before deciding whether to apply. No time saving or hiring
outcome was measured. The public board covers only the provider's latest page.

```sh
python scripts/verify_job_mcp.py https://relay-backend-r3ux6b3uwa-ew.a.run.app/tools/mcp --query backend
```
