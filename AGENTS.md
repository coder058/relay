# Relay project rules

Relay is a portfolio project demonstrating safe, observable MCP tool execution.

## Non-negotiable honesty rules

- Do not claim production readiness, zero-copy performance, or a latency value until a measured test proves it.
- Do not call a mock tool execution a real external side effect.
- Keep all demo tools safe and local. Never execute arbitrary shell commands or destructive database operations.
- Label synthetic traces and fixtures as synthetic.
- Every numeric threshold or demo constant must be documented with `# SOURCE:`, `# GUESS:`, or `# PLACEHOLDER:` explaining its origin.
- API keys and provider credentials must never be stored in the repository, traces, browser storage, or README examples.

## Scope for the first complete version

1. A working MCP JSON-RPC stdio proxy for `tools/list` and `tools/call`.
2. A policy engine that evaluates tool name, arguments, session spend and approval state.
3. Human approval for risky calls with an expiring approval token.
4. Append-only trace storage with redaction and a playback endpoint.
5. A safe local demo agent and safe local tools that make the full flow reproducible.
6. A dashboard showing traces, policy decisions, approvals, latency and playback comparisons.
7. Deterministic tests, an actual latency benchmark, Docker instructions, and a recruiter-readable README.

Do not add multi-provider failover, arbitrary remote tool execution, or claims about enterprise scale until the first version is tested and reviewed.
