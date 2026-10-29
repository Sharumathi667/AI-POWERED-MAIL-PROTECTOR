"""
Train Email Phishing Detection Model
Pipeline:
- Text normalization (subject + body + sender)
- TF-IDF Vectorization
- Train/test split with stratification
- Comparison between Logistic Regression and Linear SVM (Calibrated)
- Model selection based on validation F1-score
- Complete evaluation metrics computation (Acc, Precision, Recall, F1, ROC-AUC, FPR, FNR, Confusion Matrix)
- Save model pipeline artifact and metrics JSON
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

def prepare_text_features(df):
    """Combine subject, body, sender name, and sender domain into single text feature."""
    subject = df["email_subject"].fillna("")
    body = df["email_body"].fillna("")
    sender_name = df["sender_name"].fillna("")
    sender_domain = df["sender_domain"].fillna("")
    
    text_repr = "Subject: " + subject + " | Sender: " + sender_name + " <" + sender_domain + "> | Body: " + body
    return text_repr

def train_and_evaluate(data_path="backend/data/raw/synthetic_emails.csv"):
    print("=" * 60)
    print("TRAINING EMAIL PHISHING DETECTION MODEL")
    print("=" * 60)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Email dataset not found at {data_path}. Run generate_synthetic_data.py first.")
        
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} emails from {data_path}")
    
    # Target encoding: phishing=1, safe=0
    y = (df["label"] == "phishing").astype(int)
    X_text = prepare_text_features(df)
    
    # Stratified 80/20 train/test split
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X_text, y, df, test_size=0.20, random_state=42, stratify=y
    )
    
    # Save split datasets
    os.makedirs("backend/data/processed", exist_ok=True)
    os.makedirs("backend/artifacts", exist_ok=True)
    df_train.to_csv("backend/data/processed/email_train.csv", index=False)
    df_test.to_csv("backend/data/processed/email_test.csv", index=False)
    print(f"Saved processed splits: Train={len(df_train)}, Test={len(df_test)}")
    
    # Candidate 1: TF-IDF + Logistic Regression
    pipe_lr = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)),
        ("clf", LogisticRegression(C=1.5, max_iter=1000, random_state=42))
    ])
    
    # Candidate 2: TF-IDF + Linear SVM (calibrated with Sigmoid for valid probabilities)
    pipe_svm = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42), method="sigmoid", cv=3))
    ])
    
    print("\nFitting Logistic Regression pipeline...")
    pipe_lr.fit(X_train, y_train)
    preds_lr = pipe_lr.predict(X_test)
    f1_lr = f1_score(y_test, preds_lr)
    print(f"Logistic Regression Validation F1: {f1_lr:.4f}")
    
    print("\nFitting Calibrated Linear SVM pipeline...")
    pipe_svm.fit(X_train, y_train)
    preds_svm = pipe_svm.predict(X_test)
    f1_svm = f1_score(y_test, preds_svm)
    print(f"Calibrated Linear SVM Validation F1: {f1_svm:.4f}")
    
    # Select best model based on validation F1
    if f1_svm > f1_lr:
        selected_model = pipe_svm
        selected_name = "Calibrated Linear SVM (TF-IDF)"
        best_preds = preds_svm
        probs = pipe_svm.predict_proba(X_test)[:, 1]
    else:
        selected_model = pipe_lr
        selected_name = "Logistic Regression (TF-IDF)"
        best_preds = preds_lr
        probs = pipe_lr.predict_proba(X_test)[:, 1]
        
    print(f"\n---> Selected Best Model: {selected_name}")
    
    # Evaluation Metrics
    acc = accuracy_score(y_test, best_preds)
    prec = precision_score(y_test, best_preds)
    rec = recall_score(y_test, best_preds)
    f1 = f1_score(y_test, best_preds)
    roc_auc = roc_auc_score(y_test, probs)
    cm = confusion_matrix(y_test, best_preds)
    tn, fp, fn, tp = cm.ravel()
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    
    metrics = {
        "model_name": selected_name,
        "model_version": "email-v1.0",
        "trained_at": datetime.datetime.now().isoformat(),
        "total_dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "class_distribution": {
            "phishing": int(y.sum()),
            "safe": int((1 - y).sum())
        },
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp)
            }
        }
    }
    
    print("\n--- Model Evaluation Results ---")
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall:    {rec * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"False Positive Rate: {fpr * 100:.2f}%")
    print(f"False Negative Rate: {fnr * 100:.2f}%")
    print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
    
    # Save artifacts
    model_artifact_path = "backend/artifacts/email_model.joblib"
    metrics_path = "backend/artifacts/email_metrics.json"
    
    joblib.dump(selected_model, model_artifact_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"\nArtifact saved to: {model_artifact_path}")
    print(f"Metrics saved to: {metrics_path}")
    return metrics

if __name__ == "__main__":
    train_and_evaluate()
