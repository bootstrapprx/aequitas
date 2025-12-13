import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '@/integrations/api';
import { useNavigate } from 'react-router-dom';
import { User, LoginResponse } from '@/types/user';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  companyIds: string[];
  currentCompanyId: string | null;
  forcePasswordReset: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, isInitialSignup?: boolean, companyName?: string, companyIds?: string[]) => Promise<void>;
  logout: () => void;
  switchCompany: (companyId: string) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'aequitas_token';
const USER_KEY = 'aequitas_user';
const COMPANY_IDS_KEY = 'aequitas_company_ids';
const CURRENT_COMPANY_KEY = 'aequitas_current_company';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [companyIds, setCompanyIds] = useState<string[]>([]);
  const [currentCompanyId, setCurrentCompanyId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load and validate token from localStorage on mount
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUser = localStorage.getItem(USER_KEY);
      const storedCompanyIds = localStorage.getItem(COMPANY_IDS_KEY);
      const storedCurrentCompany = localStorage.getItem(CURRENT_COMPANY_KEY);

      if (storedToken && storedUser) {
        try {
          // Validate token by fetching user info
          api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          const userResponse = await api.get('/auth/me');

          // Token is valid, set user data
          setToken(storedToken);
          setUser(userResponse.data);

          if (storedCompanyIds) {
            setCompanyIds(JSON.parse(storedCompanyIds));
          }

          if (storedCurrentCompany) {
            setCurrentCompanyId(storedCurrentCompany);
          }
        } catch (error) {
          // Token is invalid or expired, clear everything
          console.error('Token validation failed:', error);
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          localStorage.removeItem(COMPANY_IDS_KEY);
          localStorage.removeItem(CURRENT_COMPANY_KEY);
          delete api.defaults.headers.common['Authorization'];
        }
      }
      setIsLoading(false);
    };

    validateToken();
  }, []);

  // Update API headers when token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post<LoginResponse>('/auth/login-json', { email, password });
      const { access_token, company_ids, preferred_company_id } = response.data;

      setToken(access_token);
      localStorage.setItem(TOKEN_KEY, access_token);

      // Fetch user info
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      localStorage.setItem(USER_KEY, JSON.stringify(userResponse.data));

      // Store company context
      if (company_ids && company_ids.length > 0) {
        setCompanyIds(company_ids);
        localStorage.setItem(COMPANY_IDS_KEY, JSON.stringify(company_ids));

        // Set current company to preferred or first available
        const initialCompany = preferred_company_id || company_ids[0];
        setCurrentCompanyId(initialCompany);
        localStorage.setItem(CURRENT_COMPANY_KEY, initialCompany);
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (
    email: string,
    password: string,
    isInitialSignup: boolean = false,
    companyName?: string,
    companyIds?: string[]
  ) => {
    try {
      const payload: any = { email, password };

      if (isInitialSignup && companyName) {
        payload.is_initial_signup = true;
        payload.company_name = companyName;
      } else if (companyIds && companyIds.length > 0) {
        payload.company_ids = companyIds;
      }

      await api.post('/auth/register', payload);
      // After registration, automatically log in
      await login(email, password);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const switchCompany = (companyId: string) => {
    if (companyIds.includes(companyId)) {
      setCurrentCompanyId(companyId);
      localStorage.setItem(CURRENT_COMPANY_KEY, companyId);
      // Optionally invalidate queries here if using React Query
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setCompanyIds([]);
    setCurrentCompanyId(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(COMPANY_IDS_KEY);
    localStorage.removeItem(CURRENT_COMPANY_KEY);
    delete api.defaults.headers.common['Authorization'];
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    companyIds,
    currentCompanyId,
    forcePasswordReset: user?.force_password_reset || false,
    login,
    register,
    logout,
    switchCompany,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

