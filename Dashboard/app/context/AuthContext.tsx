import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { verifySessionCall } from '../services/authService';
import type { AuthUser } from '../types/auth';
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '../utils/tokenStorage';

interface AuthContextType {
  user: AuthUser | null;
  login: (user: AuthUser, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<AuthUser>) => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }

    verifySessionCall()
      .then(setUser)
      .catch((error) => {
        console.error('Session verification failed', error);
        clearAccessToken();
      })
      .finally(() => setLoading(false));
  }, []);

  const login = (nextUser: AuthUser, token: string) => {
    setUser(nextUser);
    setAccessToken(token);
  };

  const logout = () => {
    setUser(null);
    clearAccessToken();
  };

  const updateUser = (updates: Partial<AuthUser>) => {
    setUser((current) => {
      if (!current) return current;
      return { ...current, ...updates };
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        updateUser,
        isAuthenticated: Boolean(user),
        loading,
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
