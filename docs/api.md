# REST API Reference
**Base URL:** `http://127.0.0.1:8000/api`

---

## 1. System & Health Endpoints
- `GET /health`: Returns service health status, project ID, and active mode.
- `GET /settings`: Fetches current system configuration, weights, and integration states.
- `PATCH /settings`: Updates risk weights, correlation time windows, or demo mode.
- `GET /audit-logs`: Lists immutable security audit log entries.

## 2. Dashboard Endpoints
- `GET /dashboard/summary`: Live database-backed metrics (total emails, phishing detected, logins monitored, open incidents).
- `GET /dashboard/charts`: Distribution data for Recharts (classification, login severity, incident status).
- `GET /dashboard/activity`: Recent threat alert feed combining emails, logins, and incidents.

## 3. Email Telemetry Endpoints
- `GET /emails`: List emails with search, filters (class, severity, user), sorting, and pagination.
- `GET /emails/{email_id}`: Full email details, authentication results (SPF/DKIM/DMARC), defanged URLs, ML reasons, and related logins.
- `POST /emails/analyze`: Real-time ad-hoc email classification using the trained TF-IDF model.
- `POST /emails/{email_id}/reanalyze`: Re-runs ML inference and updates the database record.

## 4. Login Telemetry Endpoints
- `GET /logins`: List login events with filters (country, severity, impossible travel, suspicious flag), sorting, and pagination.
- `GET /logins/{event_id}`: Detailed login telemetry, isolation forest score, baseline comparison, and triggered rules.
- `POST /logins/analyze`: Real-time login anomaly scoring and velocity evaluation.

## 5. Correlated Incidents Endpoints
- `GET /incidents`: List multi-source security incidents.
- `GET /incidents/{incident_id}`: Full incident record with linked evidence items, recommended actions, and notes.
- `PATCH /incidents/{incident_id}`: Update incident status (`New`, `Investigating`, `Contained`, `Resolved`, `False Positive`) or assign analyst.
- `POST /incidents/{incident_id}/notes`: Add investigation notes.
- `GET /incidents/{incident_id}/timeline`: Chronological progression of linked email, login, and response events.

## 6. Response Actions Endpoints
- `GET /actions`: List proposed and executed containment actions.
- `POST /actions/preview`: Preview scope and impact assessment of containment action.
- `POST /actions/{action_id}/approve`: Execute simulated action and log to audit trail.
- `POST /actions/{action_id}/reject`: Reject proposed action with analyst reasoning.

## 7. Machine Learning Endpoints
- `GET /models`: Lists loaded ML models and metadata.
- `GET /models/metrics`: Returns empirical evaluation metrics computed on held-out test splits.
