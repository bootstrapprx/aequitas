import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, Trash2, Share2, Building2 } from 'lucide-react';
import { toast } from 'sonner';

import { groupsApi } from '@/lib/api/groups';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import AddCompanyToGroupDialog from '@/components/groups/AddCompanyToGroupDialog';
import SUCreateCompanyDialog from '@/components/groups/SUCreateCompanyDialog';
import PropagateMappingsDialog from '@/components/groups/PropagateMappingsDialog';
import { useAuth } from '@/contexts/AuthContext';

const GroupDetail: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [isAddingCompany, setIsAddingCompany] = useState(false);
  const [isCreatingCompany, setIsCreatingCompany] = useState(false);
  const [isPropagating, setIsPropagating] = useState(false);

  const { data: group, isLoading } = useQuery({
    queryKey: ['groups', groupId],
    queryFn: () => groupsApi.getGroup(groupId!),
    enabled: !!groupId,
  });

  const removeMutation = useMutation({
    mutationFn: ({ companyId }: { companyId: string }) =>
      groupsApi.removeCompanyFromGroup(groupId!, companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups', groupId] });
      toast.success('Company removed from group');
    },
    onError: (error: any) => {
      toast.error(error?.details?.detail || 'Failed to remove company');
    },
  });

  const handleRemoveCompany = (companyId: string, companyName: string) => {
    if (confirm(`Remove ${companyName} from this group?`)) {
      removeMutation.mutate({ companyId });
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <p>Loading group...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="container mx-auto py-8">
        <p>Group not found</p>
      </div>
    );
  }

  const isSuperuser = user?.is_superuser === true;

  return (
    <div className="container mx-auto py-8">
      <Button
        variant="ghost"
        onClick={() => navigate('/groups')}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Groups
      </Button>

      <div className="mb-6">
        <h1 className="text-3xl font-bold">{group.name}</h1>
        {group.description && (
          <p className="text-muted-foreground mt-2">{group.description}</p>
        )}
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Member Companies</CardTitle>
                <CardDescription>
                  Companies that are part of this group
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsAddingCompany(true)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Company
                </Button>
                {isSuperuser && (
                  <Button
                    variant="outline"
                    onClick={() => setIsCreatingCompany(true)}
                  >
                    <Building2 className="mr-2 h-4 w-4" />
                    Create Company (SU)
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {group.companies && group.companies.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company Name</TableHead>
                    <TableHead>UCID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {group.companies.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell className="font-medium">{company.name}</TableCell>
                      <TableCell>{company.ucid}</TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                            company.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {company.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveCompany(company.id, company.name)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No companies in this group yet
              </div>
            )}
          </CardContent>
        </Card>

        {group.companies && group.companies.length > 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Mapping Propagation</CardTitle>
              <CardDescription>
                Copy account mappings from one company to others in this group
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setIsPropagating(true)}>
                <Share2 className="mr-2 h-4 w-4" />
                Propagate Mappings
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {groupId && (
        <>
          <AddCompanyToGroupDialog
            groupId={groupId}
            open={isAddingCompany}
            onClose={() => setIsAddingCompany(false)}
          />
          <SUCreateCompanyDialog
            groupId={groupId}
            open={isCreatingCompany}
            onClose={() => setIsCreatingCompany(false)}
          />
          <PropagateMappingsDialog
            groupId={groupId}
            companies={group.companies || []}
            open={isPropagating}
            onClose={() => setIsPropagating(false)}
          />
        </>
      )}
    </div>
  );
};

export default GroupDetail;
