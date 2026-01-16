import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useMetatheosAuth } from "@/contexts/MetatheosAuthContext";
import MetatheosSurface from "@/components/metatheos/MetatheosSurface";

const MetatheosProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading } = useMetatheosAuth();

  if (isLoading) {
    return (
      <MetatheosSurface className="metatheos-landing">
        <div className="metatheos-fade-in metatheos-muted">Initializing observatory...</div>
      </MetatheosSurface>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default MetatheosProtectedRoute;
