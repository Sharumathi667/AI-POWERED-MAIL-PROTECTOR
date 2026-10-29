import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  BarChart3, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Info, 
  Layers, 
  RefreshCw, 
  Sliders, 
  Terminal,
  Activity
} from 'lucide-react';
import { fetchModelsOverview, fetchModelsMetrics } from '../services/api';
import { SimulatedDataBanner } from '../components/Badges';

export default function ModelPerformancePage() {
  const [models, setModels] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [mList, mMetrics] = await Promise.all([
        fetchModelsOverview(),
        fetchModelsMetrics(),
      ]);
      setModels(mList);
      setMetrics(mMetrics);
    } catch (err) {
      console.error('Failed to load ML metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-slate-400 text-sm font-mono">Loading Real ML Model Evaluation Artifacts...</p>
      </div>
    );
  }

  const emailM = metrics?.email_model?.metrics;
  const loginM = metrics?.login_model?.metrics;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Cpu className="w-6 h-6 text-sky-400" />
            <span>Machine Learning Performance & Metrics</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical evaluation statistics computed directly on held-out test splits. No fabricated metrics.
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reload Metrics</span>
        </button>
      </div>

      <SimulatedDataBanner />

      {/* Real-World Generalization Disclaimer Box */}
      <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-xl flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-300/90 space-y-1">
          <strong className="text-amber-200 font-semibold block">Academic Integrity & Zero-Day Generalization Notice:</strong>
          <p>
            The accuracy, precision, and recall metrics presented below were measured by executing rigorous scikit-learn holdout evaluations on our programmatically generated synthetic datasets.
            While these models perform near-optimally on simulated campus scenarios, real-world deployment against human adversaries requires ongoing continuous learning, adversarial retraining, and threat intelligence feed integration.
          </p>
        </div>
      </div>

      {/* Model 1: Phishing Email Classifier */}
      <div className="cyber-card p-6 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20 font-bold">
                MODEL 1
              </span>
              <h2 className="text-base font-bold text-slate-100">Phishing Email Classifier</h2>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Algorithm: <span className="text-slate-200 font-mono">TF-IDF Vectorizer + Logistic Regression / Calibrated SVM</span> | Test Split: <span className="text-slate-200 font-mono">1,040 emails (20% held-out)</span>
            </p>
          </div>
          <div className="text-right text-[11px] font-mono text-slate-500">
            Trained: {metrics?.email_model?.trained_at ? new Date(metrics.email_model.trained_at).toLocaleString() : 'Recent'}
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Accuracy</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              {emailM ? `${(emailM.accuracy * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Precision</span>
            <span className="text-lg font-bold font-mono text-sky-400">
              {emailM ? `${(emailM.precision * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Recall</span>
            <span className="text-lg font-bold font-mono text-sky-400">
              {emailM ? `${(emailM.recall * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">F1-Score</span>
            <span className="text-lg font-bold font-mono text-indigo-400">
              {emailM ? `${(emailM.f1_score * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">ROC-AUC</span>
            <span className="text-lg font-bold font-mono text-purple-400">
              {emailM ? emailM.roc_auc.toFixed(4) : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">False Pos Rate</span>
            <span className="text-lg font-bold font-mono text-slate-300">
              {emailM ? `${(emailM.false_positive_rate * 100).toFixed(2)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">False Neg Rate</span>
            <span className="text-lg font-bold font-mono text-slate-300">
              {emailM ? `${(emailM.false_negative_rate * 100).toFixed(2)}%` : '--'}
            </span>
          </div>
        </div>

        {/* Confusion Matrix Table */}
        {emailM?.confusion_matrix && (
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <h4 className="text-xs font-mono uppercase text-slate-400 mb-3 flex items-center justify-between">
              <span>Holdout Confusion Matrix (N = {metrics.email_model.test_size})</span>
              <span className="text-[11px] text-slate-500">True Label vs Predicted Label</span>
            </h4>
            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto text-center font-mono text-xs">
              <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30">
                <span className="text-[10px] text-emerald-400 block uppercase">True Negative (Safe Classified Safe)</span>
                <span className="text-xl font-bold text-emerald-300">{emailM.confusion_matrix.true_negative}</span>
              </div>
              <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30">
                <span className="text-[10px] text-rose-400 block uppercase">False Positive (Safe Flagged Phish)</span>
                <span className="text-xl font-bold text-rose-300">{emailM.confusion_matrix.false_positive}</span>
              </div>
              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30">
                <span className="text-[10px] text-amber-400 block uppercase">False Negative (Phish Missed)</span>
                <span className="text-xl font-bold text-amber-300">{emailM.confusion_matrix.false_negative}</span>
              </div>
              <div className="p-3 rounded bg-sky-500/10 border border-sky-500/30">
                <span className="text-[10px] text-sky-400 block uppercase">True Positive (Phish Caught)</span>
                <span className="text-xl font-bold text-sky-300">{emailM.confusion_matrix.true_positive}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Model 2: Suspicious Login Anomaly Detector */}
      <div className="cyber-card p-6 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-bold">
                MODEL 2
              </span>
              <h2 className="text-base font-bold text-slate-100">Suspicious Login Anomaly Detector</h2>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Algorithm: <span className="text-slate-200 font-mono">Isolation Forest (150 Trees, contamination=0.18) + Heuristic Guardrails</span> | Test Split: <span className="text-slate-200 font-mono">2,106 events (20% held-out)</span>
            </p>
          </div>
          <div className="text-right text-[11px] font-mono text-slate-500">
            Trained: {metrics?.login_model?.trained_at ? new Date(metrics.login_model.trained_at).toLocaleString() : 'Recent'}
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Accuracy</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              {loginM ? `${(loginM.accuracy * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Precision</span>
            <span className="text-lg font-bold font-mono text-amber-400">
              {loginM ? `${(loginM.precision * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Recall</span>
            <span className="text-lg font-bold font-mono text-amber-400">
              {loginM ? `${(loginM.recall * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">F1-Score</span>
            <span className="text-lg font-bold font-mono text-indigo-400">
              {loginM ? `${(loginM.f1_score * 100).toFixed(1)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">ROC-AUC</span>
            <span className="text-lg font-bold font-mono text-purple-400">
              {loginM ? loginM.roc_auc.toFixed(4) : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">False Pos Rate</span>
            <span className="text-lg font-bold font-mono text-slate-300">
              {loginM ? `${(loginM.false_positive_rate * 100).toFixed(2)}%` : '--'}
            </span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">False Neg Rate</span>
            <span className="text-lg font-bold font-mono text-slate-300">
              {loginM ? `${(loginM.false_negative_rate * 100).toFixed(2)}%` : '--'}
            </span>
          </div>
        </div>

        {/* Confusion Matrix Table */}
        {loginM?.confusion_matrix && (
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <h4 className="text-xs font-mono uppercase text-slate-400 mb-3 flex items-center justify-between">
              <span>Holdout Confusion Matrix (N = {metrics.login_model.test_size})</span>
              <span className="text-[11px] text-slate-500">True Label vs Predicted Label</span>
            </h4>
            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto text-center font-mono text-xs">
              <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30">
                <span className="text-[10px] text-emerald-400 block uppercase">True Negative (Normal Sign-in)</span>
                <span className="text-xl font-bold text-emerald-300">{loginM.confusion_matrix.true_negative}</span>
              </div>
              <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30">
                <span className="text-[10px] text-rose-400 block uppercase">False Positive (False Alarm)</span>
                <span className="text-xl font-bold text-rose-300">{loginM.confusion_matrix.false_positive}</span>
              </div>
              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30">
                <span className="text-[10px] text-amber-400 block uppercase">False Negative (Missed Anomaly)</span>
                <span className="text-xl font-bold text-amber-300">{loginM.confusion_matrix.false_negative}</span>
              </div>
              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30">
                <span className="text-[10px] text-amber-400 block uppercase">True Positive (Anomaly Detected)</span>
                <span className="text-xl font-bold text-amber-300">{loginM.confusion_matrix.true_positive}</span>
              </div>
            </div>
          </div>
        )}

        {/* Features Input Specification */}
        <div className="pt-2">
          <span className="text-xs font-mono text-slate-400 block mb-2 font-semibold">Engineered Features Monitored:</span>
          <div className="flex flex-wrap gap-2 text-[11px] font-mono">
            {metrics?.login_model?.features?.map((f, i) => (
              <span key={i} className="px-2.5 py-1 bg-slate-900 border border-slate-800 rounded text-slate-300">
                {f}
              </span>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
