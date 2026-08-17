"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi } from "@/lib/api";
import type { UserOut } from "@/lib/types";

const TOKEN_STORAGE_KEY = "stock_platform_token";

interface AuthContextValue {
  user: UserOut | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    const verification = stored
      ? authApi
          .me(stored)
          .then((u) => {
            setToken(stored);
            setUser(u);
          })
          .catch(() => {
            // Stored token is invalid/expired — clear it rather than staying
            // "logged in" with a token that fails every subsequent request.
            window.localStorage.removeItem(TOKEN_STORAGE_KEY);
          })
      : Promise.resolve();

    verification.finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await authApi.login(email, password);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  }

  async function signup(email: string, password: string, displayName: string) {
    const res = await authApi.signup(email, password, displayName);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
