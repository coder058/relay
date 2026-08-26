import React, { useEffect, useState, useCallback } from 'react';
import { api } from './api/client';
import {
  ApprovalRecord,
  FixtureRecord,
  PlaybackResult,
  PolicyConfig,
  TraceRecord,
} from './types';
import { Navbar } from './components/Navbar';
import { ApprovalsList } from './components/ApprovalsList';
import { GuidedDemoStepper } from './components/GuidedDemoStepper';
import { TraceList } from './components/TraceList';
import { TraceDetailModal } from './components/TraceDetailModal';
import { PlaybackModal } from './components/PlaybackModal';
import { BenchmarkRunner } from './components/BenchmarkRunner';
import { PolicyViewer } from './components/PolicyViewer';
import { FixtureInspector } from './components/FixtureInspector';

export const App: React.FC = () => {
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'loading'>('loading');
  const [activeTab, setActiveTab] = useState<string>('traces');

  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [fixtures, setFixtures] = useState<FixtureRecord[]>([]);
  const [policy, setPolicy] = useState<PolicyConfig | null>(null);

  const [filterDecision, setFilterDecision] = useState<string>('');
  const [filterRisk, setFilterRisk] = useState<string>('');

  const [selectedTrace, setSelectedTrace] = useState<TraceRecord | null>(null);
  const [playbackResult, setPlaybackResult] = useState<PlaybackResult | null>(null);
  const [isReplaying, setIsReplaying] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  // Fetch all state data
  const refreshData = useCallback(async () => {
    try {
      const [healthRes, traceRes, apprRes, fixRes, polRes] = await Promise.allSettled([
        api.checkHealth(),
        api.listTraces({
          limit: 100,
          policy_decision: filterDecision || undefined,
          risk_level: filterRisk || undefined,
        }),
        api.listApprovals(),
        api.getFixtureRecords(),
        api.getPolicy(),
      ]);

      if (healthRes.status === 'fulfilled') {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }

      if (traceRes.status === 'fulfilled') {
        setTraces(traceRes.value.traces);
      }
      if (apprRes.status === 'fulfilled') {
        setApprovals(apprRes.value);
      }
      if (fixRes.status === 'fulfilled') {
        setFixtures(fixRes.value.records);
      }
      if (polRes.status === 'fulfilled') {
        setPolicy(polRes.value);
      }
    } catch (err) {
      setServerStatus('offline');
    }
  }, [filterDecision, filterRisk]);

  // Initial load and periodic polling for real-time approvals and traces
  useEffect(() => {
    refreshData();
    const timer = setInterval(refreshData, 3000);
    return () => clearInterval(timer);
  }, [refreshData]);

  const runSafeWalkthrough = useCallback(async () => {
    for (const step of [1, 2, 4, 5]) {
      await api.triggerDemoStep(step);
    }
    await refreshData();
  }, [refreshData]);

  // Handle human operator decision
  const handleDecideApproval = async (token: string, decision: 'approve' | 'deny', reason?: string) => {
    try {
      const decisionResult = await api.decideApproval(token, decision, reason);
      if (decision === 'approve') {
        await api.resumeApprovedToolCall(decisionResult.approval);
      }
      await refreshData();
    } catch (err) {
      alert(`Approval decision failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Handle trace replay
  const handleReplayTrace = async (trace: TraceRecord) => {
    setIsReplaying(true);
    setPlaybackResult(null);
    try {
      const res = await api.replayTrace(trace.id);
      setPlaybackResult(res);
    } catch (err) {
      alert(`Replay failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsReplaying(false);
    }
  };

  // Handle fixture reset
  const handleResetFixtures = async () => {
    setIsResetting(true);
    try {
      await api.resetFixtures();
      await refreshData();
    } catch (err) {
      alert(`Reset failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsResetting(false);
    }
  };

  const pendingCount = approvals.filter((a) => a.status === 'pending').length;

  return (
    <div>
      <Navbar
        serverStatus={serverStatus}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pendingApprovalsCount={pendingCount}
        onResetFixtures={handleResetFixtures}
        isResetting={isResetting}
      />

      <main className="app-container">
        {activeTab === 'traces' && (
          <div>
            <GuidedDemoStepper
              onTriggerStep={(step) => api.triggerDemoStep(step)}
              onRunWalkthrough={runSafeWalkthrough}
              onRefreshTraces={refreshData}
            />

            <ApprovalsList
              approvals={approvals}
              onDecide={handleDecideApproval}
            />

            <TraceList
              traces={traces}
              onSelectTrace={(t) => setSelectedTrace(t)}
              onReplayTrace={handleReplayTrace}
              filterDecision={filterDecision}
              setFilterDecision={setFilterDecision}
              filterRisk={filterRisk}
              setFilterRisk={setFilterRisk}
              onRunDemo={runSafeWalkthrough}
            />
          </div>
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkRunner
            onRunLatency={(iters) => api.runLatencyBenchmark(iters)}
            onCompareProviders={(prompt) => api.compareProviders(prompt)}
          />
        )}

        {activeTab === 'policy' && (
          <PolicyViewer policy={policy} />
        )}

        {activeTab === 'fixtures' && (
          <FixtureInspector
            records={fixtures}
            onReset={handleResetFixtures}
            isResetting={isResetting}
          />
        )}
      </main>

      {/* Trace Detail Modal */}
      <TraceDetailModal
        trace={selectedTrace}
        onClose={() => setSelectedTrace(null)}
        onReplay={handleReplayTrace}
      />

      {/* Playback Replay Modal */}
      <PlaybackModal
        playback={playbackResult}
        isLoading={isReplaying}
        onClose={() => setPlaybackResult(null)}
        onReplayAgain={() => {
          if (playbackResult) {
            const tr = traces.find((t) => t.id === playbackResult.original_trace_id);
            if (tr) handleReplayTrace(tr);
          }
        }}
      />
    </div>
  );
};

