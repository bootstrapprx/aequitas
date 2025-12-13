import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface PasswordResetGuardProps {
  children: ReactNode;
}

/**
 * PasswordResetGuard enforces password reset when required.
 *
 * If the user has force_password_reset = true, they are redirected to the
 * password change page and blocked from accessing other routes until they
 * complete the password reset.
 */
const PasswordResetGuard = ({ children }: PasswordResetGuardProps) => {
  const { forcePasswordReset, isAuthenticated } = useAuth();
  const location = useLocation();

  // Don't interfere if not authenticated
  if (!isAuthenticated) {
    return <>{children}</>;
  }

  // If password reset is required and we're not already on the change password page
  if (forcePasswordReset && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

export default PasswordResetGuard;
