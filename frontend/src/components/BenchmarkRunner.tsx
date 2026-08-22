import React, { useState } from 'react';
import { BenchmarkComparisonReport, LatencyBenchmarkResult } from '../types';
import { Zap, Play, BarChart2, Info, Clock } from 'lucide-react';
import { DecisionBadge } from './DecisionBadge';

interface BenchmarkRunnerProps {
  onRunLatency: (iterations: number) => Promise<LatencyBenchmarkResult>;
  onCompareProviders: (prompt: string) => Promise<BenchmarkComparisonReport>;
}

export const BenchmarkRunner: React.FC<BenchmarkRunnerProps> = ({
  onRunLatency,
  onCompareProviders,
}) => {
  const [iterations, setIterations] = useState(15);
  const [latencyResult, setLatencyResult] = useState<LatencyBenchmarkResult | null>(null);
  const [isBenchmarking, setIsBenchmarking] = useState(false);

  const [comparePrompt, setComparePrompt] = useState('Read customer account for CUST-1002');
  const [compareResult, setCompareResult] = useState<BenchmarkComparisonReport | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const handleRunLatency = async () => {
    setIsBenchmarking(true);
    try {
      const res = await onRunLatency(iterations);
      setLatencyResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsBenchmarking(false);
    }
  };

  const handleRunComparison = async () => {
    setIsComparing(true);
    try {
      const res = await onCompareProviders(comparePrompt);
      setCompareResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Empirical Latency Benchmark */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Zap size={18} color="var(--accent-blue)" />
            <span>Measured Proxy Wall-Clock Overhead Benchmark</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Iterations:</label>
            <select
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border-color)' }}
            >
              <option value={5}>5 iterations</option>
              <option value={15}>15 iterations</option>
              <option value={30}>30 iterations</option>
            </select>
            <button
              onClick={handleRunLatency}
              disabled={isBenchmarking}
              className="btn btn-primary btn-sm"
            >
              <Play size={13} className={isBenchmarking ? 'spin' : ''} />
              {isBenchmarking ? 'Measuring...' : 'Run Benchmark'}
            </button>
          </div>
        </div>

        <div className="card-body">
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Empirically executes consecutive tool calls comparing direct in-process execution vs transparent MCP proxy execution (including policy evaluation, secret redaction, and append-only SQLite persistence). No synthetic latency values are used here.
          </p>

          {latencyResult ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 16 }}>
                <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 6, padding: 14 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Direct Tool Mean Latency</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {latencyResult.direct_latency_ms.mean.toFixed(2)} ms
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                    Min: {latencyResult.direct_latency_ms.min}ms | Max: {latencyResult.direct_latency_ms.max}ms
                  </div>
                </div>

                <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 6, padding: 14 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Proxied + SQLite Trace Mean</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>
                    {latencyResult.proxied_latency_ms.mean.toFixed(2)} ms
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                    Min: {latencyResult.proxied_latency_ms.min}ms | Max: {latencyResult.proxied_latency_ms.max}ms
                  </div>
                </div>

                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: 14 }}>
                  <div style={{ fontSize: 11, color: '#15803d', marginBottom: 2 }}>Measured Proxy Overhead</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#16a34a' }}>
                    +{latencyResult.overhead_latency_ms.mean.toFixed(2)} ms
                  </div>
                  <div style={{ fontSize: 11, color: '#15803d', marginTop: 4 }}>
                    Measured across {latencyResult.iterations} cycles
                  </div>
                </div>
              </div>

              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Measured at: {new Date(latencyResult.measured_at).toLocaleString()} (Empirical wall-clock time)
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px 0', border: '1px dashed var(--border-color)', borderRadius: 6 }}>
              <Clock size={20} style={{ color: 'var(--text-muted)', margin: '0 auto 8px auto' }} />
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                Click "Run Benchmark" above to measure actual wall-clock proxy overhead on your hardware.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Provider Simulator Comparison */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <BarChart2 size={18} color="var(--accent-purple)" />
            <span>Deterministic Provider Simulator Comparison</span>
          </div>
          <span style={{ fontSize: 11, background: '#faf5ff', color: '#7c3aed', padding: '2px 8px', borderRadius: 4, fontWeight: 600, border: '1px solid #e9d5ff' }}>
            SYNTHETIC TOKENS &amp; COSTS
          </span>
        </div>

        <div className="card-body">
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <input
              type="text"
              value={comparePrompt}
              onChange={(e) => setComparePrompt(e.target.value)}
              placeholder="Enter simulated prompt..."
              style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-color)' }}
            />
            <button
              onClick={handleRunComparison}
              disabled={isComparing}
              className="btn btn-primary"
            >
              <Play size={14} className={isComparing ? 'spin' : ''} />
              {isComparing ? 'Simulating...' : 'Compare Providers'}
            </button>
          </div>

          <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
            <Info size={16} color="#64748b" />
            <span>
              Compares deterministic model simulators without calling external paid APIs. Estimated token counts and pricing calculations are explicitly synthetic proxies.
            </span>
          </div>

          {compareResult && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                {compareResult.providers.map((p) => (
                  <div key={p.provider_id} style={{ border: '1px solid var(--border-color)', borderRadius: 6, padding: 14, background: '#ffffff' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{p.provider_name}</h4>
                      <DecisionBadge decision={p.policy_decision} />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12, marginBottom: 10 }}>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Wall-clock latency: </span>
                        <strong>{p.wall_clock_latency_ms.toFixed(2)} ms</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Simulated Tokens: </span>
                        <strong>{p.simulated_input_tokens + p.simulated_output_tokens}</strong>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Simulated Cost: </span>
                        <strong>${p.simulated_total_cost_usd.toFixed(6)}</strong>
                      </div>
                    </div>

                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>Generated Tool Call:</div>
                    <pre className="code-block" style={{ fontSize: 11, maxHeight: 100 }}>
                      {JSON.stringify(p.generated_tool_call, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: '#f1f5f9', padding: 10, borderRadius: 4 }}>
                {compareResult.summary}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
