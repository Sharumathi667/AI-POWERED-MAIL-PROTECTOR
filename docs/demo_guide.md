# End-to-End Investigation Demo Guide
**Project ID:** PS 1.3  
**Scenario:** Phishing Email Arrival to Suspicious Foreign Sign-In & Automated Containment

---

## Demonstration Workflow Steps

### Step 1: Open the SOC Overview Dashboard
1. Navigate to `http://localhost:5173/`.
2. Inspect the live database counts: Total Emails Analyzed, Phishing Detections, Logins Monitored, and Active Correlated Incidents.
3. Review the interactive Recharts distribution charts and the Live Threat Telemetry feed.

### Step 2: Investigate an Incoming Phishing Alert
1. Click **Email Investigation** in the top navigation bar.
2. Filter by `Phishing` classification or search for a user like `USER-1002`.
3. Click **Inspect** on any flagged email:
   - Notice the **SPF/DKIM/DMARC** authentication validation badges.
   - Review the **defanged, non-clickable URLs** ensuring analyst safety.
   - Read the **explainable factors** indicating why the TF-IDF model and header rules flagged the alert.
   - Observe the **correlated logins** for that specific recipient listed directly inside the inspection drawer.

### Step 3: Inspect Suspicious Login Telemetry
1. Click **Login Monitoring** in the top navigation bar.
2. Filter by **Impossible Travel Only ⚡** to see high-velocity anomalies.
3. Click **Inspect** on an event (e.g., login from Bucharest, Romania or Moscow, Russia):
   - Notice the physical distance calculation (e.g. 7,400 km in 20 minutes).
   - Review the **Isolation Forest Anomaly Score** vs the **Heuristic Risk Score**.
   - Read the rule triggers (unrecognized device, foreign network range, failed attempts preceding success).

### Step 4: Triage a Correlated Attack Incident
1. Click **Incidents** in the top navigation bar.
2. Select an incident from the left queue (e.g., `INC-1002-...`):
   - Review the **Correlation Story & Causality Analysis**: notice the calculated time delta between phishing arrival and foreign sign-in, along with the **+10 to +20 correlation bonus points** applied to the incident risk score.
   - Inspect the **Chronological Event Timeline** showing the exact progression from email receipt to login anomaly.
3. In the **Proposed Containment Actions** section:
   - Click **Preview Scope** on an action (e.g., "Quarantine Malicious Email" or "Revoke Active Sessions").
   - Click **Approve**: observe the simulated execution response with a clear `[SIMULATED ACTION EXECUTED]` label and provider mock confirmation.
4. Add an analyst note in the **Investigation Notes** box (e.g., "Account owner notified via telephone; user confirmed they did not initiate sign-in from Bucharest").
5. Update the Incident status to **Contained** or **Resolved**.

### Step 5: Verify Audit Trail & Model Transparency
1. Click **Settings & Audit** to observe that your approved containment action and note were permanently recorded in the immutable audit log.
2. Click **ML Performance** to examine the real evaluation metrics (100% email F1, 90.3% login anomaly F1, and holdout confusion matrices) with full transparency.
