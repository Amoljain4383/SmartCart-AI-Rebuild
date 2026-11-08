import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('smartcart_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('smartcart_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Sync state if invalidated by API client (401)
  useEffect(() => {
    const handleInvalidated = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener('smartcart:auth_invalidated', handleInvalidated);
    return () => window.removeEventListener('smartcart:auth_invalidated', handleInvalidated);
  }, []);

  // Fetch latest profile on initial load if token exists
  useEffect(() => {
    let isMounted = true;

    async function loadProfile() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const freshUser = await authApi.getProfile();
        if (isMounted) {
          setUser(freshUser);
          localStorage.setItem('smartcart_user', JSON.stringify(freshUser));
        }
      } catch (err) {
        if (isMounted) {
          // Token expired or invalid
          setToken(null);
          setUser(null);
          localStorage.removeItem('smartcart_token');
          localStorage.removeItem('smartcart_user');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => {
      isMounted = false;
    };
  }, [token]);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('smartcart_token', data.access_token);
    localStorage.setItem('smartcart_user', JSON.stringify(data.user));
    return data.user;
  }, []);

  const register = useCallback(async (email, password, full_name) => {
    const data = await authApi.register(email, password, full_name);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('smartcart_token', data.access_token);
    localStorage.setItem('smartcart_user', JSON.stringify(data.user));
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('smartcart_token');
      localStorage.removeItem('smartcart_user');
    }
  }, []);

  const value = {
    token,
    user,
    loading,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
