import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { authApi } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string | null;
  paid: boolean;
  createdAt?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const storeAuth = (token: string, user: User) => {
    localStorage.setItem('sf_token', token);
    localStorage.setItem('sf_user', JSON.stringify(user));
    setToken(token);
    setUser(user);
  };

  const clearAuth = () => {
    localStorage.removeItem('sf_token');
    localStorage.removeItem('sf_user');
    setToken(null);
    setUser(null);
  };

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login({ email, password });
    storeAuth(data.token, data.user);
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    const data = await authApi.register({ email, password, name });
    storeAuth(data.token, data.user);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const data = await authApi.me();
      setUser(data);
      localStorage.setItem('sf_user', JSON.stringify(data));
    } catch {
      clearAuth();
    }
  }, []);

  // Restore session on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('sf_token');
    const storedUser = localStorage.getItem('sf_user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      // Verify token is still valid in background
      authApi.me().then((data) => {
        setUser(data);
        localStorage.setItem('sf_user', JSON.stringify(data));
      }).catch(() => {
        clearAuth();
      }).finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
