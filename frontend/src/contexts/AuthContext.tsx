import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserPublic } from '@/types';
import { getCurrentUser, verifyOtp, ApiError } from '@/api';

interface AuthContextType {
  user: UserPublic | null;
  loading: boolean;
  login: (email: string, otp: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      // Only clear the user session on authentication errors (401).
      // Transient failures (network errors, 5xx) should not log the user out.
      if (error instanceof ApiError && error.status === 401) {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email: string, otp: string) => {
    await verifyOtp(email, otp);
    await fetchUser();
  };

  const logout = () => {
    // TODO: Call a backend /logout endpoint to properly clear the HttpOnly session cookie.
    // The `session` cookie is HttpOnly and Secure, so it cannot be cleared from JavaScript.
    // A dedicated backend endpoint returning Set-Cookie with Max-Age=0 is required (tracked in a separate PR).
    setUser(null);
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
