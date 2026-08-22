export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type PolicyDecision =
  | 'allow'
  | 'deny'
  | 'require_approval'
  | 'approved'
  | 'denied'
  | 'rejected_invalid_token'
  | 'denied_oversized';

export interface TraceRecord {
  id: string;
  timestamp: string;
  session_id: string;
  request_id: string | number | null;
  method: string;
  tool_name: string | null;
  raw_arguments?: Record<string, unknown> | null;
  redacted_arguments?: Record<string, unknown> | null;
  policy_decision: string;
  matched_rule_id: string | null;
  policy_reason: string | null;
  risk_level: RiskLevel | null;
  approval_id: string | null;
  approval_status: 'none' | 'pending' | 'approved' | 'denied' | 'expired' | 'consumed' | 'invalid' | null;
  raw_result?: unknown;
  redacted_result?: unknown;
  error: string | null;
  duration_ms: number;
  simulated_tokens: number | null;
  simulated_cost_usd: number | null;
  is_synthetic: boolean;
}

export interface ApprovalRecord {
  id: string;
  trace_id: string;
  session_id: string;
  tool_name: string;
  arguments_hash: string;
  token: string;
  status: 'pending' | 'approved' | 'denied' | 'expired' | 'consumed';
  risk_level: RiskLevel;
  reason: string;
  redacted_arguments?: Record<string, unknown>;
  created_at: string;
  expires_at: string;
  decided_at: string | null;
  decided_by: string | null;
}

export interface ApprovalDecisionRequest {
  token: string;
  decision: 'approve' | 'deny';
  actor?: string;
  reason?: string;
}

export interface ArgumentPredicate {
  field: string;
  operator: string;
  value: unknown;
  description?: string;
}

export interface PolicyRule {
  id: string;
  name: string;
  tool_pattern: string;
  action: 'allow' | 'deny' | 'require_approval';
  risk_level: RiskLevel;
  description: string;
  argument_predicates: ArgumentPredicate[];
  max_calls_per_minute?: number | null;
  enabled: boolean;
}

export interface PolicyConfig {
  session_spend_limit_usd: number;
  default_action: 'allow' | 'deny' | 'require_approval';
  rules: PolicyRule[];
}

export interface PlaybackResult {
  original_trace_id: string;
  replayed_at: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  original_decision: string;
  playback_decision: string;
  decision_matches: boolean;
  playback_duration_ms: number;
  original_duration_ms: number;
  output: unknown;
  error: string | null;
}

export interface LatencyBenchmarkResult {
  iterations: number;
  measured_at: string;
  direct_latency_ms: {
    mean: number;
    median: number;
    min: number;
    max: number;
  };
  proxied_latency_ms: {
    mean: number;
    median: number;
    min: number;
    max: number;
  };
  overhead_latency_ms: {
    mean: number;
    percentage_increase: number;
  };
  is_measured: boolean;
}

export interface ProviderSimRunResult {
  provider_id: string;
  provider_name: string;
  prompt: string;
  generated_tool_call: {
    name: string;
    arguments: Record<string, unknown>;
  };
  wall_clock_latency_ms: number;
  simulated_input_tokens: number;
  simulated_output_tokens: number;
  simulated_total_cost_usd: number;
  policy_decision: string;
  is_simulation: boolean;
}

export interface BenchmarkComparisonReport {
  timestamp: string;
  iterations: number;
  workload_name: string;
  direct_execution_latency_ms: number;
  proxy_overhead_latency_ms: number;
  total_proxied_latency_ms: number;
  providers: ProviderSimRunResult[];
  summary: string;
  is_synthetic_workload: boolean;
}

export interface FixtureRecord {
  customer_id: string;
  name: string;
  email: string;
  account_balance: number;
  status: string;
  created_at: string;
}

export interface DemoStepResponse {
  step: number;
  title: string;
  description: string;
  response: {
    jsonrpc: string;
    id: string;
    result?: unknown;
    error?: {
      code: number;
      message: string;
      data?: unknown;
    };
  };
}
