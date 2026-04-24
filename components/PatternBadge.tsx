'use client';

import { ChartPattern } from '@/types';
import { Activity } from 'lucide-react';

interface PatternBadgeProps {
  pattern: ChartPattern;
}

export default function PatternBadge({ pattern }: PatternBadgeProps) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'border-terminal-success/50 bg-terminal-success/5';
    if (confidence >= 60) return 'border-terminal-warning/50 bg-terminal-warning/5';
    return 'border-terminal-muted/50 bg-terminal-muted/5';
  };

  return (
    <div className={`rounded border p-2 ${getConfidenceColor(pattern.confidence)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-terminal-accent" />
          <span className="text-sm font-medium">{pattern.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-terminal-muted">{pattern.timeframe}</span>
          <span className="mono-nums text-terminal-accent">{pattern.confidence}%</span>
        </div>
      </div>
      <div className="flex gap-4 text-xs">
        <div>
          <span className="text-terminal-muted">S: </span>
          <span className="mono-nums text-terminal-success">
            {pattern.keyLevels.support.map(s => `₹${s}`).join(', ')}
          </span>
        </div>
        <div>
          <span className="text-terminal-muted">R: </span>
          <span className="mono-nums text-terminal-danger">
            {pattern.keyLevels.resistance.map(r => `₹${r}`).join(', ')}
          </span>
        </div>
      </div>
    </div>
  );
}
