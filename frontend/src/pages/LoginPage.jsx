import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, Lock, AlertCircle, ExternalLink, CheckCircle2, KeyRound, ArrowRight, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, loginWithGoogle, authConfig, fetchAuthState } = useAuth();
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [showConfigHelper, setShowConfigHelper] = useState(false);

  useEffect(() => {
    if (user) {
      navigate('/', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    const error = searchParams.get('error');
    if (error) {
      setErrorMsg(decodeURIComponent(error));
    }
  }, [searchParams]);

  const handleGoogleSignIn = async () => {
    setErrorMsg('');
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Google OAuth is not configured yet. Please configure backend/.env or use Instant Demo Login below.';
      setErrorMsg(detail);
      setLoading(false);
    }
  };

  const handleDemoSignIn = async (role = 'analyst') => {
    setErrorMsg('');
    setDemoLoading(true);
    try {
      const res = await api.post('/auth/demo-login', { role });
      if (res.data.is_authenticated) {
        if (fetchAuthState) await fetchAuthState();
        navigate('/', { replace: true });
      }
    } catch (err) {
      console.error('Demo login error', err);
      setErrorMsg('Failed to sign in via demo mode.');
    } finally {
      setDemoLoading(false);
    }
  };

  const isConfigured = authConfig?.is_google_configured;

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-md w-full space-y-6 bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden">
        
        {/* Glow accent */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center relative">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-lg shadow-sky-500/10">
            <ShieldCheck className="w-9 h-9 text-sky-400" />
          </div>
          <h2 className="mt-5 text-2xl font-bold tracking-tight text-white">
            ShieldSOC Security Portal
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            AI-Powered Phishing & Login Defense Center
          </p>
          <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs font-medium text-slate-300">
            <Lock className="w-3.5 h-3.5 text-sky-400" />
            <span>Google Workspace / Gmail Single Sign-On</span>
          </div>
        </div>

        {errorMsg && (
          <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 p-4 text-xs text-rose-300 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-rose-200">Notice</p>
              <p className="break-words">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* Real Google Login Action */}
        <div className="space-y-3">
          <button
            id="google-signin-btn"
            type="button"
            disabled={loading || demoLoading}
            onClick={handleGoogleSignIn}
            className="w-full flex items-center justify-center gap-3 px-5 py-3.5 border border-slate-700 rounded-xl bg-white hover:bg-slate-50 text-slate-900 font-semibold text-sm transition-all shadow-md hover:shadow-lg disabled:opacity-60 active:scale-[0.99] cursor-pointer"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>{loading ? 'Connecting to Google...' : 'Sign in with Google'}</span>
          </button>

          {/* Quick Access / Demo Mode Bypass */}
          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-slate-800"></div>
            <span className="flex-shrink mx-3 text-slate-500 text-[11px] uppercase tracking-wider font-mono">
              or enter platform now
            </span>
            <div className="flex-grow border-t border-slate-800"></div>
          </div>

          <button
            type="button"
            disabled={loading || demoLoading}
            onClick={() => handleDemoSignIn('analyst')}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-800/90 hover:bg-slate-700/80 border border-slate-700 text-slate-200 font-semibold text-xs transition cursor-pointer shadow-sm group hover:border-sky-500/50"
          >
            <UserCheck className="w-4 h-4 text-sky-400 group-hover:scale-110 transition-transform" />
            <span>{demoLoading ? 'Logging in...' : 'Enter Directly (Instant Demo Access)'}</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
          </button>

          <p className="text-center text-[11px] text-slate-500">
            Allows instant review of all features without waiting for Google Cloud keys.
          </p>
        </div>

        {/* OAuth Status Card */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isConfigured ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
              <span className="text-slate-400">
                Google OAuth: {isConfigured ? (
                  <span className="text-emerald-400 font-medium">Configured & Ready</span>
                ) : (
                  <span className="text-amber-400 font-medium">Awaiting Credentials in backend/.env</span>
                )}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowConfigHelper(!showConfigHelper)}
              className="text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>{showConfigHelper ? 'Hide Setup' : 'How to Setup'}</span>
            </button>
          </div>

          {showConfigHelper && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-3 font-mono">
              <div className="text-slate-300 font-semibold flex items-center gap-1.5 font-sans">
                <CheckCircle2 className="w-4 h-4 text-sky-400" />
                <span>3-Minute Google Cloud Console Setup:</span>
              </div>
              <ol className="list-decimal pl-4 space-y-1.5 text-slate-400">
                <li>
                  Open{' '}
                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noreferrer"
                    className="text-sky-400 hover:underline inline-flex items-center gap-0.5"
                  >
                    Google Cloud Console <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
                <li>Enable <strong>Gmail API</strong> in APIs & Services &gt; Library</li>
                <li>Create OAuth 2.0 Client ID (Application type: <strong>Web application</strong>)</li>
                <li>
                  Authorized JavaScript origin:{' '}
                  <code className="text-amber-300 bg-slate-900 px-1 py-0.5 rounded">http://localhost:5173</code>
                </li>
                <li>
                  Authorized redirect URIs:{' '}
                  <code className="text-amber-300 bg-slate-900 px-1 py-0.5 rounded">http://localhost:8000/api/auth/google/callback</code>
                  <br />
                  <code className="text-amber-300 bg-slate-900 px-1 py-0.5 rounded">http://localhost:8000/api/integrations/gmail/callback</code>
                </li>
                <li>
                  Paste keys in file: <code className="text-sky-300">backend/.env</code>
                </li>
              </ol>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
