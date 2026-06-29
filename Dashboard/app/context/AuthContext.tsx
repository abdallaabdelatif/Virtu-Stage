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
import { UNAUTHORIZED_EVENT } from '../utils/authEvents';

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
    const handleUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () =>
      window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

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
      {loading ? (
        <div
          role="status"
          aria-live="polite"
          className="flex min-h-screen items-center justify-center bg-canvas text-secondary"
        >
          <span className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent" />
          <span className="sr-only">Loading your session</span>
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
