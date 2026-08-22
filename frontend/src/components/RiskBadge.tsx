import React from 'react';
import { RiskLevel } from '../types';

interface RiskBadgeProps {
  level?: RiskLevel | string | null;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level }) => {
  const norm = (level || 'low').toLowerCase();

  return (
    <span className={`badge badge-risk-${norm}`}>
      {norm}
    </span>
  );
};
