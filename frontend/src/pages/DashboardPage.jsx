import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  Mail, 
  LogIn, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Activity, 
  ArrowRight, 
  ShieldCheck,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { fetchDashboardSummary, fetchDashboardCharts, fetchDashboardActivity } from '../services/api';
import { SeverityBadge, SimulatedDataBanner } from '../components/Badges';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all');

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumData, chartData, actData] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardCharts(),
        fetchDashboardActivity(),
      ]);
      setSummary(sumData);
      setCharts(chartData);
      setActivity(actData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to connect to backend API. Please ensure FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const filteredActivity = activity.filter(item => {
    if (activeTab === 'all') return true;
    return item.type === activeTab;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm font-mono">Loading Security Telemetry & Live ML Models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-12 p-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-center">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-rose-300 mb-2">Backend Connection Error</h3>
        <p className="text-slate-400 text-sm mb-4">{error}</p>
        <button
          onClick={loadDashboard}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <span>Security Operations Center</span>
            <span className="text-xs font-mono font-normal text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
              LIVE MONITORING
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time phishing email classification, suspicious login anomaly triage, and correlated incidents.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadDashboard}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Telemetry</span>
          </button>
          <Link
            to="/incidents"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-medium text-white shadow-md shadow-sky-600/20 transition"
          >
            <span>Triage Incidents ({summary?.open_incidents || 0})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      <SimulatedDataBanner />

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Emails Analyzed */}
        <div className="cyber-card p-5 border border-slate-800 hover:border-sky-500/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Emails Analyzed</span>
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <Mail className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-100 font-mono">
              {summary?.total_emails_analyzed?.toLocaleString()}
            </span>
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> TF-IDF Active
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            <span className="text-rose-400 font-semibold">{summary?.phishing_emails_detected}</span> flagged as phishing ({summary?.phishing_ratio_percent}%)
          </p>
        </div>

        {/* Suspicious Logins */}
        <div className="cyber-card p-5 border border-slate-800 hover:border-amber-500/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Logins Monitored</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <LogIn className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-100 font-mono">
              {summary?.total_logins_monitored?.toLocaleString()}
            </span>
            <span className="text-xs font-mono text-amber-400">
              {summary?.suspicious_logins_detected} Anomalies
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Isolation Forest + Geographic & Impossible Travel checks
          </p>
        </div>

        {/* Correlated Incidents */}
        <div className="cyber-card p-5 border border-slate-800 hover:border-rose-500/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Incidents</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-100 font-mono">
              {summary?.total_incidents}
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/20">
              {summary?.open_incidents} Open
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            <span className="text-rose-400 font-semibold">{summary?.high_risk_incidents}</span> high/critical priority
          </p>
        </div>

        {/* Incidents Resolved */}
        <div className="cyber-card p-5 border border-slate-800 hover:border-emerald-500/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Resolved / Contained</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-100 font-mono">
              {summary?.resolved_incidents}
            </span>
            <span className="text-xs font-mono text-emerald-400">Simulated SOC</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Audit logging enabled for all response actions
          </p>
        </div>

      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Email Classification Donut */}
        <div className="cyber-card p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-200">Email Classification</h3>
              <span className="text-[11px] font-mono text-slate-400">TF-IDF Model</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Ratio of detected phishing attacks vs legitimate campus communications.</p>
          </div>
          
          <div className="h-48 w-full flex items-center justify-center">
            {charts?.email_classification && (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.email_classification}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {charts.email_classification.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="flex items-center justify-center gap-6 mt-2 pt-3 border-t border-slate-800/80 text-xs font-medium">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-500"></span>
              <span className="text-slate-300">Phishing ({summary?.phishing_emails_detected})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
              <span className="text-slate-300">Safe ({summary ? summary.total_emails_analyzed - summary.phishing_emails_detected : 0})</span>
            </div>
          </div>
        </div>

        {/* Login Anomaly Risk Breakdown */}
        <div className="cyber-card p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-200">Login Severity Distribution</h3>
              <span className="text-[11px] font-mono text-slate-400">Isolation Forest</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Risk tiers derived from geographical, device, and behavioral anomalies.</p>
          </div>

          <div className="h-48 w-full">
            {charts?.login_risk_distribution && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.login_risk_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {charts.login_risk_distribution.map((entry, index) => (
                      <Cell key={`cell-bar-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs text-slate-400">
            <span>Low: Regular sign-ins</span>
            <span className="text-amber-400">High/Crit: Unseen device/IP</span>
          </div>
        </div>

        {/* Incident Status Breakdown */}
        <div className="cyber-card p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-200">Incident Severity Status</h3>
              <span className="text-[11px] font-mono text-slate-400">Correlation Engine</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Multi-factor correlated attack chains by severity.</p>
          </div>

          <div className="h-48 w-full">
            {charts?.incident_severity && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.incident_severity} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {charts.incident_severity.map((entry, index) => (
                      <Cell key={`cell-inc-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs text-slate-400">
            <span>24h Sliding Correlation Window</span>
            <Link to="/incidents" className="text-sky-400 hover:underline flex items-center gap-1">
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

      </div>

      {/* Live Activity & Alerts Feed */}
      <div className="cyber-card p-6 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              <span>Recent Threat & Telemetry Feed</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Live events analyzed by backend machine learning models.</p>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
            {['all', 'incident', 'email', 'login'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded-md capitalize transition ${
                  activeTab === tab
                    ? 'bg-sky-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab === 'all' ? 'All Events' : `${tab}s`}
              </button>
            ))}
          </div>
        </div>

        {/* Feed List */}
        <div className="divide-y divide-slate-800/60 mt-3">
          {filteredActivity.length === 0 ? (
            <p className="py-8 text-center text-xs text-slate-500 font-mono">No recent events found matching filter.</p>
          ) : (
            filteredActivity.map((item) => (
              <div key={item.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/30 px-2 rounded-lg transition">
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 p-2 rounded-lg ${
                    item.type === 'incident' ? 'bg-rose-500/10 text-rose-400' :
                    item.type === 'email' ? 'bg-sky-500/10 text-sky-400' : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {item.type === 'incident' ? <AlertTriangle className="w-4 h-4" /> :
                     item.type === 'email' ? <Mail className="w-4 h-4" /> : <LogIn className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-200">{item.title}</span>
                      <SeverityBadge severity={item.severity} />
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-[11px] font-mono text-slate-500">
                      <span>ID: {item.id}</span>
                      {item.user_id && <span>User: {item.user_id}</span>}
                      <span>{new Date(item.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Link
                    to={
                      item.type === 'incident' ? `/incidents?id=${item.id}` :
                      item.type === 'email' ? `/emails?id=${item.id}` : `/logins?id=${item.id}`
                    }
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-slate-300 border border-slate-700 transition"
                  >
                    <span>Investigate</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
