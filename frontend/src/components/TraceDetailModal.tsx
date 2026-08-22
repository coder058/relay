import React from 'react';
import { TraceRecord } from '../types';
import { DecisionBadge } from './DecisionBadge';
import { RiskBadge } from './RiskBadge';
import { X, Play, Shield, Lock } from 'lucide-react';

interface TraceDetailModalProps {
  trace: TraceRecord | null;
  onClose: () => void;
  onReplay: (trace: TraceRecord) => void;
}

export const TraceDetailModal: React.FC<TraceDetailModalProps> = ({ trace, onClose, onReplay }) => {
  if (!trace) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Shield size={20} color="var(--accent-blue)" />
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>
              Trace Detail: <code>{trace.id}</code>
            </h3>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm" style={{ padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Metadata Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, background: '#f8fafc', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Timestamp</div>
              <div style={{ fontWeight: 500, fontSize: 13 }}>{new Date(trace.timestamp).toLocaleString()}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Tool / Method</div>
              <div style={{ fontWeight: 600, fontSize: 13, color: '#1e40af' }}>{trace.tool_name || trace.method}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Policy Decision</div>
              <DecisionBadge decision={trace.policy_decision} />
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Risk Level</div>
              <RiskBadge level={trace.risk_level} />
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Wall-Clock Duration</div>
              <div style={{ fontWeight: 500, fontSize: 13, fontFamily: 'var(--font-mono)' }}>{trace.duration_ms.toFixed(2)} ms</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Session ID</div>
              <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}>{trace.session_id}</div>
            </div>
          </div>

          {/* Policy Rationale */}
          <div>
            <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>
              Policy Evaluation Rationale
            </h4>
            <div style={{ background: '#f1f5f9', padding: 12, borderRadius: 6, fontSize: 13, color: '#334155' }}>
              {trace.policy_reason || 'No specific policy rule triggered.'}
              {trace.matched_rule_id && (
                <div style={{ marginTop: 4, fontSize: 11, color: 'var(--text-muted)' }}>
                  Rule ID: <code>{trace.matched_rule_id}</code>
                </div>
              )}
            </div>
          </div>

          {/* Redacted Arguments */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <h4 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Lock size={14} color="#7c3aed" />
                Sanitized Tool Arguments (Append-Only SQLite Record)
              </h4>
              <span style={{ fontSize: 11, color: '#16a34a', fontWeight: 500 }}>
                ✓ Secrets &amp; PII Redacted
              </span>
            </div>
            <pre className="code-block">
              {JSON.stringify(trace.redacted_arguments || {}, null, 2)}
            </pre>
          </div>

          {/* Result / Output */}
          <div>
            <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>
              Tool Execution Result
            </h4>
            {trace.error ? (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: 12, borderRadius: 6, fontSize: 13 }}>
                <strong>Error:</strong> {trace.error}
              </div>
            ) : (
              <pre className="code-block">
                {JSON.stringify(trace.redacted_result || {}, null, 2)}
              </pre>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onReplay(trace);
            }}
            className="btn btn-primary"
          >
            <Play size={14} />
            Replay Trace
          </button>
        </div>
      </div>
    </div>
  );
};
