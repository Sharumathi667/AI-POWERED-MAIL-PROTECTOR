import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const fetchDashboardSummary = () => api.get('/dashboard/summary').then(res => res.data);
export const fetchDashboardCharts = () => api.get('/dashboard/charts').then(res => res.data);
export const fetchDashboardActivity = () => api.get('/dashboard/activity').then(res => res.data);

// Emails
export const fetchEmails = (params) => api.get('/emails', { params }).then(res => res.data);
export const fetchEmailDetails = (id) => api.get(`/emails/${id}`).then(res => res.data);
export const analyzeCustomEmail = (data) => api.post('/emails/analyze', data).then(res => res.data);
export const reanalyzeEmail = (id) => api.post(`/emails/${id}/reanalyze`).then(res => res.data);
export const syncGmailInbox = () => api.post('/emails/sync-gmail').then(res => res.data);

// Logins
export const fetchLogins = (params) => api.get('/logins', { params }).then(res => res.data);
export const fetchLoginDetails = (id) => api.get(`/logins/${id}`).then(res => res.data);
export const analyzeCustomLogin = (data) => api.post('/logins/analyze', data).then(res => res.data);

// Incidents
export const fetchIncidents = (params) => api.get('/incidents', { params }).then(res => res.data);
export const fetchIncidentDetails = (id) => api.get(`/incidents/${id}`).then(res => res.data);
export const updateIncident = (id, data) => api.patch(`/incidents/${id}`, data).then(res => res.data);
export const addIncidentNote = (id, data) => api.post(`/incidents/${id}/notes`, data).then(res => res.data);
export const fetchIncidentTimeline = (id) => api.get(`/incidents/${id}/timeline`).then(res => res.data);

// Actions
export const fetchActions = (params) => api.get('/actions', { params }).then(res => res.data);
export const previewAction = (data) => api.post('/actions/preview', data).then(res => res.data);
export const approveAction = (id, data) => api.post(`/actions/${id}/approve`, data).then(res => res.data);
export const rejectAction = (id, data) => api.post(`/actions/${id}/reject`, data).then(res => res.data);

// Models
export const fetchModelsOverview = () => api.get('/models').then(res => res.data);
export const fetchModelsMetrics = () => api.get('/models/metrics').then(res => res.data);

// Integrations (Gmail)
export const fetchIntegrationsStatus = () => api.get('/integrations/status').then(res => res.data);
export const connectGmail = () => api.get('/integrations/gmail/connect').then(res => res.data);
export const disconnectGmail = () => api.post('/integrations/gmail/disconnect').then(res => res.data);
export const fetchGmailMessages = () => api.get('/integrations/gmail/messages').then(res => res.data);

// Audit & Settings
export const fetchAuditLogs = (params) => api.get('/audit-logs', { params }).then(res => res.data);
export const fetchSettings = () => api.get('/settings').then(res => res.data);
export const updateSettings = (data) => api.patch('/settings', data).then(res => res.data);

export default api;
