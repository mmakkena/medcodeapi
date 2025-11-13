'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string, companyName?: string, role?: string, website?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { data: session, status } = useSession();

  useEffect(() => {
    // Check NextAuth session first (for OAuth)
    if (status === 'loading') {
      return;
    }

    if (status === 'authenticated' && session?.accessToken) {
      // User is authenticated via NextAuth (Google/OAuth)
      const oauthToken = session.accessToken as string;
      setToken(oauthToken);
      // Store token in localStorage so API calls can access it
      localStorage.setItem('token', oauthToken);
      setUser({
        id: session.user.id as string,
        email: session.user.email as string,
        is_active: true,
        is_admin: false, // OAuth users are not admin by default
        created_at: new Date().toISOString(),
      });
      setLoading(false);
      return;
    }

    // Fall back to localStorage token (for email/password auth)
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setLoading(false);
    }
  }, [session, status]);

  const fetchUser = async (authToken: string) => {
    try {
      const response = await authAPI.getMe();
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await authAPI.login(email, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    await fetchUser(access_token);
    router.push('/dashboard');
  };

  const signup = async (email: string, password: string, fullName?: string, companyName?: string, role?: string, website?: string) => {
    await authAPI.signup(email, password, fullName, companyName, role, website);
    // Auto-login after signup
    await login(email, password);
  };

  const logout = async () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    // If using NextAuth, sign out from there too
    if (session) {
      const { signOut } = await import('next-auth/react');
      await signOut({ redirect: false });
    }
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
