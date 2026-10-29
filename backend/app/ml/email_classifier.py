import os
import joblib
import re
from typing import Dict, Any, List
from backend.app.core.config import settings

class EmailClassifierService:
    def __init__(self):
        self.model = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(settings.EMAIL_MODEL_PATH):
            try:
                self.model = joblib.load(settings.EMAIL_MODEL_PATH)
                print(f"[EmailClassifierService] Successfully loaded model from {settings.EMAIL_MODEL_PATH}")
            except Exception as e:
                print(f"[EmailClassifierService] Error loading model: {e}")
                self.model = None
        else:
            print(f"[EmailClassifierService] Model artifact not found at {settings.EMAIL_MODEL_PATH}")
            
    def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs text classification and multi-factor rule analysis.
        Returns:
            predicted_class, phishing_probability, risk_score, severity,
            reasons, recommended_actions, component breakdown
        """
        subject = str(email_data.get("email_subject") or "")
        body = str(email_data.get("email_body") or "")
        sender_name = str(email_data.get("sender_name") or "")
        sender_domain = str(email_data.get("sender_domain") or "")
        sender_email = str(email_data.get("sender_email") or "")
        urls = str(email_data.get("urls") or "")
        link_count = int(email_data.get("link_count") or 0)
        has_attachment = int(email_data.get("has_attachment") or 0)
        attachment_type = str(email_data.get("attachment_type") or "none").lower()
        spf = str(email_data.get("spf_result") or "pass").lower()
        dkim = str(email_data.get("dkim_result") or "pass").lower()
        dmarc = str(email_data.get("dmarc_result") or "pass").lower()
        display_mismatch = int(email_data.get("display_name_mismatch") or 0)
        domain_age = str(email_data.get("domain_age_category") or "established_>1y").lower()
        reply_to = str(email_data.get("reply_to") or sender_email)
        
        # 1. ML Text Prediction
        text_repr = f"Subject: {subject} | Sender: {sender_name} <{sender_domain}> | Body: {body}"
        phishing_prob = 0.5
        predicted_class = "safe"
        
        if self.model is not None:
            try:
                preds = self.model.predict([text_repr])
                predicted_class = "phishing" if preds[0] == 1 else "safe"
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba([text_repr])
                    phishing_prob = float(probs[0][1])
                else:
                    phishing_prob = 0.95 if predicted_class == "phishing" else 0.05
            except Exception as e:
                print(f"[EmailClassifierService] Inference error: {e}")
                
        # 2. Explainable Rule & Feature-Based Risk Signals
        reasons: List[str] = []
        recommended_actions: List[str] = []
        
        # --- Content Risk (0 - 100) ---
        content_risk = round(phishing_prob * 100, 1)
        if phishing_prob >= 0.70:
            reasons.append(f"ML text classifier detected high-confidence phishing indicators (confidence: {phishing_prob * 100:.1f}%)")
        elif phishing_prob >= 0.45:
            reasons.append("ML text classifier identified borderline suspicious phrasing or account urgency cues")
            
        # --- URL Risk (0 - 100) ---
        url_risk = 0.0
        if urls:
            url_lower = urls.lower()
            suspicious_tlds = [".xyz", ".tk", ".top", ".info", ".online", ".club"]
            shorteners = ["bit.ly", "tinyurl", "t.co", "is.gd", "rb.gy"]
            
            has_suspicious_tld = any(tld in url_lower for tld in suspicious_tlds)
            has_shortener = any(short in url_lower for short in shorteners)
            has_credential_keywords = any(kw in url_lower for kw in ["login", "sso", "auth", "verify", "secure", "update", "token", "password"])
            
            if has_suspicious_tld:
                url_risk += 45
                reasons.append(f"Contains link pointing to an untrusted/suspicious TLD ({urls.split('/')[2] if '/' in urls else urls})")
            if has_shortener:
                url_risk += 35
                reasons.append("Contains shortened URL obscuring final destination")
            if has_credential_keywords and (has_suspicious_tld or has_shortener or "campus.edu" not in url_lower):
                url_risk += 30
                reasons.append("Contains external link requesting credential verification/authentication")
            if link_count >= 3:
                url_risk += 15
                
            url_risk = min(100.0, url_risk)
        elif link_count > 0:
            url_risk = 20.0
            
        # --- Sender & Header Risk (0 - 100) ---
        sender_risk = 0.0
        if spf in ("fail", "softfail"):
            sender_risk += 35 if spf == "fail" else 20
            reasons.append(f"Sender Policy Framework (SPF) validation check returned '{spf}'")
        if dkim in ("fail", "none") and "campus.edu" not in sender_domain:
            sender_risk += 25 if dkim == "fail" else 15
            reasons.append(f"DKIM cryptographic signature verification status is '{dkim}'")
        if dmarc == "fail":
            sender_risk += 30
            reasons.append("DMARC alignment check failed for sender domain")
            
        if display_mismatch == 1:
            sender_risk += 30
            reasons.append(f"Display name '{sender_name}' impersonates official authority but does not match domain '{sender_domain}'")
            
        if reply_to and sender_email and reply_to != sender_email and "campus.edu" not in reply_to:
            sender_risk += 25
            reasons.append(f"Reply-to header '{reply_to}' diverges from originating sender '{sender_email}'")
            
        if "new_<30d" in domain_age:
            sender_risk += 25
            reasons.append("Sender domain was registered less than 30 days ago")
            
        if has_attachment:
            if attachment_type in ("exe", "zip", "html"):
                sender_risk += 35
                reasons.append(f"Email contains high-risk executable or script attachment type (.{attachment_type})")
            else:
                sender_risk += 10
                
        sender_risk = min(100.0, sender_risk)
        
        # --- Overall Weighted Email Risk Score ---
        # Formula: 0.40 * Content + 0.35 * URL + 0.25 * Sender
        final_risk = (
            settings.EMAIL_WEIGHT_CONTENT * content_risk +
            settings.EMAIL_WEIGHT_URL * url_risk +
            settings.EMAIL_WEIGHT_SENDER_HEADER * sender_risk
        )
        final_risk = round(min(100.0, max(0.0, final_risk)), 1)
        
        # Severity calculation
        if final_risk <= settings.SEVERITY_LOW_MAX:
            severity = "low"
        elif final_risk <= settings.SEVERITY_MED_MAX:
            severity = "medium"
        elif final_risk <= settings.SEVERITY_HIGH_MAX:
            severity = "high"
        else:
            severity = "critical"
            
        # Tailored Recommended Actions
        if severity in ("high", "critical") or predicted_class == "phishing":
            recommended_actions.append("Quarantine email to prevent campus user interaction")
            recommended_actions.append("Notify affected user and caution against entering credentials")
            if sender_domain and "campus.edu" not in sender_domain:
                recommended_actions.append(f"Add sender domain '{sender_domain}' to perimeter firewall blocklist")
            recommended_actions.append("Search for correlated login anomalies involving this recipient")
        elif severity == "medium":
            recommended_actions.append("Deliver with external security caution banner added")
            recommended_actions.append("Log URL telemetry for automated perimeter inspection")
        else:
            recommended_actions.append("Deliver to user inbox normally; no containment required")
            
        if not reasons:
            reasons.append("Authentication checks passed (SPF/DKIM/DMARC) and no suspicious language or URLs detected")
            
        return {
            "predicted_class": predicted_class,
            "phishing_probability": round(phishing_prob, 4),
            "risk_score": final_risk,
            "severity": severity,
            "reasons": reasons,
            "recommended_actions": recommended_actions,
            "content_risk": content_risk,
            "url_risk": round(url_risk, 1),
            "sender_risk": round(sender_risk, 1),
            "model_version": "email-v1.0"
        }

email_classifier = EmailClassifierService()
