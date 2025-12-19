import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useCompany } from '@/contexts/CompanyContext';
import { Loader2 } from 'lucide-react';

interface OnboardingGuardProps {
  children: React.ReactNode;
}

/**
 * OnboardingGuard - Global routing guard for canonical onboarding enforcement
 *
 * CANONICAL RULES:
 * - Dashboard access allowed only if onboarding_status = ACTIVE
 * - Any other state → redirect to /onboarding/:companyId
 * - No companies → redirect to /companies/register
 *
 * This guard runs:
 * - On first login
 * - On refresh
 * - On company switch
 * - On any route navigation within the dashboard
 */
const OnboardingGuard: React.FC<OnboardingGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedCompany, selectedCompanyId, companies, isLoadingCompanies } = useCompany();

  useEffect(() => {
    // Don't redirect while loading companies
    if (isLoadingCompanies) {
      return;
    }

    // Rule 1: If user has no companies → redirect to Company Registration
    if (!companies || companies.length === 0) {
      // Allow the companies and registration pages
      const allowedPaths = ['/companies', '/companies/register'];
      const isAllowedPath = allowedPaths.some(path => location.pathname.startsWith(path));

      if (!isAllowedPath) {
        console.log('[OnboardingGuard] No companies found, redirecting to company registration');
        navigate('/companies/register', { replace: true });
      }
      return;
    }

    // Rule 2: If no company selected, wait for selection
    if (!selectedCompanyId || !selectedCompany) {
      // CompanyContext will handle selection, wait for it
      return;
    }

    // Rule 3: If selected company exists AND onboarding_status ≠ ACTIVE
    //         → redirect to /onboarding/:companyId
    if (selectedCompany.onboarding_status !== 'ACTIVE') {
      const onboardingPath = `/onboarding/${selectedCompanyId}`;

      // Don't redirect if we're already on the onboarding page
      if (!location.pathname.startsWith('/onboarding/')) {
        console.log('[OnboardingGuard] Redirecting to onboarding wizard:', {
          company: selectedCompany.name,
          status: selectedCompany.onboarding_status,
          currentPath: location.pathname,
          redirectTo: onboardingPath
        });
        navigate(onboardingPath, { replace: true });
      }
      return;
    }

    // Rule 4: If onboarding_status = ACTIVE → allow dashboard access
    // (no action needed, render children)

  }, [
    selectedCompany,
    selectedCompanyId,
    companies,
    isLoadingCompanies,
    navigate,
    location.pathname
  ]);

  // Show loading state while determining route
  if (isLoadingCompanies) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading company information...</p>
        </div>
      </div>
    );
  }

  // If we have no companies, show a minimal UI while redirecting
  if (!companies || companies.length === 0) {
    if (location.pathname !== '/companies' && location.pathname !== '/companies/register') {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Redirecting to company registration...</p>
          </div>
        </div>
      );
    }
  }

  // If we have a company but it's not active and we're not on onboarding page
  if (selectedCompany && selectedCompany.onboarding_status !== 'ACTIVE') {
    if (!location.pathname.startsWith('/onboarding/')) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Redirecting to onboarding wizard...</p>
          </div>
        </div>
      );
    }
  }

  // All checks passed or we're on the appropriate page - render children
  return <>{children}</>;
};

export default OnboardingGuard;
