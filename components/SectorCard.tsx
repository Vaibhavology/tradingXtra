'use client';

import { Sector } from '@/types';
import { TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';

interface SectorCardProps {
  sector: Sector;
}

export default function SectorCard({ sector }: SectorCardProps) {
  const getDirectionIcon = () => {
    switch (sector.direction) {
      case 'bullish':
        return <TrendingUp className="w-5 h-5 text-terminal-success" />;
      case 'bearish':
        return <TrendingDown className="w-5 h-5 text-terminal-danger" />;
      default:
        return <Minus className="w-5 h-5 text-terminal-warning" />;
    }
  };

  const getDirectionColor = () => {
    switch (sector.direction) {
      case 'bullish':
        return 'text-terminal-success';
      case 'bearish':
        return 'text-terminal-danger';
      default:
        return 'text-terminal-warning';
    }
  };

  const getStrengthBar = () => {
    let color = 'bg-terminal-success';
    if (sector.strength < 40) color = 'bg-terminal-danger';
    else if (sector.strength < 60) color = 'bg-terminal-warning';
    
    return (
      <div className="w-full h-1.5 bg-terminal-border rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-all`}
          style={{ width: `${sector.strength}%` }}
        />
      </div>
    );
  };

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-lg p-4 hover:border-terminal-accent/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {getDirectionIcon()}
          <div>
            <h3 className="font-medium">{sector.name}</h3>
            <span className={`text-sm capitalize ${getDirectionColor()}`}>
              {sector.direction}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold mono-nums">{sector.strength}</div>
          <div className="text-xs text-terminal-muted">Strength</div>
        </div>
      </div>

      {getStrengthBar()}

      <p className="text-sm text-terminal-muted mt-3 mb-3">{sector.reason}</p>

      <div className="flex items-center justify-between pt-3 border-t border-terminal-border">
        <div className="text-sm">
          <span className="text-terminal-muted">Top Pick: </span>
          <span className="font-medium text-terminal-accent">{sector.topPick}</span>
        </div>
        <ArrowRight className="w-4 h-4 text-terminal-muted" />
      </div>
    </div>
  );
}
