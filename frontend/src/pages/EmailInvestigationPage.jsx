import React, { useState, useEffect } from 'react';
import { 
  Mail, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle, 
  ExternalLink, 
  RefreshCw, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight,
  Send,
  Eye,
  SlidersHorizontal,
  Lock,
  Globe,
  FileText,
  Inbox,
  Link2,
  Unlink2,
  MailOpen
} from 'lucide-react';
import { fetchEmails, fetchEmailDetails, analyzeCustomEmail, reanalyzeEmail, fetchGmailMessages, connectGmail, disconnectGmail, fetchIntegrationsStatus } from '../services/api';
import { SeverityBadge, RiskScoreBadge, SimulatedDataBanner } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

export default function EmailInvestigationPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('synthetic'); // 'synthetic' | 'gmail'
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

  // Gmail state
  const [gmailMessages, setGmailMessages] = useState([]);
  const [gmailLoading, setGmailLoading] = useState(false);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailStatus, setGmailStatus] = useState('');
  const [gmailConnecting, setGmailConnecting] = useState(false);
  const [selectedGmailMsg, setSelectedGmailMsg] = useState(null);
  const [analyzerForm, setAnalyzerForm] = useState({
    user_id: 'USER-1002',
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

  const loadEmails = async () => {
    try {
      setLoading(true);
      const data = await fetchEmails({
        page,
        limit: 20,
        search: search || undefined,
        predicted_class: filterClass || undefined,
        severity: filterSeverity || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      });
      setEmails(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load emails:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmails();
  }, [page, filterClass, filterSeverity, sortBy, sortDir]);

  // Gmail integration
  const loadGmailStatus = async () => {
    try {
      const data = await fetchIntegrationsStatus();
      setGmailConnected(data.gmail?.connected || false);
    } catch (err) {
      console.error('Failed to load integrations status:', err);
    }
  };

  const loadGmailMessages = async () => {
    try {
      setGmailLoading(true);
      const data = await fetchGmailMessages();
      setGmailConnected(data.connected);
      setGmailMessages(data.messages || []);
      setGmailStatus(data.message || '');
    } catch (err) {
      console.error('Failed to load Gmail messages:', err);
      setGmailStatus('Failed to fetch Gmail messages.');
    } finally {
      setGmailLoading(false);
    }
  };

  const handleConnectGmail = async () => {
    try {
      setGmailConnecting(true);
      const data = await connectGmail();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to initiate Gmail connection.';
      setGmailStatus(detail);
      setGmailConnecting(false);
    }
  };

  const handleDisconnectGmail = async () => {
    try {
      await disconnectGmail();
      setGmailConnected(false);
      setGmailMessages([]);
      setGmailStatus('Gmail disconnected successfully.');
    } catch (err) {
      console.error('Failed to disconnect Gmail:', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'gmail') {
      loadGmailStatus();
      loadGmailMessages();
    }
  }, [activeTab]);

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
      loadEmails(); // Refresh list to include ad-hoc event
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
            onClick={() => setShowAnalyzer(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white shadow-md shadow-sky-600/20 transition"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Live Phishing Tester</span>
          </button>
        </div>
      </div>

      {/* Tab Switcher: Synthetic Data vs My Gmail */}
      <div className="flex items-center gap-1 p-1 bg-slate-900/90 rounded-xl border border-slate-800 w-fit">
        <button
          onClick={() => setActiveTab('synthetic')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
            activeTab === 'synthetic'
              ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Security Telemetry (Synthetic)</span>
        </button>
        <button
          onClick={() => setActiveTab('gmail')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
            activeTab === 'gmail'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Inbox className="w-3.5 h-3.5" />
          <span>My Gmail Inbox</span>
          {gmailConnected && (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          )}
        </button>
      </div>

      {activeTab === 'synthetic' && (
      <>
      <SimulatedDataBanner />

      {/* Filter and Search Bar */}
      <div className="cyber-card p-4 border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="relative lg:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by subject, sender, or user ID..."
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

      {/* Email Table */}
      <div className="cyber-card border border-slate-800 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">
            Total Telemetry Records: <span className="font-mono text-sky-400">{total}</span>
          </span>
          <span className="text-[11px] text-slate-500">Page {page} of {totalPages}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Email ID</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Subject</th>
                <th className="py-3 px-4">Sender</th>
                <th className="py-3 px-4">ML Class</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
                    Fetching Email Telemetry...
                  </td>
                </tr>
              ) : emails.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500 font-mono">
                    No email records found matching the query criteria.
                  </td>
                </tr>
              ) : (
                emails.map((e) => (
                  <tr key={e.email_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-sky-400">{e.email_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{e.user_id}</td>
                    <td className="py-3 px-4 max-w-xs truncate font-medium text-slate-200">
                      {e.email_subject}
                    </td>
                    <td className="py-3 px-4 max-w-[180px] truncate text-slate-400">
                      {e.sender_email}
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
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {new Date(e.timestamp).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetails(e.email_id)}
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
      </>
      )}

      {/* ===== GMAIL TAB ===== */}
      {activeTab === 'gmail' && (
        <div className="space-y-5">
          {/* Gmail Connection Status Card */}
          <div className="cyber-card p-5 border border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  gmailConnected 
                    ? 'bg-emerald-500/15 border border-emerald-500/30' 
                    : 'bg-slate-800 border border-slate-700'
                }`}>
                  <Inbox className={`w-5 h-5 ${gmailConnected ? 'text-emerald-400' : 'text-slate-400'}`} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">Gmail Integration</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {gmailConnected 
                      ? `Connected as ${user?.email || 'your account'} — Read-Only access (gmail.readonly)`
                      : 'Connect your Gmail to view real inbox messages. Uses read-only access — we never modify your mail.'
                    }
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {gmailConnected ? (
                  <>
                    <button
                      onClick={loadGmailMessages}
                      disabled={gmailLoading}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg text-slate-300 border border-slate-700 transition"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${gmailLoading ? 'animate-spin' : ''}`} />
                      <span>Refresh</span>
                    </button>
                    <button
                      onClick={handleDisconnectGmail}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-xs rounded-lg text-rose-300 border border-rose-500/30 transition"
                    >
                      <Unlink2 className="w-3.5 h-3.5" />
                      <span>Disconnect</span>
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleConnectGmail}
                    disabled={gmailConnecting}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold rounded-lg text-white shadow-md shadow-emerald-600/20 transition"
                  >
                    <Link2 className="w-3.5 h-3.5" />
                    <span>{gmailConnecting ? 'Connecting...' : 'Connect Gmail'}</span>
                  </button>
                )}
              </div>
            </div>
            {gmailStatus && !gmailConnected && (
              <div className="mt-3 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                {gmailStatus}
              </div>
            )}
          </div>

          {/* Gmail Messages */}
          {gmailConnected && (
            <div className="cyber-card border border-slate-800 overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                  <MailOpen className="w-3.5 h-3.5 text-emerald-400" />
                  Live Gmail Messages
                  <span className="font-mono text-emerald-400">({gmailMessages.length})</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  REAL DATA — READ-ONLY
                </span>
              </div>

              {gmailLoading ? (
                <div className="py-16 text-center">
                  <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-3 text-emerald-400" />
                  <p className="text-sm text-slate-400 font-mono">Fetching from Gmail API...</p>
                </div>
              ) : gmailMessages.length === 0 ? (
                <div className="py-16 text-center text-slate-500 text-sm font-mono">
                  No messages loaded. Your inbox may be empty or the token may have expired.
                </div>
              ) : (
                <div className="divide-y divide-slate-800/60">
                  {gmailMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className="px-5 py-4 hover:bg-slate-800/30 transition cursor-pointer"
                      onClick={() => setSelectedGmailMsg(selectedGmailMsg?.id === msg.id ? null : msg)}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-slate-200 truncate">
                              {msg.sender}
                            </span>
                            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 shrink-0">
                              {msg.data_source === 'real_gmail_oauth' ? 'LIVE' : 'GMAIL'}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-slate-100 truncate">
                            {msg.subject}
                          </p>
                          <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                            {msg.snippet}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-[11px] font-mono text-slate-500">
                            {msg.date ? new Date(parseInt(msg.date)).toLocaleDateString() : ''}
                          </div>
                        </div>
                      </div>
                      
                      {/* Expanded detail view */}
                      {selectedGmailMsg?.id === msg.id && (
                        <div className="mt-3 p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-3">
                          <div className="grid grid-cols-2 gap-3 text-xs">
                            <div>
                              <span className="text-slate-500 block text-[10px] uppercase font-mono">From</span>
                              <span className="text-slate-300">{msg.sender}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block text-[10px] uppercase font-mono">Subject</span>
                              <span className="text-slate-300">{msg.subject}</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase font-mono mb-1">Snippet / Preview</span>
                            <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-900/60 p-3 rounded border border-slate-800">
                              {msg.snippet}
                            </p>
                          </div>
                          <p className="text-[10px] text-emerald-400 font-mono">
                            ✓ This is a real message fetched securely via Google Gmail API (read-only scope)
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {gmailConnected && gmailMessages.length > 0 && (
                <div className="px-5 py-3 border-t border-slate-800 text-center">
                  <p className="text-[11px] text-slate-500 font-mono">
                    Showing latest {gmailMessages.length} messages • gmail.readonly scope • No emails are stored permanently
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Not Connected Empty State */}
          {!gmailConnected && !gmailLoading && (
            <div className="cyber-card border border-slate-800 py-16 text-center space-y-4">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                <Mail className="w-8 h-8 text-slate-500" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-200">Connect Your Gmail</h3>
                <p className="text-xs text-slate-400 mt-2 max-w-md mx-auto">
                  Click "Connect Gmail" above to authorize read-only access to your mailbox.
                  Your emails will be fetched live from the Gmail API — nothing is stored on our server.
                </p>
              </div>
              <div className="flex items-center justify-center gap-3 text-[11px] text-slate-500 font-mono">
                <span className="flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Read-Only
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Globe className="w-3 h-3" /> OAuth 2.0
                </span>
                <span>•</span>
                <span>gmail.readonly scope</span>
              </div>
            </div>
          )}
        </div>
      )}

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
                </div>
                <h2 className="text-lg font-bold text-slate-100 mt-2">{selectedEmail.email_subject}</h2>
                <p className="text-xs text-slate-400">
                  Target Recipient: <span className="text-slate-200 font-mono">{selectedEmail.user_id}</span> | Time: {new Date(selectedEmail.timestamp).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedEmail(null)}
                className="text-slate-400 hover:text-slate-200 text-lg font-bold p-1"
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
                  selectedEmail.spf_result === 'pass' ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {selectedEmail.spf_result.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">DKIM Signature</span>
                <span className={`font-mono font-semibold ${
                  selectedEmail.dkim_result === 'pass' ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {selectedEmail.dkim_result.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-mono">DMARC Alignment</span>
                <span className={`font-mono font-semibold ${
                  selectedEmail.dmarc_result === 'pass' ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {selectedEmail.dmarc_result.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Email Body Content */}
            <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800">
              <span className="text-[10px] font-mono uppercase text-slate-500 block mb-2">Message Body Content</span>
              <p className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
                {selectedEmail.email_body}
              </p>
            </div>

            {/* Non-Clickable Extracted URLs */}
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
              
              {/* Component breakdown bars */}
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

            {/* Recommended Response Actions */}
            <div className="bg-sky-500/5 border border-sky-500/20 p-4 rounded-lg">
              <h4 className="text-xs font-bold text-sky-400 uppercase tracking-wider font-mono mb-2">
                Recommended Incident Response Actions
              </h4>
              <ul className="space-y-1">
                {selectedEmail.analysis?.recommended_actions?.map((act, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                    <CheckCircle className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Related Logins for Same User */}
            {selectedEmail.related_logins && selectedEmail.related_logins.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono mb-2">
                  Correlated User Logins ({selectedEmail.user_id})
                </h4>
                <div className="space-y-1.5">
                  {selectedEmail.related_logins.map(l => (
                    <div key={l.event_id} className="flex items-center justify-between p-2 bg-slate-900/60 border border-slate-800 rounded text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-400">{l.event_id}</span>
                        <span className="text-slate-200">{l.location} ({l.ip_address})</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <RiskScoreBadge score={l.risk_score} />
                        <SeverityBadge severity={l.severity} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modal Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <button
                onClick={() => handleReanalyze(selectedEmail.email_id)}
                disabled={reanalyzing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-300 border border-slate-700 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reanalyzing ? 'animate-spin' : ''}`} />
                <span>Re-run AI Analysis</span>
              </button>
              <button
                onClick={() => setSelectedEmail(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-200 transition"
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
              <button onClick={() => { setShowAnalyzer(false); setAnalyzerResult(null); }} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <form onSubmit={handleRunAnalyzer} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Recipient User ID</label>
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
                className="w-full py-2 bg-sky-600 hover:bg-sky-500 font-semibold rounded text-xs text-white transition flex items-center justify-center gap-2"
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
