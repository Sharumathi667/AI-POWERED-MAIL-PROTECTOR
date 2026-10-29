import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="analyst") # admin, analyst, demo
    is_active = Column(Boolean, default=True)
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    picture_url = Column(String(500), nullable=True)
    gmail_connected = Column(Boolean, default=False)
    gmail_access_token = Column(Text, nullable=True)
    gmail_refresh_token = Column(Text, nullable=True)
    gmail_token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EmailEvent(Base):
    __tablename__ = "email_events"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    sender_name = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=False)
    sender_domain = Column(String(255), index=True, nullable=False)
    reply_to = Column(String(255), nullable=True)
    email_subject = Column(String(500), nullable=False)
    email_body = Column(Text, nullable=False)
    urls = Column(Text, nullable=True)
    link_count = Column(Integer, default=0)
    has_attachment = Column(Integer, default=0)
    attachment_type = Column(String(50), default="none")
    spf_result = Column(String(50), default="none")
    dkim_result = Column(String(50), default="none")
    dmarc_result = Column(String(50), default="none")
    display_name_mismatch = Column(Integer, default=0)
    domain_age_category = Column(String(50), default="established_>1y")
    label = Column(String(50), default="safe")
    data_source = Column(String(50), default="synthetic") # synthetic, imported_dataset, gmail
    
    analysis = relationship("EmailAnalysis", back_populates="email_event", uselist=False, cascade="all, delete-orphan")

class EmailAnalysis(Base):
    __tablename__ = "email_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String(64), ForeignKey("email_events.email_id"), unique=True, nullable=False)
    predicted_class = Column(String(50), nullable=False) # phishing, safe
    phishing_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False) # 0 - 100
    severity = Column(String(20), nullable=False) # low, medium, high, critical
    reasons = Column(Text, nullable=True) # JSON list of explainable triggers
    recommended_actions = Column(Text, nullable=True) # JSON list
    content_risk = Column(Float, default=0.0)
    url_risk = Column(Float, default=0.0)
    sender_risk = Column(Float, default=0.0)
    model_version = Column(String(50), default="email-v1.0")
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    email_event = relationship("EmailEvent", back_populates="analysis")

class LoginEvent(Base):
    __tablename__ = "login_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    ip_address = Column(String(64), index=True, nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    device_id = Column(String(64), index=True, nullable=False)
    device_type = Column(String(50), nullable=False)
    browser = Column(String(100), nullable=False)
    operating_system = Column(String(100), nullable=False)
    login_success = Column(Integer, default=1)
    failed_attempts = Column(Integer, default=0)
    is_new_device = Column(Integer, default=0)
    is_new_location = Column(Integer, default=0)
    distance_from_usual_location_km = Column(Float, default=0.0)
    minutes_since_previous_login = Column(Float, default=0.0)
    impossible_travel = Column(Integer, default=0)
    label = Column(String(50), default="normal")
    data_source = Column(String(50), default="synthetic") # synthetic, live
    
    analysis = relationship("LoginAnalysis", back_populates="login_event", uselist=False, cascade="all, delete-orphan")

class LoginAnalysis(Base):
    __tablename__ = "login_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("login_events.event_id"), unique=True, nullable=False)
    anomaly_score = Column(Float, nullable=False) # 0 - 100
    risk_score = Column(Float, nullable=False) # 0 - 100
    severity = Column(String(20), nullable=False) # low, medium, high, critical
    is_suspicious = Column(Boolean, default=False)
    reasons = Column(Text, nullable=True) # JSON list
    recommended_actions = Column(Text, nullable=True) # JSON list
    location_risk = Column(Float, default=0.0)
    device_risk = Column(Float, default=0.0)
    auth_risk = Column(Float, default=0.0)
    behavior_risk = Column(Float, default=0.0)
    model_version = Column(String(50), default="login-v1.0")
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    login_event = relationship("LoginEvent", back_populates="analysis")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    affected_user = Column(String(64), index=True, nullable=False)
    risk_score = Column(Float, nullable=False) # 0 - 100
    severity = Column(String(20), index=True, nullable=False) # low, medium, high, critical
    status = Column(String(50), default="New", index=True) # New, Investigating, Contained, Resolved, False Positive
    assigned_analyst = Column(String(100), default="Unassigned")
    evidence_summary = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True) # JSON structure
    recommended_actions = Column(Text, nullable=True) # JSON list
    confidence = Column(String(50), default="High")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    evidence_items = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("ResponseAction", back_populates="incident", cascade="all, delete-orphan")
    notes = relationship("InvestigationNote", back_populates="incident", cascade="all, delete-orphan")

class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), nullable=False)
    event_type = Column(String(50), nullable=False) # email, login
    event_id = Column(String(64), nullable=False)
    evidence_desc = Column(String(500), nullable=False)
    score_contribution = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=True)
    
    incident = relationship("Incident", back_populates="evidence_items")

class ResponseAction(Base):
    __tablename__ = "response_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String(64), unique=True, index=True, nullable=False)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), nullable=True)
    action_type = Column(String(100), nullable=False) # quarantine_email, block_sender, alert_user, reset_password, revoke_session, require_mfa
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target = Column(String(255), nullable=False) # e.g. email address, user ID, IP address
    status = Column(String(50), default="pending") # pending, approved, rejected, executed
    is_simulated = Column(Boolean, default=True) # Clearly distinguished simulation!
    initiated_by = Column(String(100), default="Security System")
    approved_by = Column(String(100), nullable=True)
    execution_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    incident = relationship("Incident", back_populates="actions")

class InvestigationNote(Base):
    __tablename__ = "investigation_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), nullable=False)
    author = Column(String(100), default="Security Analyst")
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    incident = relationship("Incident", back_populates="notes")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False) # e.g. ACTION_APPROVED, INCIDENT_UPDATED, NOTE_ADDED, MODEL_REANALYSIS
    target_type = Column(String(50), nullable=False) # incident, action, email, login, user
    target_id = Column(String(64), nullable=False)
    actor = Column(String(100), nullable=False)
    details = Column(Text, nullable=True) # JSON
    is_simulated = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, index=True, nullable=False)
    setting_value = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
