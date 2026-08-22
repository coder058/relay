import React from 'react';
import { PlaybackResult } from '../types';
import { X, CheckCircle2, AlertTriangle, RefreshCw, Zap } from 'lucide-react';

interface PlaybackModalProps {
  playback: PlaybackResult | null;
  isLoading: boolean;
  onClose: () => void;
  onReplayAgain: () => void;
}

export const PlaybackModal: React.FC<PlaybackModalProps> = ({
  playback,
  isLoading,
  onClose,
  onReplayAgain,
}) => {
  if (!playback && !isLoading) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Zap size={20} color="var(--accent-purple)" />
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>
              Deterministic Trace Playback
            </h3>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm" style={{ padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
              <RefreshCw size={24} className="spin" style={{ margin: '0 auto 12px auto' }} />
              <p>Replaying trace against local policy engine and safe MCP fixture...</p>
            </div>
          ) : playback ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Determinism Status Banner */}
              <div
                style={{
                  padding: 14,
                  borderRadius: 6,
                  background: playback.decision_matches ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${playback.decision_matches ? '#bbf7d0' : '#fecaca'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                {playback.decision_matches ? (
                  <CheckCircle2 size={24} color="#16a34a" />
                ) : (
                  <AlertTriangle size={24} color="#dc2626" />
                )}
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: playback.decision_matches ? '#15803d' : '#991b1b' }}>
                    {playback.decision_matches
                      ? 'Deterministic Policy Verification Passed'
                      : 'Policy Decision Divergence Detected'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    Original Decision: <strong>{playback.original_decision}</strong> | Playback Decision: <strong>{playback.playback_decision}</strong>
                  </div>
                </div>
              </div>

              {/* Timing Comparison */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Original Latency</div>
                  <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {playback.original_duration_ms.toFixed(2)} ms
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Playback Latency (Measured)</div>
                  <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'var(--font-mono)', color: '#2563eb' }}>
                    {playback.playback_duration_ms.toFixed(2)} ms
                  </div>
                </div>
              </div>

              {/* Output */}
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Replay Output</h4>
                {playback.error ? (
                  <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: 12, borderRadius: 6, fontSize: 13 }}>
                    {playback.error}
                  </div>
                ) : (
                  <pre className="code-block">
                    {JSON.stringify(playback.output, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ) : null}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
          <button onClick={onReplayAgain} disabled={isLoading} className="btn btn-primary">
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
            Replay Again
          </button>
        </div>
      </div>
    </div>
  );
};
