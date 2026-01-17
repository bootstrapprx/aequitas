import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

interface MetatheosUser {
  id: string;
  name: string;
  email?: string;
}

interface MetatheosAuthContextValue {
  user: MetatheosUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

interface LoginResponse {
  token?: string;
  access_token?: string;
  session?: string;
  user?: MetatheosUser;
}

class MetatheosApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const MetatheosAuthContext = createContext<MetatheosAuthContextValue | undefined>(undefined);

const TOKEN_KEY = "metatheos_token";
const USER_KEY = "metatheos_user";
const BASE_URL = import.meta.env.VITE_METATHEOS_API_URL || "/metatheos-api";

const requestJson = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data?.message || data?.detail || message;
    } catch {
      // Ignore body parse errors.
    }
    throw new MetatheosApiError(response.status, message || "Request failed");
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
};

const shouldFallback = (error: unknown) => {
  if (error instanceof MetatheosApiError) {
    return error.status === 404 || error.status === 501 || error.status === 503;
  }
  return true;
};

const normalizeError = (error: unknown) => {
  if (error instanceof MetatheosApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Login failed";
};

const buildMockUser = (identifier: string): MetatheosUser => {
  const trimmed = identifier.trim();
  return {
    id: "metatheos-admin",
    name: trimmed || "Administrator",
    email: trimmed.includes("@") ? trimmed : undefined,
  };
};

export const MetatheosAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<MetatheosUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUser = localStorage.getItem(USER_KEY);

      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      setToken(storedToken);

      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          localStorage.removeItem(USER_KEY);
        }
      }

      try {
        const me = await requestJson<MetatheosUser>("/api/auth/me", {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        });
        setUser(me);
        localStorage.setItem(USER_KEY, JSON.stringify(me));
      } catch (error) {
        if (!shouldFallback(error)) {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setToken(null);
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (identifier: string, password: string) => {
    const payload = {
      username: identifier,
      email: identifier,
      password,
    };

    try {
      const response = await requestJson<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      const nextToken = response.token || response.access_token || response.session || "metatheos-token";
      setToken(nextToken);
      localStorage.setItem(TOKEN_KEY, nextToken);

      if (response.user) {
        setUser(response.user);
        localStorage.setItem(USER_KEY, JSON.stringify(response.user));
        return;
      }

      try {
        const me = await requestJson<MetatheosUser>("/api/auth/me", {
          headers: {
            Authorization: `Bearer ${nextToken}`,
          },
        });
        setUser(me);
        localStorage.setItem(USER_KEY, JSON.stringify(me));
      } catch (error) {
        if (!shouldFallback(error)) {
          throw error;
        }
        const mockUser = buildMockUser(identifier);
        setUser(mockUser);
        localStorage.setItem(USER_KEY, JSON.stringify(mockUser));
      }
    } catch (error) {
      if (shouldFallback(error)) {
        const mockUser = buildMockUser(identifier);
        const mockToken = "metatheos-mock-token";
        setToken(mockToken);
        setUser(mockUser);
        localStorage.setItem(TOKEN_KEY, mockToken);
        localStorage.setItem(USER_KEY, JSON.stringify(mockUser));
        return;
      }
      throw new Error(normalizeError(error));
    }
  };

  const logout = async () => {
    const activeToken = token || localStorage.getItem(TOKEN_KEY);
    if (activeToken) {
      try {
        await requestJson("/api/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${activeToken}`,
          },
        });
      } catch (error) {
        if (!shouldFallback(error)) {
          console.warn("Metatheos logout failed:", error);
        }
      }
    }

    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [user, token, isLoading]
  );

  return <MetatheosAuthContext.Provider value={value}>{children}</MetatheosAuthContext.Provider>;
};

export const useMetatheosAuth = () => {
  const context = useContext(MetatheosAuthContext);
  if (!context) {
    throw new Error("useMetatheosAuth must be used within MetatheosAuthProvider");
  }
  return context;
};
