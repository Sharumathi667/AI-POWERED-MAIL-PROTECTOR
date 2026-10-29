import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Key, 
  Sliders, 
  Clock, 
  Database, 
  FileText, 
  RefreshCw, 
  Check, 
  AlertCircle,
  ExternalLink,
  Radio,
  Lock
} from 'lucide-react';
import { fetchSettings, updateSettings, fetchAuditLogs } from '../services/api';
import { SimulatedDataBanner } from '../components/Badges';

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form state
  const [weights, setWeights] = useState({
    email_content: 0.40,
    email_url: 0.35,
    email_sender: 0.25,
    login_location: 0.35,
    login_device: 0.30,
    login_auth: 0.20,
    window_hours: 24,
  });

  const loadSettingsAndLogs = async () => {
    try {
      setLoading(true);
      const [sData, aData] = await Promise.all([
        fetchSettings(),
        fetchAuditLogs({ limit: 25 }),
      ]);
      setSettings(sData);
      setAuditLogs(aData.items || []);

      if (sData.risk_weights) {
        setWeights({
          email_content: sData.risk_weights.email_content,
          email_url: sData.risk_weights.email_url,
          email_sender: sData.risk_weights.email_sender_header,
          login_location: sData.risk_weights.login_location,
          login_device: sData.risk_weights.login_device,
          login_auth: sData.risk_weights.login_authentication,
          window_hours: sData.correlation?.window_hours || 24,
        });
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsAndLogs();
  }, []);

  const handleSaveWeights = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSaveSuccess(false);
      await updateSettings({
        email_weight_content: weights.email_content,
        email_weight_url: weights.email_url,
        email_weight_sender: weights.email_sender,
        login_weight_location: weights.login_location,
        login_weight_device: weights.login_device,
        login_weight_auth: weights.login_auth,
        correlation_window_hours: weights.window_hours,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      loadSettingsAndLogs();
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm font-mono">Loading System Settings & Audit Trail...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-sky-400" />
            <span>Platform Configuration & Security Audit</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure risk formula weights, inspect integration modes, and review tamper-evident audit logs.
          </p>
        </div>
      </div>

      <SimulatedDataBanner />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Card 1: Integration Architecture: Mode A vs Mode B */}
        <div className="cyber-card p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Key className="w-4 h-4 text-emerald-400" />
              <span>Integration Status: Mode A vs Mode B</span>
            </h2>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
              MODE A ACTIVE
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="bg-slate-900/80 p-3.5 rounded-lg border border-slate-800 space-y-1.5">
              <span className="font-semibold text-emerald-400 block font-mono">
                Mode A: Synthetic Demonstration Environment (Current)
              </span>
              <p className="text-slate-300 leading-relaxed">
                Operates completely without external Google API secrets or passwords. Uses reproducible synthetic campus mailboxes and simulated sign-in telemetry. All containment actions are safely simulated and audit-logged.
              </p>
            </div>

            <div className="bg-slate-900/50 p-3.5 rounded-lg border border-slate-800 space-y-2">
              <span className="font-semibold text-sky-400 block font-mono">
                Mode B: Google Workspace OAuth 2.0 Integration (Architecture Ready)
              </span>
              <p className="text-slate-400 leading-relaxed">
                Prepared for live campus deployments via Google Workspace Administrator consent.
              </p>
              <ul className="space-y-1 font-mono text-[11px] text-slate-400 list-disc list-inside">
                <li>Scope: <span className="text-slate-300">https://www.googleapis.com/auth/gmail.readonly</span></li>
                <li>Administrator Domain-Wide Delegation for multi-user campus scanning</li>
                <li>Token refresh & rate-limit backoff handler implemented</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Card 2: Risk Scoring Formula & Correlation Weights */}
        <div className="cyber-card p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-sky-400" />
              <span>Risk Engine Weight Configuration</span>
            </h2>
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                <Check className="w-3.5 h-3.5" /> Saved
              </span>
            )}
          </div>

          <form onSubmit={handleSaveWeights} className="space-y-4 text-xs">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Email Content ({weights.email_content * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.email_content}
                  onChange={(e) => setWeights({ ...weights, email_content: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Email URL ({weights.email_url * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.email_url}
                  onChange={(e) => setWeights({ ...weights, email_url: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Sender / Header ({weights.email_sender * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.email_sender}
                  onChange={(e) => setWeights({ ...weights, email_sender: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Login Location ({weights.login_location * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.login_location}
                  onChange={(e) => setWeights({ ...weights, login_location: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Login Device ({weights.login_device * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.login_device}
                  onChange={(e) => setWeights({ ...weights, login_device: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1 font-mono">Login Auth ({weights.login_auth * 100}%)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.login_auth}
                  onChange={(e) => setWeights({ ...weights, login_auth: parseFloat(e.target.value) || 0 })}
                  className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-400 block mb-1 font-mono">Correlation Sliding Window (Hours)</label>
              <input
                type="number"
                min="1"
                max="72"
                value={weights.window_hours}
                onChange={(e) => setWeights({ ...weights, window_hours: parseInt(e.target.value) || 24 })}
                className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 font-semibold rounded text-white text-xs transition"
            >
              {saving ? 'Updating Settings...' : 'Save Formula Weights'}
            </button>
          </form>
        </div>

      </div>

      {/* Security Audit Trail Table */}
      <div className="cyber-card p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <span>Immutable Security Operations Audit Log</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Cryptographically timestamped trail of all simulated response actions, approvals, status updates, and note entries.
            </p>
          </div>
          <button
            onClick={loadSettingsAndLogs}
            className="text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 font-mono"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Log
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Log ID</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Target</th>
                <th className="py-2.5 px-3">Actor</th>
                <th className="py-2.5 px-3">Details</th>
                <th className="py-2.5 px-3">Mode</th>
                <th className="py-2.5 px-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No audit records recorded yet.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 text-sky-400">#{log.id}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-200">{log.action}</td>
                    <td className="py-2.5 px-3 text-slate-300">{log.target_type}: {log.target_id}</td>
                    <td className="py-2.5 px-3 text-slate-400">{log.actor}</td>
                    <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate font-sans text-xs">
                      {typeof log.details === 'object' ? JSON.stringify(log.details) : log.details}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                        SIMULATED
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-500">
                      {new Date(log.timestamp).toLocaleTimeString()}
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
}
