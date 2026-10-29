import os
import pandas as pd
import pytest

from backend.scripts.validate_datasets import validate_emails, validate_logins, REQUIRED_EMAIL_COLUMNS, REQUIRED_LOGIN_COLUMNS

def test_synthetic_email_dataset_exists_and_valid():
    email_path = "backend/data/raw/synthetic_emails.csv"
    assert os.path.exists(email_path), "synthetic_emails.csv must exist"
    
    df = pd.read_csv(email_path)
    assert len(df) >= 5000, f"Expected at least 5000 emails, got {len(df)}"
    
    for col in REQUIRED_EMAIL_COLUMNS:
        assert col in df.columns, f"Missing required email column: {col}"
        
    assert set(df["label"].unique()).issubset({"phishing", "safe"})
    assert not df["email_id"].duplicated().any(), "Duplicate email_id found"
    assert validate_emails(email_path) is True

def test_synthetic_login_dataset_exists_and_valid():
    login_path = "backend/data/raw/synthetic_login_events.csv"
    assert os.path.exists(login_path), "synthetic_login_events.csv must exist"
    
    df = pd.read_csv(login_path)
    assert len(df) >= 10000, f"Expected at least 10000 logins, got {len(df)}"
    
    for col in REQUIRED_LOGIN_COLUMNS:
        assert col in df.columns, f"Missing required login column: {col}"
        
    assert set(df["label"].unique()).issubset({"normal", "suspicious"})
    assert not df["event_id"].duplicated().any(), "Duplicate event_id found"
    assert validate_logins(login_path) is True
