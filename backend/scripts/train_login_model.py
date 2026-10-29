"""
Train Login Anomaly Detection Model (Isolation Forest + Feature Scaler)
Features:
- login_hour (0-23)
- day_of_week (0-6)
- failed_attempts
- is_new_device
- is_new_location
- distance_from_usual_location_km
- minutes_since_previous_login
- login_success
- impossible_travel

Pipeline:
- Standardized feature transformation
- Isolation Forest training (unsupervised / semi-supervised anomaly scoring)
- Calibrated anomaly score mapping to 0-100 range
- Evaluated on holdout test set with ground-truth synthetic labels
- Save model artifact & metrics JSON
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

FEATURE_COLS = [
    "login_hour",
    "day_of_week",
    "failed_attempts",
    "is_new_device",
    "is_new_location",
    "distance_from_usual_location_km",
    "minutes_since_previous_login",
    "login_success",
    "impossible_travel"
]

def engineer_features(df):
    """Derive time features and format numerical inputs."""
    timestamps = pd.to_datetime(df["timestamp"])
    features_df = pd.DataFrame(index=df.index)
    
    features_df["login_hour"] = timestamps.dt.hour
    features_df["day_of_week"] = timestamps.dt.dayofweek
    features_df["failed_attempts"] = df["failed_attempts"].fillna(0).astype(float)
    features_df["is_new_device"] = df["is_new_device"].fillna(0).astype(float)
    features_df["is_new_location"] = df["is_new_location"].fillna(0).astype(float)
    features_df["distance_from_usual_location_km"] = df["distance_from_usual_location_km"].fillna(0.0).astype(float)
    features_df["minutes_since_previous_login"] = df["minutes_since_previous_login"].fillna(60.0).astype(float)
    features_df["login_success"] = df["login_success"].fillna(1).astype(float)
    features_df["impossible_travel"] = df["impossible_travel"].fillna(0).astype(float)
    
    return features_df[FEATURE_COLS]

def train_and_evaluate(data_path="backend/data/raw/synthetic_login_events.csv"):
    print("=" * 60)
    print("TRAINING LOGIN ANOMALY DETECTION MODEL (Isolation Forest)")
    print("=" * 60)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Login dataset not found at {data_path}. Run generate_synthetic_data.py first.")
        
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} login events from {data_path}")
    
    X = engineer_features(df)
    y = (df["label"] == "suspicious").astype(int)
    
    # Train / test split
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.20, random_state=42, stratify=y
    )
    
    os.makedirs("backend/data/processed", exist_ok=True)
    os.makedirs("backend/artifacts", exist_ok=True)
    df_train.to_csv("backend/data/processed/login_train.csv", index=False)
    df_test.to_csv("backend/data/processed/login_test.csv", index=False)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Isolation Forest with expected contamination ~18%
    iso_forest = IsolationForest(
        n_estimators=150,
        max_samples="auto",
        contamination=0.18,
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting Isolation Forest...")
    iso_forest.fit(X_train_scaled)
    
    # Decision function: lower values mean more anomalous
    test_raw_scores = iso_forest.decision_function(X_test_scaled)
    # Convert decision score to 0-100 anomaly score where higher = more anomalous
    # Decision function typically lies in [-0.5, 0.5]
    # Min-max normalization based on train distribution:
    train_raw = iso_forest.decision_function(X_train_scaled)
    min_val, max_val = train_raw.min(), train_raw.max()
    
    # Normalized anomaly score: 0 (most normal) to 100 (most anomalous)
    def normalize_scores(raw):
        clipped = np.clip(raw, min_val, max_val)
        norm = 1.0 - ((clipped - min_val) / (max_val - min_val + 1e-9))
        return np.round(norm * 100, 1)
        
    anomaly_scores_test = normalize_scores(test_raw_scores)
    
    # Predictions: -1 for outlier/anomaly, 1 for inlier
    raw_preds = iso_forest.predict(X_test_scaled)
    preds = np.where(raw_preds == -1, 1, 0) # 1 = suspicious anomaly
    
    # Combined with heuristic security rule: If impossible travel or failed_attempts >= 5, flag as suspicious
    rule_override = (X_test["impossible_travel"] == 1) | (X_test["failed_attempts"] >= 5)
    final_preds = np.where(rule_override, 1, preds)
    
    # Metrics
    acc = accuracy_score(y_test, final_preds)
    prec = precision_score(y_test, final_preds)
    rec = recall_score(y_test, final_preds)
    f1 = f1_score(y_test, final_preds)
    roc_auc = roc_auc_score(y_test, anomaly_scores_test / 100.0)
    cm = confusion_matrix(y_test, final_preds)
    tn, fp, fn, tp = cm.ravel()
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    
    metrics = {
        "model_name": "Isolation Forest + Heuristic Guardrails",
        "model_version": "login-v1.0",
        "trained_at": datetime.datetime.now().isoformat(),
        "total_dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "contamination": 0.18,
        "features": FEATURE_COLS,
        "score_calibration": {
            "min_val": float(min_val),
            "max_val": float(max_val)
        },
        "class_distribution": {
            "suspicious": int(y.sum()),
            "normal": int((1 - y).sum())
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
    
    print("\n--- Login Anomaly Evaluation Results ---")
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall:    {rec * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"False Positive Rate: {fpr * 100:.2f}%")
    print(f"False Negative Rate: {fnr * 100:.2f}%")
    print(f"Confusion Matrix: [TN={tn}, FP={fp}, FN={fn}, TP={tp}]")
    
    # Save artifacts
    model_artifact = {
        "scaler": scaler,
        "model": iso_forest,
        "feature_cols": FEATURE_COLS,
        "score_calibration": {
            "min_val": float(min_val),
            "max_val": float(max_val)
        }
    }
    
    joblib.dump(model_artifact, "backend/artifacts/login_model.joblib")
    with open("backend/artifacts/login_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("\nSaved login model artifact to backend/artifacts/login_model.joblib")
    print("Saved login metrics to backend/artifacts/login_metrics.json")
    return metrics

if __name__ == "__main__":
    train_and_evaluate()
