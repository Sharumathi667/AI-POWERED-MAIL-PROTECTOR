import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  User, 
  ShieldAlert, 
  Check, 
  X, 
  MessageSquare, 
  Activity, 
  FileText, 
  RefreshCw, 
  Search, 
  Filter, 
  ArrowRight,
  Send,
  Zap,
  Lock,
  Layers
} from 'lucide-react';
import { 
  fetchIncidents, 
  fetchIncidentDetails, 
  updateIncident, 
  addIncidentNote, 
  fetchIncidentTimeline,
  approveAction,
  rejectAction,
  previewAction
} from '../services/api';
import { SeverityBadge, RiskScoreBadge, IncidentStatusBadge, SimulatedDataBanner } from '../components/Badges';

export default function IncidentInvestigationPage() {
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id');

  const [incidents, setIncidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Selected Incident & Sub-data
  const [selectedId, setSelectedId] = useState(initialId || null);
  const [incidentDetail, setIncidentDetail] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // New Note State
  const [newNote, setNewNote] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);

  // Action Preview Modal
  const [previewData, setPreviewData] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await fetchIncidents({
        page,
        limit: 25,
        search: search || undefined,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      });
      setIncidents(data.items);
      setTotal(data.total);

      // Default select first incident if none selected
      if (!selectedId && data.items.length > 0) {
        setSelectedId(data.items[0].incident_id);
      }
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadIncidentDetail = async (incId) => {
    if (!incId) return;
    try {
      setDetailLoading(true);
      const [detail, tl] = await Promise.all([
        fetchIncidentDetails(incId),
        fetchIncidentTimeline(incId),
      ]);
      setIncidentDetail(detail);
      setTimeline(tl);
    } catch (err) {
      console.error('Failed to load incident detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [page, statusFilter, severityFilter]);

  useEffect(() => {
    if (selectedId) {
      loadIncidentDetail(selectedId);
    }
  }, [selectedId]);

  const handleStatusChange = async (newStatus) => {
    if (!selectedId) return;
    try {
      const updated = await updateIncident(selectedId, { status: newStatus });
      setIncidentDetail(updated);
      loadIncidents(); // Refresh queue
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleAssignAnalyst = async (analystName) => {
    if (!selectedId) return;
    try {
      const updated = await updateIncident(selectedId, { assigned_analyst: analystName });
      setIncidentDetail(updated);
      loadIncidents();
    } catch (err) {
      console.error('Failed to assign analyst:', err);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim() || !selectedId) return;
    try {
      setSubmittingNote(true);
      await addIncidentNote(selectedId, {
        author: 'Lead SOC Analyst',
        note_text: newNote.trim(),
      });
      setNewNote('');
      loadIncidentDetail(selectedId);
    } catch (err) {
      console.error('Failed to add note:', err);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handlePreviewAction = async (action) => {
    try {
      const p = await previewAction({
        action_type: action.action_type,
        target: action.target,
      });
      setPreviewData({ ...p, action_id: action.action_id, title: action.title });
    } catch (err) {
      console.error('Failed to preview action:', err);
    }
  };

  const handleApproveAction = async (actionId) => {
    try {
      setActionInProgress(true);
      await approveAction(actionId, {
        analyst_name: 'Lead SOC Analyst',
        notes: 'Simulated containment executed and logged to audit trail.',
      });
      setPreviewData(null);
      loadIncidentDetail(selectedId);
      loadIncidents();
    } catch (err) {
      console.error('Failed to approve action:', err);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleRejectAction = async (actionId) => {
    try {
      setActionInProgress(true);
      await rejectAction(actionId, {
        analyst_name: 'Lead SOC Analyst',
        notes: 'Rejected after analyst review.',
      });
      setPreviewData(null);
      loadIncidentDetail(selectedId);
      loadIncidents();
    } catch (err) {
      console.error('Failed to reject action:', err);
    } finally {
      setActionInProgress(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-rose-400" />
            <span>Incident Triage & Response</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Correlated multi-event attacks combining phishing telemetry and suspicious sign-ins into actionable security cases.
          </p>
        </div>
      </div>

      <SimulatedDataBanner />

      {/* Main 2-Column Incident Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Incidents List Queue (4 cols) */}
        <div className="lg:col-span-4 cyber-card p-4 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-slate-200">Incident Queue ({total})</h2>
            <button
              onClick={loadIncidents}
              className="text-slate-400 hover:text-slate-200"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Quick Filter */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700/80 rounded text-slate-300 text-xs"
            >
              <option value="">All Statuses</option>
              <option value="New">New</option>
              <option value="Investigating">Investigating</option>
              <option value="Contained">Contained</option>
              <option value="Resolved">Resolved</option>
            </select>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700/80 rounded text-slate-300 text-xs"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>

          {/* Incidents Queue Cards */}
          <div className="space-y-2 max-h-[650px] overflow-y-auto pr-1">
            {loading ? (
              <p className="text-center py-8 text-xs text-slate-500 font-mono">Loading cases...</p>
            ) : incidents.length === 0 ? (
              <p className="text-center py-8 text-xs text-slate-500 font-mono">No incidents found.</p>
            ) : (
              incidents.map((inc) => (
                <div
                  key={inc.incident_id}
                  onClick={() => setSelectedId(inc.incident_id)}
                  className={`p-3 rounded-lg border transition cursor-pointer text-xs ${
                    selectedId === inc.incident_id
                      ? 'bg-sky-500/10 border-sky-500/40 shadow-sm shadow-sky-500/10'
                      : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-[11px] text-sky-400 font-semibold">{inc.incident_id}</span>
                    <IncidentStatusBadge status={inc.status} />
                  </div>
                  <h4 className="font-semibold text-slate-200 line-clamp-1">{inc.title}</h4>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                    <span className="font-mono">{inc.affected_user}</span>
                    <div className="flex items-center gap-1.5">
                      <SeverityBadge severity={inc.severity} />
                      <RiskScoreBadge score={inc.risk_score} />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Deep-Dive Incident Inspector (8 cols) */}
        <div className="lg:col-span-8 cyber-card p-6 border border-slate-800 space-y-6">
          {detailLoading ? (
            <div className="py-24 text-center text-slate-400 font-mono">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-sky-400" />
              Loading Incident Case Data...
            </div>
          ) : !incidentDetail ? (
            <div className="py-24 text-center text-slate-500">
              Select an incident from the queue to review evidence, timelines, and response actions.
            </div>
          ) : (
            <>
              {/* Header Details */}
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-xs text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                      {incidentDetail.incident_id}
                    </span>
                    <SeverityBadge severity={incidentDetail.severity} />
                    <RiskScoreBadge score={incidentDetail.risk_score} />
                    <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      Confidence: {incidentDetail.confidence}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-100">{incidentDetail.title}</h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Affected Account: <span className="font-mono text-slate-200 font-semibold">{incidentDetail.affected_user}</span> | Created: {new Date(incidentDetail.created_at).toLocaleString()}
                  </p>
                </div>

                {/* Status and Assignment Control */}
                <div className="flex flex-col sm:flex-row items-end gap-2 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  <div>
                    <label className="text-[10px] uppercase font-mono text-slate-500 block mb-1">Status</label>
                    <select
                      value={incidentDetail.status}
                      onChange={(e) => handleStatusChange(e.target.value)}
                      className="px-2.5 py-1 bg-slate-950 border border-slate-700 rounded text-xs text-slate-200 font-medium"
                    >
                      <option value="New">New</option>
                      <option value="Investigating">Investigating</option>
                      <option value="Contained">Contained</option>
                      <option value="Resolved">Resolved</option>
                      <option value="False Positive">False Positive</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] uppercase font-mono text-slate-500 block mb-1">Analyst</label>
                    <select
                      value={incidentDetail.assigned_analyst}
                      onChange={(e) => handleAssignAnalyst(e.target.value)}
                      className="px-2.5 py-1 bg-slate-950 border border-slate-700 rounded text-xs text-slate-200 font-medium"
                    >
                      <option value="Unassigned">Unassigned</option>
                      <option value="Lead SOC Analyst">Lead SOC Analyst</option>
                      <option value="Security Admin">Security Admin</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Correlation Story & Reasoning Breakdown */}
              <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800 space-y-3">
                <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider font-mono flex items-center gap-2">
                  <Layers className="w-4 h-4" />
                  <span>Correlation Story & Causality Analysis</span>
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {incidentDetail.evidence_summary}
                </p>

                {incidentDetail.reasoning?.correlation_analysis && (
                  <div className="grid grid-cols-2 gap-3 text-xs bg-slate-900/60 p-3 rounded border border-slate-800 font-mono">
                    <div>
                      <span className="text-slate-500 block text-[10px]">Temporal Proximity</span>
                      <span className="text-slate-200">
                        {incidentDetail.reasoning.correlation_analysis.time_delta_hours} hours between events
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Correlation Bonus Points</span>
                      <span className="text-rose-400 font-bold">
                        +{incidentDetail.reasoning.correlation_analysis.correlation_bonus_applied} pts
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Linked Evidence Items */}
              <div>
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono mb-2">
                  Linked Multi-Source Telemetry Evidence
                </h3>
                <div className="space-y-2">
                  {incidentDetail.evidence_items?.map((ev) => (
                    <div key={ev.id} className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase font-bold ${
                          ev.event_type === 'email' ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30' : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        }`}>
                          {ev.event_type}
                        </span>
                        <div>
                          <span className="font-semibold text-slate-200">{ev.event_id}: </span>
                          <span className="text-slate-400">{ev.evidence_desc}</span>
                        </div>
                      </div>
                      <span className="font-mono text-slate-400 text-[11px]">
                        +{ev.score_contribution.toFixed(1)} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Incident Response Actions (Simulated) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-sky-400" />
                    <span>Proposed Containment Actions</span>
                  </h3>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    SIMULATED WORKFLOW
                  </span>
                </div>

                <div className="space-y-2">
                  {incidentDetail.actions?.length === 0 ? (
                    <p className="text-xs text-slate-500 font-mono py-2">No proposed actions for this incident.</p>
                  ) : (
                    incidentDetail.actions.map((act) => (
                      <div key={act.action_id} className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-200">{act.title}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                              act.status === 'executed' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                              act.status === 'rejected' ? 'bg-slate-500/20 text-slate-400 border border-slate-500/30' :
                              'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            }`}>
                              {act.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{act.description}</p>
                          {act.execution_result && (
                            <p className="text-[11px] font-mono text-emerald-400/90 mt-1 bg-emerald-950/40 p-1.5 rounded border border-emerald-800/40">
                              {act.execution_result}
                            </p>
                          )}
                        </div>

                        {act.status === 'pending' && (
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => handlePreviewAction(act)}
                              className="px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-[11px] border border-slate-700"
                            >
                              Preview Scope
                            </button>
                            <button
                              onClick={() => handleApproveAction(act.action_id)}
                              disabled={actionInProgress}
                              className="flex items-center gap-1 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[11px] transition shadow-sm"
                            >
                              <Check className="w-3 h-3" /> Approve
                            </button>
                            <button
                              onClick={() => handleRejectAction(act.action_id)}
                              disabled={actionInProgress}
                              className="p-1.5 rounded bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-400 border border-slate-700"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Event Timeline */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                  <Clock className="w-4 h-4 text-sky-400" />
                  <span>Chronological Event Timeline</span>
                </h3>
                
                <div className="relative pl-6 space-y-4 border-l border-slate-800 ml-2">
                  {timeline.map((item, idx) => (
                    <div key={idx} className="relative group">
                      <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full bg-slate-900 border-2 border-sky-400"></span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-200 text-xs">{item.title}</span>
                          <span className="text-[10px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                            {new Date(item.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{item.details}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analyst Notes */}
              <div className="space-y-3 pt-4 border-t border-slate-800">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-sky-400" />
                  <span>Investigation Notes & Audit</span>
                </h3>

                {/* Notes List */}
                <div className="space-y-2">
                  {incidentDetail.notes?.map((n) => (
                    <div key={n.id} className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-mono">
                        <span className="font-semibold text-slate-300">{n.author}</span>
                        <span>{new Date(n.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-slate-200">{n.note_text}</p>
                    </div>
                  ))}
                </div>

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Add an investigation note, IOC analysis, or user contact log..."
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  />
                  <button
                    type="submit"
                    disabled={submittingNote || !newNote.trim()}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-xs font-semibold text-white rounded-lg transition"
                  >
                    Add Note
                  </button>
                </form>
              </div>

            </>
          )}
        </div>

      </div>

      {/* Action Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Simulated Action Impact Assessment</span>
              </h3>
              <button onClick={() => setPreviewData(null)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-slate-950 p-3 rounded border border-slate-800 font-mono">
                <div className="text-slate-500">Action: <span className="text-slate-200 font-bold">{previewData.title}</span></div>
                <div className="text-slate-500">Target: <span className="text-sky-400">{previewData.target}</span></div>
                <div className="text-slate-500">Scope: <span className="text-amber-400">{previewData.impact_scope}</span></div>
              </div>

              <p className="text-slate-300 leading-relaxed">
                {previewData.estimated_impact}
              </p>

              <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded text-sky-300 text-[11px]">
                <strong>Safety Guarantee:</strong> In Mode A Demo, this action is executed in the isolated sandbox database and logged to the security audit trail. No external credentials or destructive operations occur.
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setPreviewData(null)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleApproveAction(previewData.action_id)}
                disabled={actionInProgress}
                className="px-3.5 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white shadow-sm"
              >
                Confirm Simulated Execution
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
