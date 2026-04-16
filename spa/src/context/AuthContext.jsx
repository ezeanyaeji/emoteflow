import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import api, { setAccessToken } from '../api/axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to refresh using the httpOnly cookie (bypass interceptors)
  useEffect(() => {
    axios
      .post(`${API_BASE}/auth/refresh`, null, { withCredentials: true })
      .then(({ data }) => {
        setAccessToken(data.access_token);
        return api.get('/auth/me');
      })
      .then((res) => setUser(res.data))
      .catch(() => {
        setAccessToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    setAccessToken(data.access_token);
    const me = await api.get('/auth/me');
    setUser(me.data);
    return me.data;
  };

  const register = async (email, password, first_name, last_name, role = 'student') => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      first_name,
      last_name,
      role,
    });
    return data;
  };

  const logout = async () => {
    await api.post('/auth/logout').catch(() => {});
    setAccessToken(null);
    setUser(null);
  };

  const updateConsent = async (consent_camera) => {
    const { data } = await api.patch('/auth/me', { consent_camera });
    setUser(data);
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, updateConsent }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
