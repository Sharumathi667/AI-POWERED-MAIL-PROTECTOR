"""
Dataset Validation Module
Validates schema, data types, timestamp formats, ranges, missing values, duplicates,
and train/test leakage.
"""

import os
import sys
import pandas as pd
import numpy as np

REQUIRED_EMAIL_COLUMNS = [
    "email_id", "user_id", "timestamp", "sender_name", "sender_email",
    "sender_domain", "reply_to", "email_subject", "email_body", "urls",
    "link_count", "has_attachment", "attachment_type", "spf_result",
    "dkim_result", "dmarc_result", "display_name_mismatch",
    "domain_age_category", "label"
]

REQUIRED_LOGIN_COLUMNS = [
    "event_id", "user_id", "timestamp", "ip_address", "country", "city",
    "device_id", "device_type", "browser", "operating_system",
    "login_success", "failed_attempts", "is_new_device", "is_new_location",
    "distance_from_usual_location_km", "minutes_since_previous_login",
    "impossible_travel", "label"
]

def validate_emails(filepath="backend/data/raw/synthetic_emails.csv"):
    print(f"\n[VALIDATING EMAILS] Checking: {filepath}")
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return False
        
    df = pd.read_csv(filepath)
    errors = []
    
    # 1. Row count >= 5,000
    if len(df) < 5000:
        errors.append(f"Row count {len(df)} is less than required 5,000")
        
    # 2. Required columns
    missing_cols = [c for c in REQUIRED_EMAIL_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        
    # 3. Duplicate IDs
    if df["email_id"].duplicated().any():
        dup_count = df["email_id"].duplicated().sum()
        errors.append(f"Found {dup_count} duplicate email_id values")
        
    # 4. Valid labels
    valid_labels = {"phishing", "safe"}
    invalid_labels = set(df["label"].unique()) - valid_labels
    if invalid_labels:
        errors.append(f"Invalid email labels found: {invalid_labels}")
        
    # 5. Timestamp format
    try:
        pd.to_datetime(df["timestamp"])
    except Exception as e:
        errors.append(f"Invalid timestamp values: {e}")
        
    # 6. Null checks on critical fields
    for col in ["email_id", "user_id", "sender_email", "email_subject", "label"]:
        if df[col].isnull().any():
            errors.append(f"Column '{col}' contains {df[col].isnull().sum()} null values")
            
    # 7. Numerical ranges
    if (df["link_count"] < 0).any():
        errors.append("Negative link_count detected")
        
    print(f"Total email records: {len(df):,}")
    print(f"Class distribution:\n{df['label'].value_counts(normalize=True).round(4) * 100}%")
    print(f"Unique users targeted: {df['user_id'].nunique()}")
    
    if errors:
        print("[FAIL] Email dataset validation failed:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("[PASS] Email dataset passed all validation checks!")
        return True


def validate_logins(filepath="backend/data/raw/synthetic_login_events.csv"):
    print(f"\n[VALIDATING LOGINS] Checking: {filepath}")
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return False
        
    df = pd.read_csv(filepath)
    errors = []
    
    # 1. Row count >= 10,000
    if len(df) < 10000:
        errors.append(f"Row count {len(df)} is less than required 10,000")
        
    # 2. Required columns
    missing_cols = [c for c in REQUIRED_LOGIN_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        
    # 3. Duplicate IDs
    if df["event_id"].duplicated().any():
        dup_count = df["event_id"].duplicated().sum()
        errors.append(f"Found {dup_count} duplicate event_id values")
        
    # 4. Valid labels
    valid_labels = {"normal", "suspicious"}
    invalid_labels = set(df["label"].unique()) - valid_labels
    if invalid_labels:
        errors.append(f"Invalid login labels found: {invalid_labels}")
        
    # 5. Timestamp format
    try:
        pd.to_datetime(df["timestamp"])
    except Exception as e:
        errors.append(f"Invalid timestamp values: {e}")
        
    # 6. Null checks
    for col in ["event_id", "user_id", "ip_address", "country", "label"]:
        if df[col].isnull().any():
            errors.append(f"Column '{col}' contains {df[col].isnull().sum()} null values")
            
    # 7. Numerical sanity
    if (df["distance_from_usual_location_km"] < 0).any():
        errors.append("Negative distance detected")
    if (df["failed_attempts"] < 0).any():
        errors.append("Negative failed_attempts detected")
        
    print(f"Total login events: {len(df):,}")
    print(f"Class distribution:\n{df['label'].value_counts(normalize=True).round(4) * 100}%")
    print(f"Unique users monitored: {df['user_id'].nunique()}")
    print(f"Impossible travel events: {df['impossible_travel'].sum()}")
    
    if errors:
        print("[FAIL] Login dataset validation failed:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("[PASS] Login dataset passed all validation checks!")
        return True


def check_splits_leakage(train_path, test_path, id_col):
    print(f"\n[CHECKING SPLIT LEAKAGE] {train_path} vs {test_path}")
    if not (os.path.exists(train_path) and os.path.exists(test_path)):
        print("Skipping split leakage check: Split files not generated yet.")
        return True
        
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    train_ids = set(train_df[id_col])
    test_ids = set(test_df[id_col])
    overlap = train_ids.intersection(test_ids)
    
    if overlap:
        print(f"[FAIL] Data leakage! {len(overlap)} IDs exist in both train and test splits!")
        return False
    else:
        print(f"[PASS] Zero ID leakage between train ({len(train_df)}) and test ({len(test_df)}) splits.")
        return True


if __name__ == "__main__":
    email_ok = validate_emails()
    login_ok = validate_logins()
    
    if not (email_ok and login_ok):
        sys.exit(1)
    print("\nAll dataset validations completed successfully!")
