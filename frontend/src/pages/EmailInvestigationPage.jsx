import React, { useState, useEffect, useCallback } from 'react';
import { 
  Mail, 
  Search, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight,
  Send,
  Lock,
  Globe,
  Inbox,
  Link2,
  Unlink2,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  ExternalLink
} from 'lucide-react';
import { 
  fetchEmails, 
  fetchEmailDetails, 
  analyzeCustomEmail, 
  reanalyzeEmail, 
  connectGmail, 
  disconnectGmail, 
  syncGmailInbox 
} from '../services/api';
import { SeverityBadge, RiskScoreBadge, SimulatedDataBanner } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

export default function EmailInvestigationPage() {
  const { user } = useAuth();
  const isGmailUser = Boolean(user && (user.gmail_connected || user.google_sub || user.email?.includes('@gmail.com')));
  const [activeTab, setActiveTab] = useState(isGmailUser ? 'my_gmail' : 'synthetic');

  const [emails, setEmails] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [filterClass, setFilterClass] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortDir, setSortDir] = useState('desc');

  // Selected Email Drawer / Modal
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);

  // Live Analyzer Modal / Form
  const [showAnalyzer, setShowAnalyzer] = useState(false);

  // Gmail sync states
  const [syncingGmail, setSyncingGmail] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');
  const [connectingGmail, setConnectingGmail] = useState(false);

  const [analyzerForm, setAnalyzerForm] = useState({
    user_id: user?.email || 'USER-1002',
    sender_name: 'IT Helpdesk Support',
    sender_email: 'support@campus-auth-security.xyz',
    email_subject: 'CRITICAL: Account Credentials Verification Required',
    email_body: 'Our security gateway flagged an unauthorized login attempt on your university portal. Please verify your identity immediately to prevent account suspension: https://campus-auth-security.xyz/verify-token',
    urls: 'https://campus-auth-security.xyz/verify-token',
    link_count: 1,
    has_attachment: 0,
    attachment_type: 'none',
    spf_result: 'fail',
    dkim_result: 'fail',
    dmarc_result: 'fail',
    display_name_mismatch: 1,
  });
  const [analyzerResult, setAnalyzerResult] = useState(null);
  const [analyzerLoading, setAnalyzerLoading] = useState(false);

  const loadEmails = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        limit: 20,
        search: search || undefined,
        predicted_class: filterClass || undefined,
        severity: filterSeverity || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        data_source: activeTab === 'synthetic' ? 'synthetic' : undefined,
      };

      const data = await fetchEmails(params);
      setEmails(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to load emails:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filterClass, filterSeverity, sortBy, sortDir, activeTab]);

  useEffect(() => {
    loadEmails();
  }, [loadEmails]);

  // Sync real emails from Gmail API
  const handleSyncGmail = async () => {
    try {
      setSyncingGmail(true);
      setSyncMessage('');
      const res = await syncGmailInbox();
      setSyncMessage(res.message || `Successfully synced ${res.synced_count} emails.`);
      await loadEmails();
    } catch (err) {
      console.error('Failed to sync Gmail:', err);
      const detail = err.response?.data?.detail || 'Failed to sync emails from Gmail API.';
      setSyncMessage(detail);
    } finally {
      setSyncingGmail(false);
    }
  };

  const handleConnectGmail = async () => {
    try {
      setConnectingGmail(true);
      setSyncMessage('');
      const data = await connectGmail();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to initiate Gmail connection.';
      setSyncMessage(detail);
      setConnectingGmail(false);
    }
  };

  const handleDisconnectGmail = async () => {
    try {
      await disconnectGmail();
      loadEmails();
    } catch (err) {
      console.error('Failed to disconnect Gmail:', err);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadEmails();
  };

  const handleOpenDetails = async (emailId) => {
    try {
      setDetailLoading(true);
      const data = await fetchEmailDetails(emailId);
      setSelectedEmail(data);
    } catch (err) {
      console.error('Failed to load email details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleReanalyze = async (emailId) => {
    try {
      setReanalyzing(true);
      const updated = await reanalyzeEmail(emailId);
      setSelectedEmail(updated);
      loadEmails();
    } catch (err) {
      console.error('Failed to reanalyze email:', err);
    } finally {
      setReanalyzing(false);
    }
  };

  const handleRunAnalyzer = async (e) => {
    e.preventDefault();
    try {
      setAnalyzerLoading(true);
      const result = await analyzeCustomEmail(analyzerForm);
      setAnalyzerResult(result);
      loadEmails();
    } catch (err) {
      console.error('Analyzer error:', err);
    } finally {
      setAnalyzerLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Mail className="w-6 h-6 text-sky-400" />
            <span>Email Phishing Investigation</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Supervised TF-IDF classification and explainable header, URL, and sender authentication risk analysis.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setAnalyzerForm(prev => ({
                ...prev,
                user_id: user?.email || 'MY-GMAIL-USER'
              }));
              setShowAnalyzer(true);
            }}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white shadow-md shadow-sky-600/20 transition cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Live Phishing Tester</span>
          </button>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-1 p-1 bg-slate-900/90 rounded-xl border border-slate-800">
          <button
            onClick={() => { setActiveTab('my_gmail'); setPage(1); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
              activeTab === 'my_gmail'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>My Gmail Account ({user?.email || 'Personal'})</span>
            {user?.gmail_connected && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            )}
          </button>
          <button
            onClick={() => { setActiveTab('synthetic'); setPage(1); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
              activeTab === 'synthetic'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Campus Benchmark Dataset (Synthetic)</span>
          </button>
        </div>

        {/* Sync or Connect Button for Real Gmail */}
        {activeTab === 'my_gmail' && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleConnectGmail}
              disabled={connectingGmail}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition cursor-pointer"
              title="Grant or Refresh Gmail Permissions with Google"
            >
              <Link2 className="w-3.5 h-3.5 text-sky-400" />
              <span>{connectingGmail ? 'Redirecting...' : 'Grant / Refresh Gmail Scope'}</span>
            </button>
            <button
              onClick={handleSyncGmail}
              disabled={syncingGmail}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncingGmail ? 'animate-spin' : ''}`} />
              <span>{syncingGmail ? 'Syncing Gmail...' : 'Sync Real Emails Now'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Active Mailbox Status Banner */}
      {activeTab === 'my_gmail' ? (
        <div className="space-y-3">
          <div className="cyber-card p-4 border border-emerald-500/30 bg-emerald-950/20 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-100">Live Gmail Account:</span>
                  <span className="font-mono text-xs text-emerald-300 font-semibold">{user?.email || 'Logged In Account'}</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                    REAL MAILS FILTER ACTIVE
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Showing emails directly from your Google account evaluated by the AI Phishing Detector.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center">
              <button
                onClick={handleSyncGmail}
                disabled={syncingGmail}
                className="px-3 py-1.5 bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
              >
                <RefreshCw className={`w-3 h-3 ${syncingGmail ? 'animate-spin' : ''}`} />
                <span>Sync</span>
              </button>
            </div>
          </div>

          {/* Sync status alert if error or message */}
          {syncMessage && (
            <div className={`text-xs p-3.5 rounded-xl border flex items-start gap-3 ${
              syncMessage.toLowerCase().includes('error') || syncMessage.toLowerCase().includes('denied') || syncMessage.toLowerCase().includes('not enabled') || syncMessage.toLowerCase().includes('failed')
                ? 'text-rose-200 bg-rose-950/70 border-rose-500/50'
                : 'text-emerald-300 bg-emerald-950/70 border-emerald-500/40'
            }`}>
              {syncMessage.toLowerCase().includes('error') || syncMessage.toLowerCase().includes('denied') || syncMessage.toLowerCase().includes('not enabled') ? (
                <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
              ) : (
                <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
              )}
              <div className="space-y-1 flex-1">
                <p className="font-semibold">{syncMessage}</p>
                {syncMessage.includes('console.cloud.google.com') && (
                  <p className="pt-1">
                    <a
                      href="https://console.cloud.google.com/apis/library/gmail.googleapis.com"
                      target="_blank"
                      rel="noreferrer"
                      className="text-sky-400 hover:underline font-semibold inline-flex items-center gap-1"
                    >
                      Click here to open Google Cloud Console and Enable Gmail API <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </p>
                )}
                {syncMessage.includes('Permission Denied') && (
                  <button
                    onClick={handleConnectGmail}
                    className="mt-2 px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium text-xs cursor-pointer inline-flex items-center gap-1"
                  >
                    <Link2 className="w-3 h-3" />
                    <span>Click here to Authorize Gmail Read Permission</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <SimulatedDataBanner />
      )}

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="relative lg:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={activeTab === 'my_gmail' ? "Search your inbox messages..." : "Search synthetic emails..."}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Classification Filter */}
          <div>
            <select
              value={filterClass}
              onChange={(e) => { setFilterClass(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Classifications</option>
              <option value="phishing">Phishing</option>
              <option value="safe">Legitimate (Safe)</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div>
            <select
              value={filterSeverity}
              onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical (80-100)</option>
              <option value="high">High (60-79)</option>
              <option value="medium">Medium (30-59)</option>
              <option value="low">Low (0-29)</option>
            </select>
          </div>

          {/* Sort Controls */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              className="w-full px-3 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="timestamp">Sort: Newest First</option>
              <option value="risk_score">Sort: Highest Risk</option>
              <option value="email_id">Sort: Email ID</option>
            </select>
          </div>
        </form>
      </div>

      {/* Main Email Table */}
      <div className="cyber-card border border-slate-800 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">
            {activeTab === 'my_gmail' ? 'Your Gmail Messages' : 'Telemetry Records'}: <span className="font-mono text-emerald-400">{total}</span>
          </span>
          <span className="text-[11px] text-slate-500">Page {page} of {totalPages}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Subject</th>
                <th className="py-3 px-4">Sender</th>
                <th className="py-3 px-4">ML Class</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
                    Loading Emails & Threat Analysis...
                  </td>
                </tr>
              ) : emails.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 font-mono space-y-4">
                    <p className="text-sm font-semibold text-slate-300">No emails loaded for your Gmail account yet.</p>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      Click the buttons below to grant read-only permissions and sync your inbox messages.
                    </p>
                    {activeTab === 'my_gmail' && (
                      <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                        <button
                          onClick={handleConnectGmail}
                          disabled={connectingGmail}
                          className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-600/20 transition cursor-pointer flex items-center gap-2"
                        >
                          <Link2 className="w-4 h-4" />
                          <span>{connectingGmail ? 'Redirecting to Google...' : '1. Authorize Gmail Access (Google Consent)'}</span>
                        </button>
                        <button
                          onClick={handleSyncGmail}
                          disabled={syncingGmail}
                          className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-emerald-600/20 transition cursor-pointer flex items-center gap-2"
                        >
                          <RefreshCw className={`w-4 h-4 ${syncingGmail ? 'animate-spin' : ''}`} />
                          <span>{syncingGmail ? 'Syncing...' : '2. Sync & Analyze Real Emails'}</span>
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                emails.map((e) => (
                  <tr key={e.email_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 max-w-sm truncate font-medium text-slate-200">
                      {e.email_subject}
                    </td>
                    <td className="py-3 px-4 max-w-[200px] truncate text-slate-400">
                      <span className="text-slate-300 block">{e.sender_name || e.sender_email}</span>
                      <span className="text-[10px] font-mono text-slate-500">{e.sender_email}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                        e.analysis?.predicted_class === 'phishing'
                          ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                          : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {e.analysis?.predicted_class || e.label}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <RiskScoreBadge score={e.analysis?.risk_score} />
                    </td>
                    <td className="py-3 px-4">
                      <SeverityBadge severity={e.analysis?.severity} />
                    </td>
                    <td className="py-3 px-4 font-mono text-[10px]">
                      <span className={`px-1.5 py-0.5 rounded border ${
                        e.data_source === 'gmail'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-semibold'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {e.data_source === 'gmail' ? 'REAL GMAIL' : 'SYNTHETIC'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {new Date(e.timestamp).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetails(e.email_id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition cursor-pointer"
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

      {/* Email Detail Inspection Modal */}
      {selectedEmail && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-4xl w-full p-6 space-y-6 shadow-2xl my-8">
            
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                    {selectedEmail.email_id}
                  </span>
                  <SeverityBadge severity={selectedEmail.analysis?.severity} />
                  <RiskScoreBadge score={selectedEmail.analysis?.risk_score} />
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                    selectedEmail.data_source === 'gmail' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}>
                    {selectedEmail.data_source === 'gmail' ? 'REAL GMAIL MESSAGE' : 'SIMULATED'}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-slate-100 mt-2">{selectedEmail.email_subject}</h2>
                <p className="text-xs text-slate-400">
                  Target Recipient: <span className="text-slate-200 font-mono">{selectedEmail.user_id}</span> | Time: {new Date(selectedEmail.timestamp).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedEmail(null)}
                className="text-slate-400 hover:text-slate-200 text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Headers & Authentication Verification Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">Sender Domain</span>
                <span className="text-slate-300 font-mono font-medium">{selectedEmail.sender_domain}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">SPF Check</span>
                <span className={`font-mono font-semibold ${
                  selectedEmail.spf_result === 'pass' ? 'text-emerald-400' : (selectedEmail.spf_result === 'fail' ? 'text-rose-400' : 'text-slate-400')
                }`}>
                  {selectedEmail.spf_result?.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">DKIM Signature</span>
                <span className={`font-mono font-semibold ${
                  selectedEmail.dkim_result === 'pass' ? 'text-emerald-400' : (selectedEmail.dkim_result === 'fail' ? 'text-rose-400' : 'text-slate-400')
                }`}>
                  {selectedEmail.dkim_result?.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">DMARC Alignment</span>
                <span className={`font-mono font-semibold ${
                  selectedEmail.dmarc_result === 'pass' ? 'text-emerald-400' : (selectedEmail.dmarc_result === 'fail' ? 'text-rose-400' : 'text-slate-400')
                }`}>
                  {selectedEmail.dmarc_result?.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Email Body Content */}
            <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800">
              <span className="text-[10px] font-mono uppercase text-slate-500 block mb-2">Message Body Content</span>
              <p className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-60 overflow-y-auto">
                {selectedEmail.email_body}
              </p>
            </div>

            {/* Extracted URLs */}
            {selectedEmail.urls && (
              <div className="bg-rose-500/5 border border-rose-500/20 p-3 rounded-lg">
                <span className="text-[10px] font-mono uppercase text-rose-400 block mb-1">
                  Extracted URL Telemetry (Non-Clickable Defanged Format)
                </span>
                <code className="text-xs font-mono text-rose-300 select-all block bg-slate-950/80 p-2 rounded border border-rose-500/30">
                  {selectedEmail.urls}
                </code>
              </div>
            )}

            {/* Explainable Decision Factors */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                Explainable Risk Signals & Model Attribution
              </h3>
              
              {selectedEmail.analysis && (
                <div className="grid grid-cols-3 gap-3 text-xs bg-slate-900/50 p-3 rounded border border-slate-800">
                  <div>
                    <span className="text-slate-400 text-[11px]">Content NLP Risk (40%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedEmail.analysis.content_risk}/100</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px]">URL Analysis Risk (35%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedEmail.analysis.url_risk}/100</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px]">Sender / Header Risk (25%):</span>
                    <div className="font-mono font-bold text-slate-200">{selectedEmail.analysis.sender_risk}/100</div>
                  </div>
                </div>
              )}

              <ul className="space-y-1.5">
                {selectedEmail.analysis?.reasons?.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-sky-400 font-bold mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <button
                onClick={() => handleReanalyze(selectedEmail.email_id)}
                disabled={reanalyzing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-300 border border-slate-700 transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reanalyzing ? 'animate-spin' : ''}`} />
                <span>Re-run AI Analysis</span>
              </button>
              <button
                onClick={() => setSelectedEmail(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-200 transition cursor-pointer"
              >
                Close Inspector
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Live Email Phishing Analyzer Modal */}
      {showAnalyzer && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-2xl w-full p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Send className="w-4 h-4 text-sky-400" />
                <span>Real-Time Phishing Classifier Sandbox</span>
              </h2>
              <button onClick={() => { setShowAnalyzer(false); setAnalyzerResult(null); }} className="text-slate-400 hover:text-slate-200 cursor-pointer">
                ✕
              </button>
            </div>

            <form onSubmit={handleRunAnalyzer} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Recipient User</label>
                  <input
                    type="text"
                    value={analyzerForm.user_id}
                    onChange={(e) => setAnalyzerForm({ ...analyzerForm, user_id: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Sender Email</label>
                  <input
                    type="email"
                    value={analyzerForm.sender_email}
                    onChange={(e) => setAnalyzerForm({ ...analyzerForm, sender_email: e.target.value })}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Email Subject</label>
                <input
                  type="text"
                  value={analyzerForm.email_subject}
                  onChange={(e) => setAnalyzerForm({ ...analyzerForm, email_subject: e.target.value })}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Email Body Content</label>
                <textarea
                  rows={3}
                  value={analyzerForm.email_body}
                  onChange={(e) => setAnalyzerForm({ ...analyzerForm, email_body: e.target.value })}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Embedded URLs</label>
                <input
                  type="text"
                  value={analyzerForm.urls}
                  onChange={(e) => setAnalyzerForm({ ...analyzerForm, urls: e.target.value })}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">SPF Result</label>
                  <select
                    value={analyzerForm.spf_result}
                    onChange={(e) => setAnalyzerForm({ ...analyzerForm, spf_result: e.target.value })}
                    className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  >
                    <option value="pass">pass</option>
                    <option value="fail">fail</option>
                    <option value="softfail">softfail</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">DKIM Result</label>
                  <select
                    value={analyzerForm.dkim_result}
                    onChange={(e) => setAnalyzerForm({ ...analyzerForm, dkim_result: e.target.value })}
                    className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  >
                    <option value="pass">pass</option>
                    <option value="fail">fail</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Display Mismatch</label>
                  <select
                    value={analyzerForm.display_name_mismatch}
                    onChange={(e) => setAnalyzerForm({ ...analyzerForm, display_name_mismatch: parseInt(e.target.value) })}
                    className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200"
                  >
                    <option value={0}>No (0)</option>
                    <option value={1}>Yes (1)</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={analyzerLoading}
                className="w-full py-2 bg-sky-600 hover:bg-sky-500 font-semibold rounded text-xs text-white transition flex items-center justify-center gap-2 cursor-pointer"
              >
                {analyzerLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>Evaluate with ML Model</span>
              </button>
            </form>

            {/* Results display */}
            {analyzerResult && (
              <div className="mt-4 p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-200">ML Prediction:</span>
                    <span className={`px-2 py-0.5 rounded font-mono text-xs uppercase font-bold ${
                      analyzerResult.analysis?.predicted_class === 'phishing'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {analyzerResult.analysis?.predicted_class}
                    </span>
                  </div>
                  <RiskScoreBadge score={analyzerResult.analysis?.risk_score} />
                </div>
                <div className="text-xs text-slate-300 space-y-1">
                  <div className="text-[11px] text-slate-400 font-mono">Explainable Factors:</div>
                  {analyzerResult.analysis?.reasons?.map((r, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-slate-300">
                      <span className="text-sky-400">•</span>
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
