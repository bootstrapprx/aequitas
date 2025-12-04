import React from 'react';
import { Company } from '@/types/company';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Trash2, Mail, Phone, MapPin, Building2, Eye, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import CompanyUsers from './CompanyUsers';

interface CompaniesListProps {
  companies: Company[];
  onEdit: (company: Company) => void;
  onView: (company: Company) => void;
  onInactivate: (company: Company) => void;
  onActivate: (company: Company) => void;
  isLoading: boolean;
  isError: boolean;
  title?: string;
}

const CompaniesList: React.FC<CompaniesListProps> = ({
  companies,
  onEdit,
  onView,
  onInactivate,
  onActivate,
  isLoading,
  isError,
  title = "Existing Companies"
}) => {
  if (isLoading) return <p>Loading companies...</p>;
  if (isError) return <p className="text-destructive">Error loading companies.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {companies.map((company) => {
            const isActive = company.is_active !== false;
            return (
              <li
                key={company.id}
                className={`p-4 border rounded-lg transition-colors ${isActive ? 'hover:bg-muted/50' : 'bg-muted/30 opacity-75'}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 cursor-pointer" onClick={() => isActive && onEdit(company)}>
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className={`font-semibold text-lg ${isActive ? 'hover:underline' : ''}`}>{company.name}</h3>
                      {company.ucid && (
                        <Badge variant="outline" className="font-mono text-xs">
                          {company.ucid}
                        </Badge>
                      )}
                      {!isActive && (
                        <Badge variant="secondary" className="text-xs">Inactive</Badge>
                      )}
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      {company.industry && (
                        <div className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          <span>{company.industry}</span>
                        </div>
                      )}
                      {company.email && (
                        <div className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          <span>{company.email}</span>
                        </div>
                      )}
                      {company.phone && (
                        <div className="flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          <span>{company.phone}</span>
                        </div>
                      )}
                      {(company.city || company.state) && (
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          <span>
                            {[company.city, company.state].filter(Boolean).join(', ')}
                            {company.country && `, ${company.country}`}
                          </span>
                        </div>
                      )}
                      {/* Audit info placeholder - requires backend support in Company model response */}
                      {/* {company.inactivated_at && (
                        <div className="text-xs text-red-500 mt-1">
                          Inactivated on {new Date(company.inactivated_at).toLocaleDateString()}
                        </div>
                      )} */}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onView(company)}
                      title="View Details"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>

                    {isActive ? (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onEdit(company)}
                          title="Edit"
                        >
                          {/* Edit Icon? Using default text or maybe Pencil */}
                          <span className="sr-only">Edit</span>
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-pencil"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" /></svg>
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onInactivate(company)}
                          className="text-destructive hover:text-destructive"
                          title="Inactivate"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onActivate(company)}
                        className="text-green-600 hover:text-green-700"
                        title="Activate"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
                {/* Display users for this company */}
                <CompanyUsers companyId={company.id} />
              </li>
            );
          })}
        </ul>
        {companies.length === 0 && (
          <p className="text-muted-foreground text-center py-8">No companies found.</p>
        )}
      </CardContent>
    </Card>
  );
};

export default CompaniesList;
