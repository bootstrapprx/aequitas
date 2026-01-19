import { Building, ChevronDown, AlertCircle } from 'lucide-react';
import { useCompany } from '@/contexts/CompanyContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

interface CompanySelectorProps {
  className?: string;
  showLabel?: boolean;
}

const CompanySelector = ({ className = '', showLabel = true }: CompanySelectorProps) => {
  const {
    selectedCompanyId,
    selectedCompany,
    companies,
    isLoadingCompanies,
    setSelectedCompanyId,
  } = useCompany();

  if (isLoadingCompanies) {
    return (
      <div className={className}>
        {showLabel && <div className="text-xs font-heading text-muted-foreground uppercase tracking-widest mb-2">Company</div>}
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className={className}>
        {showLabel && <div className="text-xs font-heading text-muted-foreground uppercase tracking-widest mb-2">Company</div>}
        <Alert variant="destructive" className="py-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            No companies available. Please contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={className}>
      {showLabel && (
        <div className="text-xs font-heading text-muted-foreground uppercase tracking-widest mb-2">
          Active Company
        </div>
      )}
      <Select
        value={selectedCompanyId || undefined}
        onValueChange={(value) => setSelectedCompanyId(value)}
      >
        <SelectTrigger className="bg-background/50 border-gold/20 hover:border-gold/40 hover:bg-gold/5 transition-all duration-300 group">
          <div className="flex items-center gap-2">
            <Building className="h-4 w-4 text-gold group-hover:text-gold-light transition-colors" />
            <SelectValue placeholder="Select a company">
              {selectedCompany ? (
                <div className="flex items-center gap-2">
                  <span className="font-medium">{selectedCompany.name}</span>
                  <span className="text-xs text-muted-foreground font-mono">
                    ({selectedCompany.ucid})
                  </span>
                </div>
              ) : (
                'Select a company'
              )}
            </SelectValue>
          </div>
        </SelectTrigger>
        <SelectContent className="bg-background border-sidebar-border shadow-2xl shadow-black/50">
          {companies.map((company) => (
            <SelectItem
              key={company.id}
              value={company.id}
              className="focus:bg-gold/10 focus:text-gold cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <Building className="h-4 w-4 text-muted-foreground" />
                <div className="flex flex-col">
                  <span className="font-medium">{company.name}</span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {company.ucid}
                  </span>
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default CompanySelector;
