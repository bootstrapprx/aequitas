import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { User } from '@/types/user';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, Users, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CompanyUsersProps {
  companyId: string;
}

const CompanyUsers: React.FC<CompanyUsersProps> = ({ companyId }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const { data: users, isLoading, isError } = useQuery({
    queryKey: ['company-users', companyId],
    queryFn: async () => {
      const response = await api.get<User[]>(`/companies/${companyId}/users`);
      return response.data;
    },
    enabled: isExpanded, // Only fetch when expanded
  });

  return (
    <div className="mt-2 pt-2 border-t">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm"
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        <Users className="h-4 w-4" />
        <span>Users {users && `(${users.length})`}</span>
      </Button>

      {isExpanded && (
        <div className="mt-2 ml-6 space-y-2">
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading users...
            </div>
          )}

          {isError && (
            <p className="text-sm text-destructive">Failed to load users</p>
          )}

          {users && users.length === 0 && (
            <p className="text-sm text-muted-foreground">No users assigned to this company</p>
          )}

          {users && users.length > 0 && (
            <ul className="space-y-1">
              {users.map((user) => (
                <li
                  key={user.id}
                  className="flex items-center justify-between p-2 rounded bg-muted/30 text-sm"
                >
                  <div>
                    <span className="font-medium">{user.email}</span>
                    {user.is_superuser && (
                      <Badge variant="secondary" className="ml-2 text-xs">
                        Superuser
                      </Badge>
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs font-mono">
                    {user.user_uid}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default CompanyUsers;
