import React, { useState } from 'react';
import { Play, CheckCircle, ShieldAlert, Lock, EyeOff, Sparkles } from 'lucide-react';
import { DemoStepResponse } from '../types';

interface GuidedDemoStepperProps {
  onTriggerStep: (step: number) => Promise<DemoStepResponse>;
  onRunWalkthrough: () => Promise<void>;
  onRefreshTraces: () => void;
}

export const GuidedDemoStepper: React.FC<GuidedDemoStepperProps> = ({ onTriggerStep, onRunWalkthrough, onRefreshTraces }) => {
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastResult, setLastResult] = useState<DemoStepResponse | null>(null);
  const [walkthroughError, setWalkthroughError] = useState<string | null>(null);

  const steps = [
    {
      step: 1,
      title: '1. Safe Read',
      icon: <CheckCircle size={14} color="#16a34a" />,
      desc: 'Calls read_record (Allowed automatically)',
    },
    {
      step: 2,
      title: '2. Tool Discovery',
      icon: <Sparkles size={14} color="#2563eb" />,
      desc: 'Calls list_records (Allowed discovery)',
    },
    {
      step: 3,
      title: '3. Risky Deletion Gate',
      icon: <ShieldAlert size={14} color="#d97706" />,
      desc: 'Calls delete_record (Pauses for human approval)',
    },
    {
      step: 4,
      title: '4. Critical Policy Block',
      icon: <Lock size={14} color="#dc2626" />,
      desc: 'Attempts system_shell_exec (Blocked by policy)',
    },
    {
      step: 5,
      title: '5. Secret Redaction',
      icon: <EyeOff size={14} color="#7c3aed" />,
      desc: 'Injects API keys & email (Redacted before trace store)',
    },
  ];

  const handleRun = async (stepNum: number) => {
    setActiveStep(stepNum);
    setIsLoading(true);
    try {
      const res = await onTriggerStep(stepNum);
      setLastResult(res);
      onRefreshTraces();
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleWalkthrough = async () => {
    setIsLoading(true);
    setWalkthroughError(null);
    try {
      await onRunWalkthrough();
      onRefreshTraces();
    } catch (err) {
      setWalkthroughError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 24, borderLeft: '4px solid var(--accent-blue)' }}>
      <div className="card-header" style={{ padding: '12px 20px' }}>
        <div className="card-title" style={{ fontSize: 14 }}>
          <Play size={16} color="var(--accent-blue)" />
          <span>Guided Safety Scenarios (Reproducible Demo)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Synthetic local scenarios - no external model or paid API
          </span>
          <button className="btn btn-primary btn-sm" disabled={isLoading} onClick={handleWalkthrough}>
            <Play size={12} />
            {isLoading ? 'Running...' : 'Run safe walkthrough'}
          </button>
        </div>
      </div>

      <div className="card-body" style={{ padding: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 8, marginBottom: 16 }}>
          {[
            ['ALLOW', 'Safe reads pass'],
            ['REVIEW', 'Deletion pauses'],
            ['DENY', 'Shell is blocked'],
            ['REDACT', 'Secrets leave no raw trace'],
          ].map(([label, description]) => (
            <div key={label} style={{ border: '1px solid var(--border-color)', borderRadius: 6, padding: '9px 10px', background: '#fafafa' }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.06em', color: 'var(--text-primary)' }}>{label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 3 }}>{description}</div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: '0 0 12px' }}>
          The walkthrough runs safe read, discovery, critical-block, and redaction scenarios. The deletion gate stays manual so you can inspect and approve it yourself.
        </p>
        {walkthroughError && (
          <div role="alert" style={{ color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: 10, marginBottom: 12, fontSize: 12 }}>
            Walkthrough failed: {walkthroughError}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10, marginBottom: lastResult ? 16 : 0 }}>
          {steps.map((s) => (
            <button
              key={s.step}
              disabled={isLoading}
              onClick={() => handleRun(s.step)}
              className="btn btn-secondary"
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                padding: '10px 12px',
                textAlign: 'left',
                background: activeStep === s.step ? '#eff6ff' : '#ffffff',
                borderColor: activeStep === s.step ? '#93c5fd' : 'var(--border-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>
                {s.icon}
                <span>{s.title}</span>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {s.desc}
              </span>
            </button>
          ))}
        </div>

        {lastResult && (
          <div style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 6, padding: 12, marginTop: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
                Result: {lastResult.title}
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                Step {lastResult.step} executed
              </span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
              {lastResult.description}
            </p>
            <pre className="code-block" style={{ fontSize: 11, maxHeight: 180, overflowY: 'auto' }}>
              {JSON.stringify(lastResult.response, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

