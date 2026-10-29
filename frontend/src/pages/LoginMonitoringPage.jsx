import React, { useState, useEffect } from 'react';
import { 
  LogIn, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle, 
  ChevronLeft, 
  ChevronRight, 
  RefreshCw, 
  Radio, 
  MapPin, 
  Compass, 
  Smartphone, 
  ShieldAlert, 
  Clock,
  Send,
  Zap
} from 'lucide-react';
import { fetchLogins, fetchLoginDetails, analyzeCustomLogin } from '../services/api';
import { SeverityBadge, RiskScoreBadge, SimulatedDataBanner } from '../components/Badges';

export default function LoginMonitoringPage() {
  const [logins, setLogins] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterSuspicious, setFilterSuspicious] = useState('');
  const [filterImpossible, setFilterImpossible] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortDir, setSortDir] = useState('desc');

  // Detail Modal
  const [selectedLogin, setSelectedLogin] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Live Sandbox
  const [showSandbox, setShowSandbox] = useState(false);
  const [sandboxForm, setSandboxForm] = useState({
    user_id: 'USER-1002',
    ip_address: '203.0.113.195',
    country: 'Romania',
    city: 'Bucharest',
    device_id: 'DEV-ROGUE-449',
    device_type: 'desktop',
    browser: 'Unknown/TorBrowser',
    operating_system: 'Linux',
    login_success: 1,
    failed_attempts: 6,
    is_new_device: 1,
    is_new_location: 1,
    distance_from_usual_location_km: 7400,
    minutes_since_previous_login: 20,
    impossible_travel: 1
  });
  const [sandboxResult, setSandboxResult] = useState(null);
  const [sandboxLoading, setSandboxLoading] = useState(false);

  const loadLogins = async () => {
    try {
      setLoading(true);
      const data = await fetchLogins({
        page,
        limit: 20,
        search: search || undefined,
        severity: filterSeverity || undefined,
        is_suspicious: filterSuspicious === '' ? undefined : filterSuspicious === 'true',
        impossible_travel: filterImpossible === '' ? undefined : parseInt(filterImpossible),
        sort_by: sortBy,
        sort_dir: sortDir,
      });
      setLogins(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load logins:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogins();
  }, [page, filterSeverity, filterSuspicious, filterImpossible, sortBy, sortDir]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadLogins();
  };

  const handleOpenDetails = async (eventId) => {
    try {
      setDetailLoading(true);
      const data = await fetchLoginDetails(eventId);
      setSelectedLogin(data);
    } catch (err) {
      console.error('Failed to load login details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleRunSandbox = async (e) => {
    e.preventDefault();
    try {
      setSandboxLoading(true);
      const res = await analyzeCustomLogin(sandboxForm);
      setSandboxResult(res);
      loadLogins();
    } catch (err) {
      console.error('Sandbox error:', err);
    } finally {
      setSandboxLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <LogIn className="w-6 h-6 text-amber-400" />
            <span>Login Behavior & Anomaly Telemetry</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Unsupervised Isolation Forest model and heuristic guardrails for impossible travel and credential stuffing.
          </p>
        </div>
        <div>
          <button
            onClick={() => setShowSandbox(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white shadow-md shadow-amber-600/20 transition"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Simulate Anomaly Attempt</span>
          </button>
        </div>
      </div>

      <SimulatedDataBanner />

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="relative lg:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search user ID, IP address, city, or country..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Severity Filter */}
          <div>
            <select
              value={filterSeverity}
              onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical (80-100)</option>
              <option value="high">High (60-79)</option>
              <option value="medium">Medium (30-59)</option>
              <option value="low">Low (0-29)</option>
            </select>
          </div>

          {/* Anomaly Filter */}
          <div>
            <select
              value={filterSuspicious}
              onChange={(e) => { setFilterSuspicious(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Statuses</option>
              <option value="true">Flagged Anomalies Only</option>
              <option value="false">Normal Sign-ins Only</option>
            </select>
          </div>

          {/* Impossible Travel Filter */}
          <div>
            <select
              value={filterImpossible}
              onChange={(e) => { setFilterImpossible(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Travel Distances</option>
              <option value="1">Impossible Travel Only ⚡</option>
              <option value="0">Normal Geography</option>
            </select>
          </div>
        </form>
      </div>

      {/* Login Table */}
      <div className="cyber-card border border-slate-800 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">
            Total Telemetry Records: <span className="font-mono text-amber-400">{total}</span>
          </span>
          <span className="text-[11px] text-slate-500">Page {page} of {totalPages}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">IP Address</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Device & OS</th>
                <th className="py-3 px-4">Distance (km)</th>
                <th className="py-3 px-4">Travel Flag</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400 font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-400" />
                    Fetching Login Telemetry...
                  </td>
                </tr>
              ) : logins.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500 font-mono">
                    No login events found matching criteria.
                  </td>
                </tr>
              ) : (
                logins.map((l) => (
                  <tr key={l.event_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-amber-400">{l.event_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{l.user_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{l.ip_address}</td>
                    <td className="py-3 px-4 text-slate-200">
                      {l.city}, {l.country}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {l.browser} ({l.operating_system})
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {l.distance_from_usual_location_km > 0 ? `${l.distance_from_usual_location_km.toLocaleString()} km` : '0 km (Local)'}
                    </td>
                    <td className="py-3 px-4">
                      {l.impossible_travel === 1 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
                          ⚡ IMPOSSIBLE
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500 font-mono">Normal</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <RiskScoreBadge score={l.analysis?.risk_score} />
                    </td>
                    <td className="py-3 px-4">
                      <SeverityBadge severity={l.analysis?.severity} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetails(l.event_id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            className="flex items-center gap-1 px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs rounded text-slate-300 border border-slate-700"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Previous
          </button>
          <span className="text-xs font-mono text-slate-400">Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            className="flex items-center gap-1 px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs rounded text-slate-300 border border-slate-700"
          >
            Next <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Login Detail Modal */}
      {selectedLogin && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-3xl w-full p-6 space-y-6 shadow-2xl my-8">
            
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {selectedLogin.event_id}
                  </span>
                  <SeverityBadge severity={selectedLogin.analysis?.severity} />
                  <RiskScoreBadge score={selectedLogin.analysis?.risk_score} />
                </div>
                <h2 className="text-lg font-bold text-slate-100 mt-2">
                  Sign-In Telemetry: {selectedLogin.city}, {selectedLogin.country}
                </h2>
                <p className="text-xs text-slate-400">
                  User Account: <span className="text-slate-200 font-mono">{selectedLogin.user_id}</span> | Timestamp: {new Date(selectedLogin.timestamp).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedLogin(null)}
                className="text-slate-400 hover:text-slate-200 text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            {/* Impossible Travel Alarm Banner */}
            {selectedLogin.impossible_travel === 1 && (
              <div className="bg-rose-500/10 border border-rose-500/40 p-3.5 rounded-lg flex items-center gap-3 text-rose-300">
                <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 animate-bounce" />
                <div className="text-xs">
                  <strong className="block font-semibold">IMPOSSIBLE TRAVEL ALARM DETECTED</strong>
                  User transitioned <span className="font-mono font-bold text-white">{selectedLogin.distance_from_usual_location_km.toLocaleString()} km</span> within <span className="font-mono font-bold text-white">{selectedLogin.minutes_since_previous_login} minutes</span>, exceeding physical transport velocity.
                </div>
              </div>
            )}

            {/* Geographic & Device Telemetry Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/80 p-3.5 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">IP Address</span>
                <span className="text-slate-200 font-mono font-bold">{selectedLogin.ip_address}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Device Type</span>
                <span className="text-slate-300 capitalize">{selectedLogin.device_type}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Operating System</span>
                <span className="text-slate-300">{selectedLogin.operating_system}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Browser</span>
                <span className="text-slate-300">{selectedLogin.browser}</span>
              </div>
            </div>

            {/* Authentication Breakdown */}
            <div className="grid grid-cols-3 gap-3 bg-slate-950/70 p-3.5 rounded-lg border border-slate-800 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Outcome</span>
                <span className={`font-bold ${selectedLogin.login_success === 1 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {selectedLogin.login_success === 1 ? 'SUCCESS (Authenticated)' : 'FAILED (Rejected)'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Preceding Failed Attempts</span>
                <span className="text-slate-200 font-bold">{selectedLogin.failed_attempts}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Unrecognized Device</span>
                <span className="text-slate-200 font-bold">{selectedLogin.is_new_device === 1 ? 'YES' : 'NO'}</span>
              </div>
            </div>

            {/* Explainable Decision Factors */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                Model Anomaly Score & Triggered Heuristics
              </h3>

              {/* Component breakdown */}
              {selectedLogin.analysis && (
                <div className="grid grid-cols-4 gap-2 text-xs bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  <div>
                    <span className="text-slate-400 text-[10px]">Location (35%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedLogin.analysis.location_risk}/100</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px]">Device (30%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedLogin.analysis.device_risk}/100</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px]">Auth (20%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedLogin.analysis.auth_risk}/100</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px]">Behavior (15%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedLogin.analysis.behavior_risk}/100</div>
                  </div>
                </div>
              )}

              <ul className="space-y-1.5">
                {selectedLogin.analysis?.reasons?.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-amber-400 font-bold mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Recommended Containment Actions */}
            <div className="bg-amber-500/5 border border-amber-500/20 p-4 rounded-lg">
              <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider font-mono mb-2">
                Recommended Incident Response Actions
              </h4>
              <ul className="space-y-1">
                {selectedLogin.analysis?.recommended_actions?.map((act, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                    <CheckCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end pt-4 border-t border-slate-800">
              <button
                onClick={() => setSelectedLogin(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-200 transition"
              >
                Close Inspector
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Live Anomaly Simulator Sandbox */}
      {showSandbox && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-2xl w-full p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Simulate Real-Time Login Telemetry</span>
              </h2>
              <button onClick={() => { setShowSandbox(false); setSandboxResult(null); }} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <form onSubmit={handleRunSandbox} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Target User ID</label>
                  <input
                    type="text"
                    value={sandboxForm.user_id}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, user_id: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Simulated IP Address</label>
                  <input
                    type="text"
                    value={sandboxForm.ip_address}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, ip_address: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Country</label>
                  <input
                    type="text"
                    value={sandboxForm.country}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, country: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">City</label>
                  <input
                    type="text"
                    value={sandboxForm.city}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, city: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Distance (km)</label>
                  <input
                    type="number"
                    value={sandboxForm.distance_from_usual_location_km}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, distance_from_usual_location_km: parseFloat(e.target.value) })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Minutes Gap</label>
                  <input
                    type="number"
                    value={sandboxForm.minutes_since_previous_login}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, minutes_since_previous_login: parseFloat(e.target.value) })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Failed Attempts</label>
                  <input
                    type="number"
                    value={sandboxForm.failed_attempts}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, failed_attempts: parseInt(e.target.value) })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Impossible Travel</label>
                  <select
                    value={sandboxForm.impossible_travel}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, impossible_travel: parseInt(e.target.value) })}
                    className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  >
                    <option value={1}>Yes (Impossible Speed)</option>
                    <option value={0}>No (Normal Velocity)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Browser / Client</label>
                  <input
                    type="text"
                    value={sandboxForm.browser}
                    onChange={(e) => setSandboxForm({ ...sandboxForm, browser: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={sandboxLoading}
                className="w-full py-2 bg-amber-600 hover:bg-amber-500 font-semibold rounded text-xs text-white transition flex items-center justify-center gap-2"
              >
                {sandboxLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                <span>Evaluate with Isolation Forest Model</span>
              </button>
            </form>

            {/* Results display */}
            {sandboxResult && (
              <div className="mt-4 p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-200">Anomaly Status:</span>
                    <span className={`px-2 py-0.5 rounded font-mono text-xs uppercase font-bold ${
                      sandboxResult.analysis?.is_suspicious
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {sandboxResult.analysis?.is_suspicious ? 'ANOMALOUS / SUSPICIOUS' : 'NORMAL'}
                    </span>
                  </div>
                  <RiskScoreBadge score={sandboxResult.analysis?.risk_score} />
                </div>
                <div className="text-xs text-slate-300 space-y-1">
                  <div className="text-[11px] text-slate-400 font-mono">Explainable Factors:</div>
                  {sandboxResult.analysis?.reasons?.map((r, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-slate-300">
                      <span className="text-amber-400">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
