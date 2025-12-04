import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/integrations/api';
import { User, UserCreate } from '@/types/user';
import { Company } from '@/types/company';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';

interface UserFormProps {
  onSubmit: (data: UserCreate | Partial<User>) => void;
  initialData?: User | null;
  onCancel: () => void;
  isSubmitting: boolean;
}

const UserForm: React.FC<UserFormProps> = ({
  onSubmit,
  initialData,
  onCancel,
  isSubmitting,
}) => {
  const { user: currentUser } = useAuth();
  const [mode, setMode] = useState<'create' | 'join'>('join');
  const [email, setEmail] = useState(initialData?.email || '');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<string[]>([]);

  const { data: companies, isLoading: loadingCompanies } = useQuery<Company[]>({
    queryKey: ['companies'],
    queryFn: async () => {
      const response = await api.get('/companies/');
      return response.data;
    },
  });

  useEffect(() => {
    if (initialData) {
      setEmail(initialData.email);
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (initialData) {
      // Update existing user
      onSubmit({ email });
    } else {
      // Create new user
      if (mode === 'create') {
        // Create company + user
        onSubmit({
          email,
          password,
          is_initial_signup: true,
          company_name: companyName,
        } as UserCreate);
      } else {
        // Add user to existing companies
        onSubmit({
          email,
          password,
          company_ids: selectedCompanyIds,
        } as UserCreate);
      }
    }
  };

  const toggleCompany = (companyId: string) => {
    setSelectedCompanyIds((prev) =>
      prev.includes(companyId)
        ? prev.filter((id) => id !== companyId)
        : [...prev, companyId]
    );
  };

  const isSuperuser = currentUser?.is_superuser || false;

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {initialData ? 'Edit User' : 'Create New User'}
        </CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isSubmitting}
            />
          </div>

          {!initialData && (
            <>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={isSubmitting}
                />
                <p className="text-xs text-muted-foreground">
                  Must be at least 8 characters
                </p>
              </div>

              {isSuperuser && (
                <Tabs value={mode} onValueChange={(v) => setMode(v as 'create' | 'join')}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="join">Add to Existing Company</TabsTrigger>
                    <TabsTrigger value="create">Create New Company</TabsTrigger>
                  </TabsList>

                  <TabsContent value="join" className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Assign to Companies</Label>
                      {loadingCompanies ? (
                        <p className="text-sm text-muted-foreground">Loading companies...</p>
                      ) : (
                        <div className="space-y-2 max-h-48 overflow-y-auto border rounded p-3">
                          {companies && companies.length > 0 ? (
                            companies.map((company) => (
                              <div key={company.id} className="flex items-center space-x-2">
                                <Checkbox
                                  id={`company-${company.id}`}
                                  checked={selectedCompanyIds.includes(company.id)}
                                  onCheckedChange={() => toggleCompany(company.id)}
                                />
                                <label
                                  htmlFor={`company-${company.id}`}
                                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex-1"
                                >
                                  {company.name} ({company.ucid})
                                </label>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-muted-foreground">No companies available</p>
                          )}
                        </div>
                      )}
                      {selectedCompanyIds.length === 0 && (
                        <p className="text-xs text-destructive">
                          Please select at least one company
                        </p>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="create" className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label htmlFor="companyName">Company Name</Label>
                      <Input
                        id="companyName"
                        type="text"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        required={mode === 'create'}
                        disabled={isSubmitting}
                        placeholder="Acme Inc."
                      />
                      <p className="text-xs text-muted-foreground">
                        A unique company ID (UCID) will be generated automatically
                      </p>
                    </div>
                  </TabsContent>
                </Tabs>
              )}

              {!isSuperuser && (
                <div className="space-y-2">
                  <Label>Assign to Companies</Label>
                  {loadingCompanies ? (
                    <p className="text-sm text-muted-foreground">Loading companies...</p>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto border rounded p-3">
                      {companies && companies.length > 0 ? (
                        companies.map((company) => (
                          <div key={company.id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`company-${company.id}`}
                              checked={selectedCompanyIds.includes(company.id)}
                              onCheckedChange={() => toggleCompany(company.id)}
                            />
                            <label
                              htmlFor={`company-${company.id}`}
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex-1"
                            >
                              {company.name} ({company.ucid})
                            </label>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          You don't have admin access to any companies
                        </p>
                      )}
                    </div>
                  )}
                  {selectedCompanyIds.length === 0 && (
                    <p className="text-xs text-destructive">
                      Please select at least one company
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={
              isSubmitting ||
              (!initialData &&
                mode === 'join' &&
                selectedCompanyIds.length === 0) ||
              (!initialData && mode === 'create' && !companyName.trim())
            }
          >
            {isSubmitting ? 'Saving...' : initialData ? 'Update User' : 'Create User'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default UserForm;
