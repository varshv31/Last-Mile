import { useNavigate } from "@tanstack/react-router";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi, getTokens, setTokens } from "./api-client";
import type { UserResponse, UserRole } from "./api-types";

interface AuthContextValue {
  user: UserResponse | null;
  status: "loading" | "authenticated" | "unauthenticated";
  login: (email: string, password: string) => Promise<UserResponse>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function homePathForRole(role: UserRole | undefined | null): string {
  if (role === "ADMIN") return "/admin";
  if (role === "AGENT") return "/agent";
  return "/dashboard";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");

  const loadUser = useCallback(async () => {
    if (!getTokens()?.access_token) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
      setStatus("authenticated");
    } catch {
      setTokens(null);
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  useEffect(() => {
    void loadUser();
    const onUnauth = () => {
      setUser(null);
      setStatus("unauthenticated");
    };
    window.addEventListener("lmd:unauthenticated", onUnauth);
    return () => window.removeEventListener("lmd:unauthenticated", onUnauth);
  }, [loadUser]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login({ email, password });
    setTokens({ access_token: tokens.access_token, refresh_token: tokens.refresh_token });
    const me = await authApi.me();
    setUser(me);
    setStatus("authenticated");
    return me;
  }, []);

  const logout = useCallback(() => {
    setTokens(null);
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, logout, refreshUser: loadUser }),
    [user, status, login, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

/** Redirects to /login when signed out, or to the role home when the role mismatches. */
export function useRequireRole(role: UserRole) {
  const { user, status } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === "unauthenticated") {
      void navigate({ to: "/login", replace: true });
    } else if (status === "authenticated" && user && user.role !== role) {
      void navigate({ to: homePathForRole(user.role), replace: true });
    }
  }, [status, user, role, navigate]);

  return { user, ready: status === "authenticated" && user?.role === role, status };
}
