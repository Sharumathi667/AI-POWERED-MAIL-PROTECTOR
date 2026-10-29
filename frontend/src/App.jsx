import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import EmailInvestigationPage from './pages/EmailInvestigationPage';
import LoginMonitoringPage from './pages/LoginMonitoringPage';
import IncidentInvestigationPage from './pages/IncidentInvestigationPage';
import ModelPerformancePage from './pages/ModelPerformancePage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import { AuthProvider } from './context/AuthContext';

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-[#080c14] text-slate-100 cyber-grid-bg">
          <Navbar />
          
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/emails" element={<EmailInvestigationPage />} />
              <Route path="/logins" element={<LoginMonitoringPage />} />
              <Route path="/incidents" element={<IncidentInvestigationPage />} />
              <Route path="/models" element={<ModelPerformancePage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <footer className="border-t border-slate-800/80 bg-[#0a0f1d]/80 py-4 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-400">ShieldSOC</span>
                <span>— AI Phishing & Suspicious Login Investigation Challenge (PS 1.3)</span>
              </div>
              <div className="flex items-center gap-4 font-mono text-[11px]">
                <span>Google OAuth 2.0 Auth</span>
                <span>FastAPI + SQLite</span>
                <span>Dual ML Ensemble</span>
              </div>
            </div>
          </footer>
        </div>
      </AuthProvider>
    </Router>
  );
}
