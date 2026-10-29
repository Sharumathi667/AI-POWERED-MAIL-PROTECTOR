import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authConfig, setAuthConfig] = useState(null);

  const fetchAuthState = useCallback(async () => {
    try {
      const [meRes, configRes] = await Promise.all([
        api.get('/auth/me'),
        api.get('/auth/config'),
      ]);
      setAuthConfig(configRes.data);
      if (meRes.data.is_authenticated) {
        setUser(meRes.data.user);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAuthState();
  }, [fetchAuthState]);

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {}
    setUser(null);
    window.location.href = '/login';
  };

  const loginWithGoogle = async () => {
    try {
      const res = await api.get('/auth/google/url');
      window.location.href = res.data.url;
    } catch (err) {
      console.error('Failed to get Google OAuth URL', err);
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, authConfig, logout, loginWithGoogle, fetchAuthState }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
