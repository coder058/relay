import React from 'react';
import { TraceRecord } from '../types';
import { DecisionBadge } from './DecisionBadge';
import { RiskBadge } from './RiskBadge';
import { Play, Eye, Hash } from 'lucide-react';

interface TraceListProps {
  traces: TraceRecord[];
  onSelectTrace: (trace: TraceRecord) => void;
  onReplayTrace: (trace: TraceRecord) => void;
  filterDecision: string;
  setFilterDecision: (val: string) => void;
  filterRisk: string;
  setFilterRisk: (val: string) => void;
}

export const TraceList: React.FC<TraceListProps> = ({
  traces,
  onSelectTrace,
  onReplayTrace,
  filterDecision,
  setFilterDecision,
  filterRisk,
  setFilterRisk,
}) => {
  return (
    <div className="card">
      <div className="card-header" style={{ flexWrap: 'wrap', gap: 12 }}>
        <div className="card-title">
          <Hash size={18} />
          <span>Execution Traces ({traces.length})</span>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            value={filterDecision}
            onChange={(e) => setFilterDecision(e.target.value)}
            style={{
              padding: '4px 8px',
              borderRadius: 4,
              border: '1px solid var(--border-color)',
              background: '#ffffff',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Decisions</option>
            <option value="allow">Allow</option>
            <option value="require_approval">Require Approval</option>
            <option value="approved">Approved</option>
            <option value="deny">Denied</option>
          </select>

          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            style={{
              padding: '4px 8px',
              borderRadius: 4,
              border: '1px solid var(--border-color)',
              background: '#ffffff',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Risk Levels</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Method / Tool</th>
              <th>Decision</th>
              <th>Risk</th>
              <th>Latency</th>
              <th>Simulated Cost</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {traces.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-secondary)' }}>
                  No traces recorded yet. Run a guided scenario or execute an MCP tool to see live traces.
                </td>
              </tr>
            ) : (
              traces.map((trace) => {
                const dateStr = new Date(trace.timestamp).toLocaleTimeString();

                return (
                  <tr key={trace.id} style={{ cursor: 'pointer' }} onClick={() => onSelectTrace(trace)}>
                    <td style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {dateStr}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {trace.tool_name || trace.method}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          ID: {trace.id.substring(0, 10)}...
                        </span>
                      </div>
                    </td>
                    <td>
                      <DecisionBadge decision={trace.policy_decision} />
                    </td>
                    <td>
                      <RiskBadge level={trace.risk_level} />
                    </td>
                    <td style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        {trace.duration_ms.toFixed(2)} ms
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                      {trace.simulated_cost_usd !== null ? (
                        <span title="Synthetic estimation label">
                          ${trace.simulated_cost_usd.toFixed(4)} <small style={{ color: 'var(--text-muted)' }}>(sim)</small>
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                        <button
                          onClick={() => onSelectTrace(trace)}
                          className="btn btn-secondary btn-sm"
                          title="View trace details"
                        >
                          <Eye size={12} />
                          Details
                        </button>
                        <button
                          onClick={() => onReplayTrace(trace)}
                          className="btn btn-secondary btn-sm"
                          title="Replay trace against local environment"
                        >
                          <Play size={12} />
                          Replay
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
