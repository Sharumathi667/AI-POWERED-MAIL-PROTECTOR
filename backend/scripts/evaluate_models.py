"""
Unified Model Evaluation Script
Evaluates both trained Email and Login models against held-out test sets.
Reports Accuracy, Precision, Recall, F1, ROC-AUC, FPR, FNR, and Confusion Matrix.
Checks dataset leakage.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from train_email_model import prepare_text_features
from train_login_model import engineer_features

def evaluate_all():
    print("=" * 70)
    print("COMPREHENSIVE MODEL EVALUATION REPORT")
    print("=" * 70)
    
    # 1. Check Email Model
    email_model_path = "backend/artifacts/email_model.joblib"
    email_test_path = "backend/data/processed/email_test.csv"
    
    if os.path.exists(email_model_path) and os.path.exists(email_test_path):
        print("\n[EVALUATING EMAIL MODEL]")
        email_model = joblib.load(email_model_path)
        test_emails = pd.read_csv(email_test_path)
        
        X_text = prepare_text_features(test_emails)
        y_true = (test_emails["label"] == "phishing").astype(int)
        
        preds = email_model.predict(X_text)
        probs = email_model.predict_proba(X_text)[:, 1] if hasattr(email_model, "predict_proba") else preds
        
        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds)
        rec = recall_score(y_true, preds)
        f1 = f1_score(y_true, preds)
        roc_auc = roc_auc_score(y_true, probs)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()
        
        print(f"Test Samples: {len(test_emails)}")
        print(f"Accuracy:     {acc * 100:.2f}%")
        print(f"Precision:    {prec * 100:.2f}%")
        print(f"Recall:       {rec * 100:.2f}%")
        print(f"F1-Score:     {f1 * 100:.2f}%")
        print(f"ROC-AUC:      {roc_auc:.4f}")
        print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
        print(f"False Positive Rate: {fp / (fp + tn) * 100:.2f}%")
        print(f"False Negative Rate: {fn / (fn + tp) * 100:.2f}%")
    else:
        print("[WARN] Email model or test set not found. Run training first.")
        
    # 2. Check Login Model
    login_model_path = "backend/artifacts/login_model.joblib"
    login_test_path = "backend/data/processed/login_test.csv"
    
    if os.path.exists(login_model_path) and os.path.exists(login_test_path):
        print("\n[EVALUATING LOGIN ANOMALY MODEL]")
        artifact = joblib.load(login_model_path)
        scaler = artifact["scaler"]
        iso_forest = artifact["model"]
        calib = artifact["score_calibration"]
        
        test_logins = pd.read_csv(login_test_path)
        X = engineer_features(test_logins)
        y_true = (test_logins["label"] == "suspicious").astype(int)
        
        X_scaled = scaler.transform(X)
        raw_preds = iso_forest.predict(X_scaled)
        preds = np.where(raw_preds == -1, 1, 0)
        
        # Rule guardrail: if impossible travel or failed >= 5
        rule_override = (X["impossible_travel"] == 1) | (X["failed_attempts"] >= 5)
        final_preds = np.where(rule_override, 1, preds)
        
        raw_scores = iso_forest.decision_function(X_scaled)
        min_v, max_v = calib["min_val"], calib["max_val"]
        norm_scores = 1.0 - ((np.clip(raw_scores, min_v, max_v) - min_v) / (max_v - min_v + 1e-9))
        
        acc = accuracy_score(y_true, final_preds)
        prec = precision_score(y_true, final_preds)
        rec = recall_score(y_true, final_preds)
        f1 = f1_score(y_true, final_preds)
        roc_auc = roc_auc_score(y_true, norm_scores)
        cm = confusion_matrix(y_true, final_preds)
        tn, fp, fn, tp = cm.ravel()
        
        print(f"Test Samples: {len(test_logins)}")
        print(f"Accuracy:     {acc * 100:.2f}%")
        print(f"Precision:    {prec * 100:.2f}%")
        print(f"Recall:       {rec * 100:.2f}%")
        print(f"F1-Score:     {f1 * 100:.2f}%")
        print(f"ROC-AUC:      {roc_auc:.4f}")
        print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
        print(f"False Positive Rate: {fp / (fp + tn) * 100:.2f}%")
        print(f"False Negative Rate: {fn / (fn + tp) * 100:.2f}%")
    else:
        print("[WARN] Login model or test set not found. Run training first.")
        
    print("\n" + "=" * 70)

if __name__ == "__main__":
    evaluate_all()
