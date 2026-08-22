import {
  ApprovalRecord,
  BenchmarkComparisonReport,
  DemoStepResponse,
  FixtureRecord,
  LatencyBenchmarkResult,
  PlaybackResult,
  PolicyConfig,
  TraceRecord,
} from '../types';

// Keep local development same-origin by default; hosted builds can point at the
// public Relay API without changing source code.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let errMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData.detail) errMsg = errData.detail;
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }

  return res.json();
}

export const api = {
  // Health
  checkHealth: () => fetchJson<{ status: string; app: string; version: string }>(`${BASE_URL}/health`),

  // Traces
  listTraces: (params?: { limit?: number; offset?: number; session_id?: string; policy_decision?: string; risk_level?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.session_id) searchParams.set('session_id', params.session_id);
    if (params?.policy_decision) searchParams.set('policy_decision', params.policy_decision);
    if (params?.risk_level) searchParams.set('risk_level', params.risk_level);
    const qs = searchParams.toString();
    return fetchJson<{ total: number; limit: number; offset: number; traces: TraceRecord[] }>(
      `${BASE_URL}/traces${qs ? `?${qs}` : ''}`
    );
  },

  getTrace: (traceId: string) => fetchJson<TraceRecord>(`${BASE_URL}/traces/${traceId}`),

  replayTrace: (traceId: string, overrideArguments?: Record<string, unknown>) =>
    fetchJson<PlaybackResult>(`${BASE_URL}/traces/replay`, {
      method: 'POST',
      body: JSON.stringify({ trace_id: traceId, override_arguments: overrideArguments }),
    }),

  // Approvals
  listApprovals: () => fetchJson<ApprovalRecord[]>(`${BASE_URL}/approvals`),

  decideApproval: (token: string, decision: 'approve' | 'deny', reason?: string) =>
    fetchJson<{ status: string; approval: ApprovalRecord }>(`${BASE_URL}/approvals/decide`, {
      method: 'POST',
      body: JSON.stringify({ token, decision, actor: 'human_operator', reason }),
    }),

  resumeApprovedToolCall: (approval: ApprovalRecord) =>
    fetchJson<Record<string, unknown>>(`${BASE_URL}/mcp/rpc`, {
      method: 'POST',
      headers: { 'X-Session-ID': approval.session_id },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: `resume_${approval.id}`,
        method: 'tools/call',
        params: {
          name: approval.tool_name,
          arguments: approval.redacted_arguments || {},
          _approval_token: approval.token,
        },
      }),
    }),

  // Policy
  getPolicy: () => fetchJson<PolicyConfig>(`${BASE_URL}/policy`),

  updatePolicy: (policy: PolicyConfig) =>
    fetchJson<PolicyConfig>(`${BASE_URL}/policy`, {
      method: 'PUT',
      body: JSON.stringify(policy),
    }),

  // Benchmarks
  runLatencyBenchmark: (iterations: number = 15) =>
    fetchJson<LatencyBenchmarkResult>(`${BASE_URL}/benchmarks/latency?iterations=${iterations}`, {
      method: 'POST',
    }),

  compareProviders: (prompt: string) =>
    fetchJson<BenchmarkComparisonReport>(
      `${BASE_URL}/benchmarks/compare-providers?prompt=${encodeURIComponent(prompt)}`,
      { method: 'POST' }
    ),

  // Fixtures
  getFixtureRecords: () => fetchJson<{ count: number; records: FixtureRecord[] }>(`${BASE_URL}/fixtures/records`),

  resetFixtures: () =>
    fetchJson<{ status: string; message: string; records: FixtureRecord[] }>(`${BASE_URL}/fixtures/reset`, {
      method: 'POST',
    }),

  // Demo
  triggerDemoStep: (step: number) => fetchJson<DemoStepResponse>(`${BASE_URL}/demo/step/${step}`, { method: 'POST' }),
};
