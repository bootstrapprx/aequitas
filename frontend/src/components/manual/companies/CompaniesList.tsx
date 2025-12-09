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
  if (isLoading) return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <Card key={i} className="animate-pulse h-[200px]">
          <CardHeader className="space-y-2">
            <div className="h-4 bg-muted rounded w-3/4"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </CardHeader>
          <CardContent>
            <div className="h-24 bg-muted rounded"></div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  if (isError) return (
    <div className="flex flex-col items-center justify-center p-8 text-center border rounded-lg bg-destructive/10 text-destructive">
      <h3 className="text-lg font-semibold mb-2">Error loading companies</h3>
      <p>Please try refreshing the page.</p>
    </div>
  );

  return (
    <div className="space-y-4">
      {companies.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {companies.map((company) => {
            const isActive = company.is_active !== false;
            return (
              <Card
                key={company.id}
                className={`transition-all hover:shadow-md ${!isActive ? 'opacity-75 bg-muted/30 border-dashed' : ''}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-lg font-bold leading-none truncate cursor-pointer hover:underline" onClick={() => isActive && onEdit(company)}>
                          {company.name}
                        </CardTitle>
                        {!isActive && (
                          <Badge variant="secondary" className="text-[10px] px-1 h-5">Inactive</Badge>
                        )}
                      </div>
                      {company.ucid && (
                        <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground">
                          {company.ucid}
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-start gap-1 -mr-2 -mt-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onView(company)}
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
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
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <span className="sr-only">Edit</span>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-pencil"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" /></svg>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onInactivate(company)}
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
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
                          className="h-8 w-8 text-muted-foreground hover:text-green-600"
                          title="Activate"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2.5 text-sm text-muted-foreground">
                    {company.industry ? (
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 opacity-70" />
                        <span className="truncate">{company.industry}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-muted-foreground/50">
                        <Building2 className="h-4 w-4 opacity-70" />
                        <span>No industry set</span>
                      </div>
                    )}

                    {company.email ? (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 opacity-70" />
                        <span className="truncate" title={company.email}>{company.email}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-muted-foreground/50">
                        <Mail className="h-4 w-4 opacity-70" />
                        <span>No email</span>
                      </div>
                    )}

                    {company.phone ? (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 opacity-70" />
                        <span className="truncate">{company.phone}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-muted-foreground/50">
                        <Phone className="h-4 w-4 opacity-70" />
                        <span>No phone</span>
                      </div>
                    )}

                    {(company.city || company.state || company.country) ? (
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 opacity-70" />
                        <span className="truncate">
                          {[company.city, company.state, company.country].filter(Boolean).join(', ')}
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-muted-foreground/50">
                        <MapPin className="h-4 w-4 opacity-70" />
                        <span>No location</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <CompanyUsers companyId={company.id} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed rounded-xl bg-muted/20">
          <Building2 className="h-10 w-10 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold">{title === "Inactive Companies" ? "No inactive companies" : "No companies yet"}</h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-sm">
            {title === "Inactive Companies"
              ? "Companies that have been deactivated will appear here."
              : "Get started by registering your first company."}
          </p>
        </div>
      )}
    </div>
  );
};

export default CompaniesList;
