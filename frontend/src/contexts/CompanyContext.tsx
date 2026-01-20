import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';
import { useQueryClient } from '@tanstack/react-query';
import type { Company } from '@/types/company';

interface CompanyContextType {
  selectedCompanyId: string | null;
  selectedCompany: Company | null;
  companies: Company[];
  isLoadingCompanies: boolean;
  isInitialized: boolean;
  setSelectedCompanyId: (companyId: string | null) => void;
  refreshCompanies: () => Promise<void>;
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

const SELECTED_COMPANY_KEY = 'aequitas_selected_company';

export const CompanyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated, companyIds, currentCompanyId } = useAuth();
  const queryClient = useQueryClient();
  const [selectedCompanyId, setSelectedCompanyIdState] = useState<string | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch companies when authenticated
  const fetchCompanies = async () => {
    if (!isAuthenticated) {
      setCompanies([]);
      setSelectedCompanyIdState(null);
      setSelectedCompany(null);
      setIsLoadingCompanies(false);
      setIsInitialized(false);
      return;
    }

    setIsInitialized(false);
    setIsLoadingCompanies(true);
    try {
      let companiesData: Company[] = [];
      if (companyIds && companyIds.length > 0) {
        const results = await Promise.all(
          companyIds.map(async (id) => {
            try {
              return await api.get<Company>(`/companies/${id}`);
            } catch (error) {
              console.error(`Failed to fetch company ${id}:`, error);
              return null;
            }
          })
        );
        companiesData = results.filter((c): c is Company => c !== null);
      } else {
        companiesData = await api.get<Company[]>('/companies');
      }

      setCompanies(companiesData);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
      setCompanies([]);
    } finally {
      setIsLoadingCompanies(false);
      setIsInitialized(true);
    }
  };

  // Initialize companies on mount and when auth state changes
  useEffect(() => {
    fetchCompanies();
  }, [isAuthenticated, companyIds?.join(',')]);

  // Initialize selected company from localStorage or auth context
  useEffect(() => {
    if (!isAuthenticated) {
      setSelectedCompanyIdState(null);
      setSelectedCompany(null);
      return;
    }

    // Try to restore from localStorage first
    const storedCompanyId = localStorage.getItem(SELECTED_COMPANY_KEY);
    const availableCompanyIds = (companyIds && companyIds.length > 0)
      ? companyIds
      : companies.map((company) => company.id);

    // Determine which company to select
    let companyToSelect: string | null = null;

    if (storedCompanyId && availableCompanyIds.includes(storedCompanyId)) {
      // Use stored company if user still has access to it
      companyToSelect = storedCompanyId;
    } else if (currentCompanyId && availableCompanyIds.includes(currentCompanyId)) {
      // Fall back to auth context's current company
      companyToSelect = currentCompanyId;
    } else if (availableCompanyIds.length > 0) {
      // Fall back to first available company
      companyToSelect = availableCompanyIds[0];
    }

    setSelectedCompanyIdState(companyToSelect);
  }, [isAuthenticated, currentCompanyId, companyIds?.join(','), companies]);

  // Update selected company object when selectedCompanyId or companies change
  useEffect(() => {
    if (selectedCompanyId && companies.length > 0) {
      const company = companies.find((c) => c.id === selectedCompanyId);
      setSelectedCompany(company || null);
    } else {
      setSelectedCompany(null);
    }
  }, [selectedCompanyId, companies]);

  // Handle company selection changes
  const setSelectedCompanyId = (companyId: string | null) => {
    // Validate that user has access to this company
    if (companyId) {
      const hasAccess = (companyIds && companyIds.includes(companyId)) || companies.some((c) => c.id === companyId);
      if (!hasAccess) {
        console.error('User does not have access to company:', companyId);
        return;
      }
    }

    setSelectedCompanyIdState(companyId);

    // Persist selection
    if (companyId) {
      localStorage.setItem(SELECTED_COMPANY_KEY, companyId);
    } else {
      localStorage.removeItem(SELECTED_COMPANY_KEY);
    }

    // Invalidate all company-scoped queries when switching companies
    // This ensures fresh data is fetched for the newly selected company
    queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
    queryClient.invalidateQueries({ queryKey: ['account-ledger'] });
    queryClient.invalidateQueries({ queryKey: ['trial-balance'] });
    queryClient.invalidateQueries({ queryKey: ['balance-sheet'] });
    queryClient.invalidateQueries({ queryKey: ['income-statement'] });
    queryClient.invalidateQueries({ queryKey: ['cash-flow-statement'] });
    queryClient.invalidateQueries({ queryKey: ['account-balances'] });
    queryClient.invalidateQueries({ queryKey: ['company-accounts'] });
  };

  const value: CompanyContextType = {
    selectedCompanyId,
    selectedCompany,
    companies,
    isLoadingCompanies,
    isInitialized,
    setSelectedCompanyId,
    refreshCompanies: fetchCompanies,
  };

  return <CompanyContext.Provider value={value}>{children}</CompanyContext.Provider>;
};

export const useCompany = () => {
  const context = useContext(CompanyContext);
  if (context === undefined) {
    throw new Error('useCompany must be used within a CompanyProvider');
  }
  return context;
};
