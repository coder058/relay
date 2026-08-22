import React from 'react';
import { FixtureRecord } from '../types';
import { Database, RefreshCw } from 'lucide-react';

interface FixtureInspectorProps {
  records: FixtureRecord[];
  onReset: () => void;
  isResetting: boolean;
}

export const FixtureInspector: React.FC<FixtureInspectorProps> = ({
  records,
  onReset,
  isResetting,
}) => {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Database size={18} color="var(--accent-blue)" />
          <span>Safe Local SQLite Fixture ({records.length} Records)</span>
        </div>
        <button
          onClick={onReset}
          disabled={isResetting}
          className="btn btn-secondary btn-sm"
          title="Reset demo records to initial seed"
        >
          <RefreshCw size={13} className={isResetting ? 'spin' : ''} />
          {isResetting ? 'Resetting...' : 'Reset Fixture'}
        </button>
      </div>

      <div className="card-body">
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          All tool mutations (like record creation or record deletion) operate solely on this isolated local SQLite table. No real database or external API is ever touched.
        </p>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Account Balance</th>
                <th>Status</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '24px 16px', color: 'var(--text-secondary)' }}>
                    All fixture records have been deleted. Click "Reset Fixture" to restore seed records.
                  </td>
                </tr>
              ) : (
                records.map((r) => (
                  <tr key={r.customer_id}>
                    <td>
                      <code style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{r.customer_id}</code>
                    </td>
                    <td style={{ fontWeight: 500 }}>{r.name}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{r.email}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>${r.account_balance.toFixed(2)}</td>
                    <td>
                      <span style={{ fontSize: 11, background: '#f1f5f9', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {new Date(r.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
