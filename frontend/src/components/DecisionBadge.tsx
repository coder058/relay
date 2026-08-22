import React from 'react';
import { CheckCircle2, XCircle, Clock, ShieldCheck } from 'lucide-react';

interface DecisionBadgeProps {
  decision: string;
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision }) => {
  const norm = decision.toLowerCase();

  if (norm === 'allow') {
    return (
      <span className="badge badge-allow">
        <CheckCircle2 size={12} />
        Allow
      </span>
    );
  }

  if (norm === 'require_approval') {
    return (
      <span className="badge badge-approval">
        <Clock size={12} />
        Approval Req
      </span>
    );
  }

  if (norm === 'approved') {
    return (
      <span className="badge badge-approved">
        <ShieldCheck size={12} />
        Approved
      </span>
    );
  }

  return (
    <span className="badge badge-deny">
      <XCircle size={12} />
      {norm === 'rejected_invalid_token' ? 'Invalid Token' : 'Denied'}
    </span>
  );
};
