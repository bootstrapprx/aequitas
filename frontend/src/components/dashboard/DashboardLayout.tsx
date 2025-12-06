// frontend/src/components/dashboard/DashboardLayout.tsx
import { Outlet } from "react-router-dom";
import AequitasSidebar from "./AequitasSidebar";
import { ManualModeProvider } from "@/contexts/ManualModeContext";

const DashboardLayout = () => {
  return (
    <ManualModeProvider>
      <div className="flex min-h-screen bg-background">
        <AequitasSidebar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </ManualModeProvider>
  );
};

export default DashboardLayout;
