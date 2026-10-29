import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

# User
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    picture_url: Optional[str] = None
    gmail_connected: Optional[bool] = False
    created_at: datetime.datetime

# Email
class EmailAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email_id: str
    predicted_class: str
    phishing_probability: float
    risk_score: float
    severity: str
    reasons: List[str]
    recommended_actions: List[str]
    content_risk: float
    url_risk: float
    sender_risk: float
    model_version: str
    analyzed_at: datetime.datetime

class EmailEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email_id: str
    user_id: str
    timestamp: datetime.datetime
    sender_name: Optional[str]
    sender_email: str
    sender_domain: str
    reply_to: Optional[str]
    email_subject: str
    email_body: str
    urls: Optional[str]
    link_count: int
    has_attachment: int
    attachment_type: str
    spf_result: str
    dkim_result: str
    dmarc_result: str
    display_name_mismatch: int
    domain_age_category: str
    label: str
    data_source: str
    analysis: Optional[EmailAnalysisOut] = None

class EmailAnalyzeRequest(BaseModel):
    user_id: str
    sender_name: Optional[str] = ""
    sender_email: str
    email_subject: str
    email_body: str
    urls: Optional[str] = ""
    link_count: Optional[int] = 0
    has_attachment: Optional[int] = 0
    attachment_type: Optional[str] = "none"
    spf_result: Optional[str] = "pass"
    dkim_result: Optional[str] = "pass"
    dmarc_result: Optional[str] = "pass"
    display_name_mismatch: Optional[int] = 0
    reply_to: Optional[str] = None

# Login
class LoginAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    anomaly_score: float
    risk_score: float
    severity: str
    is_suspicious: bool
    reasons: List[str]
    recommended_actions: List[str]
    location_risk: float
    device_risk: float
    auth_risk: float
    behavior_risk: float
    model_version: str
    analyzed_at: datetime.datetime

class LoginEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    user_id: str
    timestamp: datetime.datetime
    ip_address: str
    country: str
    city: str
    device_id: str
    device_type: str
    browser: str
    operating_system: str
    login_success: int
    failed_attempts: int
    is_new_device: int
    is_new_location: int
    distance_from_usual_location_km: float
    minutes_since_previous_login: float
    impossible_travel: int
    label: str
    data_source: str
    analysis: Optional[LoginAnalysisOut] = None

class LoginAnalyzeRequest(BaseModel):
    user_id: str
    ip_address: str
    country: str
    city: str
    device_id: str
    device_type: str
    browser: str
    operating_system: str
    login_success: int
    failed_attempts: int
    is_new_device: int
    is_new_location: int
    distance_from_usual_location_km: float
    minutes_since_previous_login: float
    impossible_travel: int

# Incident
class EvidenceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    event_id: str
    evidence_desc: str
    score_contribution: float
    timestamp: Optional[datetime.datetime]

class ResponseActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: str
    incident_id: Optional[str]
    action_type: str
    title: str
    description: Optional[str]
    target: str
    status: str
    is_simulated: bool
    initiated_by: str
    approved_by: Optional[str]
    execution_result: Optional[str]
    created_at: datetime.datetime
    executed_at: Optional[datetime.datetime]

class InvestigationNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: str
    author: str
    note_text: str
    created_at: datetime.datetime

class InvestigationNoteCreate(BaseModel):
    author: Optional[str] = "Security Analyst"
    note_text: str

class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: str
    title: str
    affected_user: str
    risk_score: float
    severity: str
    status: str
    assigned_analyst: str
    evidence_summary: Optional[str]
    reasoning: Optional[Dict[str, Any]]
    recommended_actions: Optional[List[str]]
    confidence: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    evidence_items: List[EvidenceItemOut] = []
    actions: List[ResponseActionOut] = []
    notes: List[InvestigationNoteOut] = []

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    assigned_analyst: Optional[str] = None
    confidence: Optional[str] = None

class IncidentCreate(BaseModel):
    title: str
    affected_user: str
    risk_score: float
    severity: str
    evidence_summary: str
    recommended_actions: List[str]
    related_email_ids: List[str] = []
    related_login_event_ids: List[str] = []

# Action Approval
class ActionApprovalRequest(BaseModel):
    analyst_name: Optional[str] = "Security Administrator"
    notes: Optional[str] = "Approved after manual evidence review"

# Dashboard Summary & Charts
class DashboardSummaryOut(BaseModel):
    total_emails_analyzed: int
    phishing_emails_detected: int
    phishing_ratio_percent: float
    total_logins_monitored: int
    suspicious_logins_detected: int
    total_incidents: int
    open_incidents: int
    high_risk_incidents: int
    resolved_incidents: int
    demo_mode: bool
    model_statuses: Dict[str, Any]

class ActivityItem(BaseModel):
    id: str
    type: str # email, login, incident, action
    timestamp: datetime.datetime
    title: str
    description: str
    severity: str
    user_id: Optional[str]

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    target_type: str
    target_id: str
    actor: str
    details: Optional[Dict[str, Any]]
    is_simulated: bool
    timestamp: datetime.datetime
