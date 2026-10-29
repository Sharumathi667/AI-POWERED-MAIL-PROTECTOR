# Machine Learning Pipeline & Evaluation
**Project ID:** PS 1.3  
**Project Title:** AI-Powered Phishing Email and Suspicious Login Investigation System

---

## 1. Datasets & Synthetic Generation

### 1.1 Synthetic Emails Dataset
- **Total Records:** 5,200 emails
- **Class Distribution:** 2,496 Phishing (48.0%) vs 2,704 Legitimate (52.0%)
- **Target User Pool:** 150 simulated campus students and faculty
- **Categories Generated:**
  - Password resets with simulated credential harvesters
  - Academic mailbox suspensions and quota warnings
  - Fake scholarship and financial aid disbursement grants
  - Midterm examination grade sheets with malicious attachments (.zip, .html)
  - Harder borderline cases (polite legitimate emails with urgent deadlines; legitimate emails mentioning passwords)
- **Features Extracted:** `email_subject`, `email_body`, `sender_name`, `sender_domain`, `urls`, `link_count`, `has_attachment`, `spf_result`, `dkim_result`, `dmarc_result`, `display_name_mismatch`, `domain_age_category`.

### 1.2 Synthetic Login Events Dataset
- **Total Records:** 10,526 login events
- **Class Distribution:** 1,514 Suspicious (14.4%) vs 9,012 Normal (85.6%)
- **Target User Pool:** 150 unique campus users with established baseline locations and primary devices
- **Behavioral Scenarios:**
  - Routine daytime logins from recognized laptops/mobiles in campus cities
  - Impossible travel violations (e.g., Boston to Moscow within 30 minutes, speed > 1,000 km/h)
  - Credential stuffing patterns (multiple failed sign-ins followed by successful authentication)
  - Tor browser and script-based anomalies during late night hours (01:00 - 04:00)

---

## 2. Models & Evaluation Results

Evaluated on 20% held-out test splits with zero data leakage:

| Metric | Phishing Email Model (TF-IDF + Calibrated Classifier) | Login Anomaly Model (Isolation Forest + Guardrails) |
| :--- | :---: | :---: |
| **Model Type** | Supervised NLP Classification | Unsupervised / Semi-Supervised Anomaly Detection |
| **Test Set Size** | 1,040 emails | 2,106 login events |
| **Accuracy** | **100.00%** | **96.91%** |
| **Precision** | **100.00%** | **82.34%** |
| **Recall** | **100.00%** | **100.00%** |
| **F1-Score** | **100.00%** | **90.31%** |
| **ROC-AUC** | **1.0000** | **0.9962** |
| **False Positive Rate** | **0.00%** | **3.61%** |
| **False Negative Rate** | **0.00%** | **0.00%** |

### Confusion Matrices
- **Email Classifier:**
  - True Negative (TN): 541
  - False Positive (FP): 0
  - False Negative (FN): 0
  - True Positive (TP): 499
- **Login Anomaly Detector:**
  - True Negative (TN): 1,738
  - False Positive (FP): 65
  - False Negative (FN): 0
  - True Positive (TP): 303
