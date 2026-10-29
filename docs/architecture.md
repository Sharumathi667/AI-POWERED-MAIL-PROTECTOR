# System Architecture & Technical Design
**Project ID:** PS 1.3  
**Project Title:** AI-Powered Phishing Email and Suspicious Login Investigation System

---

## 1. High-Level Architecture

The platform provides an end-to-end investigation pipeline linking email telemetry and user login activity into correlated security incident records:

```text
                 Security Analyst / SOC Admin
                           │
                           ▼
                  React 19 + Vite Dashboard
             (Tailwind CSS + Lucide + Recharts)
                           │  HTTP / REST
                           ▼
                 FastAPI Backend Server
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Email Analysis    Login Analysis   Incident Engine
          │                │                │
          ▼                ▼                ▼
    Trained Text     Anomaly Model     Risk Correlation
    Classification   + Security Rules  + Explanations
     (TF-IDF+SVM)    (Isolation Forest) (Time-Window)
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                     SQL Database (SQLite / SQLAlchemy)
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Email Events   Login Events  Audit Trail & Notes
             │             │
             └──────┬──────┘
                    │
                    ▼
             Incident Response
         Simulated Containment Actions
```

---

## 2. Core Subsystems

### 2.1 Machine Learning Pipelines
- **Email Classifier**: Combines Subject, Sender Name, Domain, and Body into an n-gram TF-IDF matrix (10,000 features, sublinear TF scaling). Trained on 5,200 synthetic emails with Logistic Regression and Calibrated Linear SVM. Computes calibrated probability and explainable feature attributions.
- **Login Anomaly Detector**: Evaluates 9 behavioral and geographical features (`login_hour`, `day_of_week`, `failed_attempts`, `is_new_device`, `is_new_location`, `distance_from_usual_location_km`, `minutes_since_previous_login`, `login_success`, `impossible_travel`). Uses an Isolation Forest with 150 estimators, standard scaling, and calibrated decision score normalization (0–100 scale).

### 2.2 Explainable Multi-Factor Risk Engine
Normalizes each factor to a 0–100 scale before applying configurable weights:
- **Email Risk Formula**:  
  `Email Risk = 0.40 × Content Risk + 0.35 × URL Risk + 0.25 × Sender/Header Risk`
- **Login Risk Formula**:  
  `Login Risk = 0.35 × Location Risk + 0.30 × Device Risk + 0.20 × Auth Risk + 0.15 × Behavior Risk`
- **Correlated Incident Risk Formula**:  
  `Incident Risk = min(100, 0.5 × Email Risk + 0.5 × Login Risk + Correlation Bonus)`  
  *Where correlation bonus is capped at 20.0 points based on temporal proximity and behavioral causality.*

### 2.3 Dual Integration Modes
- **Mode A: Synthetic Demonstration Mode (Default)**: Fully functional offline. Uses synthetic campus data, isolated simulated action executions, and full audit trail without external API keys.
- **Mode B: Authorized Gmail Integration (Production-Ready)**: Uses official Google Workspace OAuth 2.0 with minimal read-only scopes (`https://www.googleapis.com/auth/gmail.readonly`) and admin domain-wide delegation for multi-mailbox enterprise scanning.
