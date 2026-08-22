import React from 'react';
import { PolicyConfig } from '../types';
import { RiskBadge } from './RiskBadge';
import { DecisionBadge } from './DecisionBadge';
import { Shield } from 'lucide-react';

interface PolicyViewerProps {
  policy: PolicyConfig | null;
}

export const PolicyViewer: React.FC<PolicyViewerProps> = ({ policy }) => {
  if (!policy) {
    return (
      <div className="card">
        <div className="card-body" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          Loading active policy configuration...
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Policy Summary Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Shield size={18} color="var(--accent-blue)" />
            <span>Active Policy Engine Rules &amp; Budget Ceilings</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Configured via Pydantic schema
          </span>
        </div>

        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginBottom: 20 }}>
            <div style={{ background: '#f8fafc', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Session Spend Ceiling</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>
                ${policy.session_spend_limit_usd.toFixed(2)} USD
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                # PLACEHOLDER: conservative lab budget threshold
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Default Fallback Action</div>
              <div style={{ marginTop: 4 }}>
                <DecisionBadge decision={policy.default_action} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                # GUESS: zero-trust deny for unlisted tools
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>Total Evaluated Rules</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-blue)' }}>
                {policy.rules.length} Rules Active
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                Evaluated in strict sequential order
              </div>
            </div>
          </div>

          {/* Rules Table */}
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Rule ID / Name</th>
                  <th>Tool Pattern</th>
                  <th>Decision</th>
                  <th>Risk Level</th>
                  <th>Description</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {policy.rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{rule.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{rule.id}</div>
                    </td>
                    <td>
                      <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>
                        {rule.tool_pattern}
                      </code>
                    </td>
                    <td>
                      <DecisionBadge decision={rule.action} />
                    </td>
                    <td>
                      <RiskBadge level={rule.risk_level} />
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {rule.description}
                    </td>
                    <td>
                      <span style={{ fontSize: 11, color: rule.enabled ? '#16a34a' : '#94a3b8', fontWeight: 600 }}>
                        {rule.enabled ? 'ACTIVE' : 'DISABLED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
