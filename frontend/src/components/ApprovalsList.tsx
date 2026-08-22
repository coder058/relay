import React, { useState } from 'react';
import { ApprovalRecord } from '../types';
import { RiskBadge } from './RiskBadge';
import { Check, X, Clock, Key, ShieldAlert } from 'lucide-react';

interface ApprovalsListProps {
  approvals: ApprovalRecord[];
  onDecide: (token: string, decision: 'approve' | 'deny', reason?: string) => Promise<void>;
  onRefresh?: () => void;
}

export const ApprovalsList: React.FC<ApprovalsListProps> = ({ approvals, onDecide }) => {
  const [decidingToken, setDecidingToken] = useState<string | null>(null);

  const pendingApprovals = approvals.filter((a) => a.status === 'pending');

  if (pendingApprovals.length === 0) {
    return (
      <div className="card" style={{ marginBottom: 24, borderStyle: 'dashed' }}>
        <div className="card-body" style={{ textAlign: 'center', padding: '24px 16px' }}>
          <Clock size={24} style={{ color: 'var(--text-muted)', margin: '0 auto 8px auto', display: 'block' }} />
          <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>No Pending Approvals</p>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            When an MCP tool call matches a high-risk policy rule (e.g. <code>delete_record</code>), execution pauses here for operator confirmation.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ marginBottom: 24, borderColor: '#fde68a', background: '#fffbeb' }}>
      <div className="card-header" style={{ background: '#fef3c7', borderColor: '#fde68a' }}>
        <div className="card-title" style={{ color: '#92400e' }}>
          <ShieldAlert size={18} />
          <span>Pending Approvals ({pendingApprovals.length})</span>
        </div>
        <span style={{ fontSize: 12, color: '#b45309', fontWeight: 500 }}>
          Human Operator Gate Active
        </span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {pendingApprovals.map((appr) => {
          const isProcessing = decidingToken === appr.token;

          return (
            <div
              key={appr.id}
              style={{
                background: '#ffffff',
                border: '1px solid #fde68a',
                borderRadius: 6,
                padding: 16,
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <code style={{ fontSize: 14, fontWeight: 600, color: '#991b1b', background: '#fee2e2', padding: '2px 6px', borderRadius: 4 }}>
                      {appr.tool_name}
                    </code>
                    <RiskBadge level={appr.risk_level} />
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      Trace: <code>{appr.trace_id}</code>
                    </span>
                  </div>
                  <p style={{ fontSize: 13, color: '#374151' }}>
                    {appr.reason}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    disabled={isProcessing}
                    onClick={async () => {
                      setDecidingToken(appr.token);
                      try {
                        await onDecide(appr.token, 'approve');
                      } finally {
                        setDecidingToken(null);
                      }
                    }}
                    className="btn btn-success btn-sm"
                  >
                    <Check size={14} />
                    Approve
                  </button>

                  <button
                    disabled={isProcessing}
                    onClick={async () => {
                      setDecidingToken(appr.token);
                      try {
                        await onDecide(appr.token, 'deny');
                      } finally {
                        setDecidingToken(null);
                      }
                    }}
                    className="btn btn-danger btn-sm"
                  >
                    <X size={14} />
                    Deny
                  </button>
                </div>
              </div>

              <div style={{ background: '#f8fafc', padding: 10, borderRadius: 4, border: '1px solid #e2e8f0', fontSize: 12 }}>
                <div style={{ color: 'var(--text-secondary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Key size={12} />
                  <span>Bound Token: <code>{appr.token}</code> (Expires: {new Date(appr.expires_at).toLocaleTimeString()})</span>
                </div>
                <div style={{ color: 'var(--text-secondary)', marginBottom: 2 }}>Arguments:</div>
                <pre style={{ margin: 0, fontSize: 11, color: '#0f172a' }}>
                  {JSON.stringify(appr.redacted_arguments || {}, null, 2)}
                </pre>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
