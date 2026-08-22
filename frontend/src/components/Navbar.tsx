import React from 'react';
import { Shield, RefreshCw, Activity, Zap, Database } from 'lucide-react';

interface NavbarProps {
  serverStatus: 'online' | 'offline' | 'loading';
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
  onResetFixtures: () => void;
  isResetting: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  serverStatus,
  activeTab,
  setActiveTab,
  pendingApprovalsCount,
  onResetFixtures,
  isResetting,
}) => {
  return (
    <header style={{ background: '#ffffff', borderBottom: '1px solid var(--border-color)', marginBottom: 24 }}>
      <div className="app-container" style={{ padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ background: '#eff6ff', padding: '8px', borderRadius: '8px', color: '#2563eb', display: 'flex' }}>
            <Shield size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h1 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Relay
              </h1>
              <span style={{ fontSize: 11, background: '#f1f5f9', color: '#475569', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>
                MCP SAFETY LAB
              </span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Deterministic Policy Enforcement &amp; Redacted Observability
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, background: '#f1f5f9', padding: 4, borderRadius: 8 }}>
          <button
            onClick={() => setActiveTab('traces')}
            className="btn"
            style={{
              padding: '6px 14px',
              fontSize: 13,
              borderRadius: 6,
              background: activeTab === 'traces' ? '#ffffff' : 'transparent',
              color: activeTab === 'traces' ? 'var(--text-primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'traces' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              fontWeight: activeTab === 'traces' ? 600 : 500,
            }}
          >
            <Activity size={15} />
            Traces &amp; Approvals
            {pendingApprovalsCount > 0 && (
              <span style={{ background: '#dc2626', color: '#fff', fontSize: 10, padding: '1px 6px', borderRadius: 10, fontWeight: 700 }}>
                {pendingApprovalsCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('benchmark')}
            className="btn"
            style={{
              padding: '6px 14px',
              fontSize: 13,
              borderRadius: 6,
              background: activeTab === 'benchmark' ? '#ffffff' : 'transparent',
              color: activeTab === 'benchmark' ? 'var(--text-primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'benchmark' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              fontWeight: activeTab === 'benchmark' ? 600 : 500,
            }}
          >
            <Zap size={15} />
            Overhead &amp; Playback
          </button>

          <button
            onClick={() => setActiveTab('policy')}
            className="btn"
            style={{
              padding: '6px 14px',
              fontSize: 13,
              borderRadius: 6,
              background: activeTab === 'policy' ? '#ffffff' : 'transparent',
              color: activeTab === 'policy' ? 'var(--text-primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'policy' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              fontWeight: activeTab === 'policy' ? 600 : 500,
            }}
          >
            <Shield size={15} />
            Policy Rules
          </button>

          <button
            onClick={() => setActiveTab('fixtures')}
            className="btn"
            style={{
              padding: '6px 14px',
              fontSize: 13,
              borderRadius: 6,
              background: activeTab === 'fixtures' ? '#ffffff' : 'transparent',
              color: activeTab === 'fixtures' ? 'var(--text-primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'fixtures' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
              fontWeight: activeTab === 'fixtures' ? 600 : 500,
            }}
          >
            <Database size={15} />
            Safe Fixtures
          </button>
        </div>

        {/* Status & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: serverStatus === 'online' ? '#16a34a' : '#dc2626',
              }}
            />
            {serverStatus === 'online' ? 'Proxy Active' : 'Offline'}
          </div>

          <button
            onClick={onResetFixtures}
            disabled={isResetting}
            className="btn btn-secondary btn-sm"
            title="Reset demo SQLite fixture records to initial clean state"
          >
            <RefreshCw size={13} className={isResetting ? 'spin' : ''} />
            Reset Fixture
          </button>
        </div>
      </div>
    </header>
  );
};
