import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, RefreshCw } from 'lucide-react';
import { useManualCRUD } from '@/hooks/useManualCRUD';
import { useManualMode } from '@/contexts/ManualModeContext';
import { Company, CompanyCreate, CompanyUpdate } from '@/types/company';
import { QueryKey } from '@/lib/queryKeys';
import CompaniesList from '@/components/manual/companies/CompaniesList';
import CompanyDetails from '@/components/manual/companies/CompanyDetails';
import EditCompanyModal from '@/components/manual/companies/EditCompanyModal';
import InactivateCompanyModal from '@/components/manual/companies/InactivateCompanyModal';
import CompanyMergePreview from '@/components/integrations/companies/CompanyMergePreview';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from '@/lib/api';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const CompaniesPage: React.FC = () => {
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [viewingCompany, setViewingCompany] = useState<Company | null>(null);
  const [inactivatingCompany, setInactivatingCompany] = useState<Company | null>(null);
  const [activatingCompany, setActivatingCompany] = useState<Company | null>(null);

  const { isManualMode } = useManualMode();
  const queryClient = useQueryClient();

  const {
    data: companies,
    isLoading,
    isError,
    updateItem,
    refetch,
  } = useManualCRUD<Company, CompanyCreate>({
    queryKey: QueryKey.COMPANIES,
    endpoint: '/companies',
    queryParams: { status: 'all' },
  });

  const activeCompanies = companies.filter(c => c.is_active !== false);
  const inactiveCompanies = companies.filter(c => c.is_active === false);

  const handleUpdate = async (data: CompanyUpdate) => {
    if (!editingCompany) return;

    // Sanitize data
    const sanitizedData = Object.fromEntries(
      Object.entries(data).map(([key, value]) => [key, value === "" ? null : value])
    ) as CompanyUpdate;

    try {
      await updateItem({ ...editingCompany, ...sanitizedData });
      toast.success("Company updated successfully");
      setEditingCompany(null);
    } catch (error) {
      console.error("Failed to update company:", error);
      toast.error("Failed to update company");
    }
  };

  const handleInactivate = async (ucid: string, confirmation: string) => {
    try {
      await api.patch(`/companies/${ucid}/inactivate`, { confirmation });
      queryClient.invalidateQueries({ queryKey: [QueryKey.COMPANIES] });
      toast.success("Company inactivated successfully");
      setInactivatingCompany(null);
    } catch (error: any) {
      console.error("Failed to inactivate company:", error);
      toast.error(error.response?.data?.detail || "Failed to inactivate company");
      throw error; // Re-throw to let modal handle loading state if needed
    }
  };

  const handleActivate = async (ucid: string, confirmation: string) => {
    try {
      await api.patch(`/companies/${ucid}/activate`, { confirmation });
      queryClient.invalidateQueries({ queryKey: [QueryKey.COMPANIES] });
      toast.success("Company activated successfully");
      setActivatingCompany(null);
    } catch (error: any) {
      console.error("Failed to activate company:", error);
      toast.error(error.response?.data?.detail || "Failed to activate company");
      throw error;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Companies</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            title="Sync Data"
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button asChild>
            <Link to="/companies/register">
              <Plus className="mr-2 h-4 w-4" />
              Register Company
            </Link>
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <Tabs defaultValue="active" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="active">Active ({activeCompanies.length})</TabsTrigger>
            <TabsTrigger value="inactive">Inactive ({inactiveCompanies.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="active" className="mt-4">
            <CompaniesList
              companies={activeCompanies}
              onEdit={setEditingCompany}
              onView={setViewingCompany}
              onInactivate={setInactivatingCompany}
              onActivate={setActivatingCompany}
              isLoading={isLoading}
              isError={isError}
              title="Active Companies"
            />
          </TabsContent>
          <TabsContent value="inactive" className="mt-4">
            <CompaniesList
              companies={inactiveCompanies}
              onEdit={() => { }} // Cannot edit inactive
              onView={setViewingCompany}
              onInactivate={() => { }} // Cannot inactivate inactive
              onActivate={setActivatingCompany}
              isLoading={isLoading}
              isError={isError}
              title="Inactive Companies"
            />
          </TabsContent>
        </Tabs>
      </div>

      <EditCompanyModal
        company={editingCompany}
        open={!!editingCompany}
        onOpenChange={(open) => !open && setEditingCompany(null)}
        onSubmit={handleUpdate}
      />

      <InactivateCompanyModal
        company={inactivatingCompany}
        open={!!inactivatingCompany}
        onOpenChange={(open) => !open && setInactivatingCompany(null)}
        onConfirm={handleInactivate}
      />

      <InactivateCompanyModal
        company={activatingCompany}
        open={!!activatingCompany}
        onOpenChange={(open) => !open && setActivatingCompany(null)}
        onConfirm={handleActivate}
        isActivating={true}
      />

      <CompanyDetails
        company={viewingCompany}
        open={!!viewingCompany}
        onOpenChange={(open) => !open && setViewingCompany(null)}
      />

      {!isManualMode && (
        <CompanyMergePreview companies={activeCompanies} />
      )}
    </div>
  );
};

export default CompaniesPage;
