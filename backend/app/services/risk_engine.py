from typing import Dict, Any, List
from backend.app.core.config import settings

class RiskEngine:
    @staticmethod
    def calculate_incident_risk(
        email_risk: float,
        login_risk: float,
        time_delta_hours: float = 0.0,
        has_credential_phish: bool = False,
        is_compromised_login: bool = False
    ) -> Dict[str, Any]:
        """
        Combines email and login risk scores using bounded correlation adjustments.
        Incident Risk = min(100, 0.5 * Email Risk + 0.5 * Login Risk + Correlation Bonus)
        """
        base_combined = 0.5 * email_risk + 0.5 * login_risk
        
        # Calculate correlation bonus based on real evidence
        bonus = 0.0
        bonus_factors = []
        
        if time_delta_hours <= 2.0:
            bonus += 10.0
            bonus_factors.append(f"Temporal proximity: login occurred within {time_delta_hours:.1f} hours of phishing email arrival (+10 pts)")
        elif time_delta_hours <= 12.0:
            bonus += 6.0
            bonus_factors.append(f"Temporal proximity: login occurred within {time_delta_hours:.1f} hours of phishing email arrival (+6 pts)")
            
        if has_credential_phish and is_compromised_login:
            bonus += 10.0
            bonus_factors.append("Behavioral causality: phishing email requested credential reset followed by successful foreign login (+10 pts)")
            
        # Cap bonus
        capped_bonus = min(settings.MAX_CORRELATION_BONUS, bonus)
        
        final_risk = min(100.0, base_combined + capped_bonus)
        final_risk = round(max(0.0, final_risk), 1)
        
        if final_risk <= settings.SEVERITY_LOW_MAX:
            severity = "low"
        elif final_risk <= settings.SEVERITY_MED_MAX:
            severity = "medium"
        elif final_risk <= settings.SEVERITY_HIGH_MAX:
            severity = "high"
        else:
            severity = "critical"
            
        confidence = "High" if (email_risk >= 60 and login_risk >= 60) else "Medium"
        if email_risk < 40 and login_risk < 40:
            confidence = "Low"
            
        return {
            "risk_score": final_risk,
            "severity": severity,
            "confidence": confidence,
            "base_email_risk": email_risk,
            "base_login_risk": login_risk,
            "correlation_bonus": capped_bonus,
            "bonus_factors": bonus_factors
        }

risk_engine = RiskEngine()
