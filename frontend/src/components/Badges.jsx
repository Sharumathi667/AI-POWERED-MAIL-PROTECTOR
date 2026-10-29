import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle, Info, Flame, Radio } from 'lucide-react';

export function SeverityBadge({ severity }) {
  const sev = (severity || 'low').toLowerCase();

  const config = {
    critical: {
      bg: 'bg-rose-500/15',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
      label: 'CRITICAL',
      icon: Flame,
    },
    high: {
      bg: 'bg-amber-500/15',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      label: 'HIGH',
      icon: AlertTriangle,
    },
    medium: {
      bg: 'bg-yellow-500/15',
      text: 'text-yellow-400',
      border: 'border-yellow-500/30',
      label: 'MEDIUM',
      icon: Info,
    },
    low: {
      bg: 'bg-emerald-500/15',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      label: 'LOW',
      icon: CheckCircle,
    },
  };

  const current = config[sev] || config.low;
  const Icon = current.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold border ${current.bg} ${current.text} ${current.border}`}>
      <Icon className="w-3 h-3" />
      {current.label}
    </span>
  );
}

export function RiskScoreBadge({ score }) {
  const num = parseFloat(score || 0);
  let colorClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  if (num >= 80) colorClass = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  else if (num >= 60) colorClass = 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  else if (num >= 30) colorClass = 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded font-mono text-xs font-bold border ${colorClass}`}>
      {num.toFixed(0)}/100
    </span>
  );
}

export function IncidentStatusBadge({ status }) {
  const s = status || 'New';
  const styles = {
    'New': 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    'Investigating': 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    'Contained': 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    'Resolved': 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    'False Positive': 'bg-slate-500/15 text-slate-300 border-slate-500/30'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${styles[s] || styles['New']}`}>
      {s}
    </span>
  );
}

export function SimulatedDataBanner() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between text-xs text-slate-400 mb-4">
      <div className="flex items-center gap-2">
        <Radio className="w-4 h-4 text-sky-400 animate-pulse" />
        <span>
          <strong className="text-slate-300 font-semibold">SIMULATED CAMPUS TELEMETRY:</strong> IP addresses (RFC 5737 doc ranges) and geolocations are synthetically generated for safe evaluation.
        </span>
      </div>
      <span className="font-mono text-[10px] text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded">
        Zero Real User Privacy Impact
      </span>
    </div>
  );
}
