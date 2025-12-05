import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  Plus,
  Search,
  Filter,
  UserPlus,
  UserX,
  Edit,
  Trash2,
  MoreVertical,
  Shield,
  Building2,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  useAllUsersQuery,
  useCompanyUsersQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeactivateUserMutation,
  useDeleteUserMutation,
  useReactivateUserMutation,
} from '@/hooks/api/usersManagement';
import {
  UserListItem,
  UserDetail,
  UserCreateRequest,
  UserUpdateRequest,
  CompanyRoleAssignment,
} from '@/types/user';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

// Placeholder for companies - replace with actual query
const useCompaniesQuery = () => {
  // TODO: Import actual companies query hook
  return { data: [], isLoading: false };
};

const UsersListPage = () => {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const { toast } = useToast();

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompanyId, setFilterCompanyId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null);
  const [deleteUserId, setDeleteUserId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<{
    email: string;
    password: string;
    company_ids: string[];
    company_roles: CompanyRoleAssignment[];
    is_active: boolean;
  }>({
    email: '',
    password: '',
    company_ids: [],
    company_roles: [],
    is_active: true,
  });

  // Permission check
  const isSuperuser = currentUser?.is_superuser || false;
  const isCompanyAdmin = false; // TODO: Check if user is admin of any company

  useEffect(() => {
    if (!isSuperuser && !isCompanyAdmin) {
      toast({
        title: 'Access Denied',
        description: 'You must be a superuser or company admin to access this page.',
        variant: 'destructive',
      });
      navigate('/dashboard');
    }
  }, [isSuperuser, isCompanyAdmin, navigate, toast]);

  // Queries
  const { data: users, isLoading } = useAllUsersQuery({
    search: searchQuery || undefined,
    company_id: filterCompanyId || undefined,
    is_active: filterStatus === 'all' ? undefined : filterStatus === 'active',
  });

  const { data: companies } = useCompaniesQuery();

  // Mutations
  const createMutation = useCreateUserMutation();
  const updateMutation = useUpdateUserMutation();
  const deactivateMutation = useDeactivateUserMutation();
  const deleteMutation = useDeleteUserMutation();
  const reactivateMutation = useReactivateUserMutation();

  // Handlers
  const handleCreateUser = async () => {
    if (!formData.email || formData.company_ids.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'Email and at least one company are required.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const result = await createMutation.mutateAsync({
        email: formData.email,
        password: formData.password || undefined,
        company_ids: formData.company_ids,
        company_roles: formData.company_roles.length > 0 ? formData.company_roles : undefined,
        is_active: formData.is_active,
      });

      toast({
        title: 'User Created',
        description: result.temporary_password
          ? `User created with temporary password: ${result.temporary_password}`
          : 'User created successfully.',
      });

      setIsCreateDialogOpen(false);
      resetForm();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create user.',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;

    try {
      await updateMutation.mutateAsync({
        userId: selectedUser.id,
        data: {
          email: formData.email !== selectedUser.email ? formData.email : undefined,
          company_ids: formData.company_ids,
          company_roles: formData.company_roles.length > 0 ? formData.company_roles : undefined,
          is_active: formData.is_active,
        },
      });

      toast({
        title: 'User Updated',
        description: 'User information updated successfully.',
      });

      setIsEditDialogOpen(false);
      setSelectedUser(null);
      resetForm();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update user.',
        variant: 'destructive',
      });
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    try {
      await deactivateMutation.mutateAsync({ userId });
      toast({
        title: 'User Deactivated',
        description: 'User has been deactivated successfully.',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to deactivate user.',
        variant: 'destructive',
      });
    }
  };

  const handleReactivateUser = async (userId: string) => {
    try {
      await reactivateMutation.mutateAsync(userId);
      toast({
        title: 'User Reactivated',
        description: 'User has been reactivated successfully.',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to reactivate user.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteUserId) return;

    try {
      await deleteMutation.mutateAsync(deleteUserId);
      toast({
        title: 'User Deleted',
        description: 'User has been permanently deleted.',
      });
      setDeleteUserId(null);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete user.',
        variant: 'destructive',
      });
    }
  };

  const openEditDialog = (user: UserListItem) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      password: '',
      company_ids: user.companies.map((c) => c.id),
      company_roles: user.companies.map((c) => ({
        company_id: c.id,
        is_admin: c.is_admin,
        can_edit: true,
        can_view: true,
      })),
      is_active: user.is_active,
    });
    setIsEditDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      company_ids: [],
      company_roles: [],
      is_active: true,
    });
  };

  const toggleCompanySelection = (companyId: string) => {
    setFormData((prev) => {
      const isSelected = prev.company_ids.includes(companyId);
      if (isSelected) {
        return {
          ...prev,
          company_ids: prev.company_ids.filter((id) => id !== companyId),
          company_roles: prev.company_roles.filter((r) => r.company_id !== companyId),
        };
      } else {
        return {
          ...prev,
          company_ids: [...prev.company_ids, companyId],
          company_roles: [
            ...prev.company_roles,
            {
              company_id: companyId,
              is_admin: false,
              can_edit: true,
              can_view: true,
            },
          ],
        };
      }
    });
  };

  const toggleCompanyAdmin = (companyId: string) => {
    setFormData((prev) => ({
      ...prev,
      company_roles: prev.company_roles.map((role) =>
        role.company_id === companyId ? { ...role, is_admin: !role.is_admin } : role
      ),
    }));
  };

  if (!isSuperuser && !isCompanyAdmin) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-4 mb-2">
              <Users className="h-8 w-8 text-green-600 dark:text-green-400" />
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                Users Management
              </h1>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Manage system users, roles, and permissions
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <UserPlus className="mr-2 h-4 w-4" />
            Create User
          </Button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Search & Filter</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search by email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                  <SelectItem value="active">Active Only</SelectItem>
                  <SelectItem value="inactive">Inactive Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Users Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <CardDescription>
              {users?.length || 0} user{users?.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>UID</TableHead>
                    <TableHead>Companies</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users?.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.email}</TableCell>
                      <TableCell>
                        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                          {user.user_uid.slice(0, 8)}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.companies.map((company) => (
                            <Badge
                              key={company.id}
                              variant={company.is_admin ? 'default' : 'secondary'}
                              className="text-xs"
                            >
                              {company.is_admin && <Shield className="h-3 w-3 mr-1" />}
                              {company.name}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.is_superuser ? (
                          <Badge variant="destructive">
                            <Shield className="h-3 w-3 mr-1" />
                            Superuser
                          </Badge>
                        ) : user.companies.some((c) => c.is_admin) ? (
                          <Badge variant="default">Admin</Badge>
                        ) : (
                          <Badge variant="outline">User</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="outline" className="text-green-600">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-red-600">
                            <XCircle className="h-3 w-3 mr-1" />
                            Inactive
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => openEditDialog(user)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            {user.is_active ? (
                              <DropdownMenuItem
                                onClick={() => handleDeactivateUser(user.id)}
                                className="text-orange-600"
                              >
                                <UserX className="mr-2 h-4 w-4" />
                                Deactivate
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => handleReactivateUser(user.id)}
                                className="text-green-600"
                              >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Reactivate
                              </DropdownMenuItem>
                            )}
                            {isSuperuser && (
                              <DropdownMenuItem
                                onClick={() => setDeleteUserId(user.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete Permanently
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create User Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Create a new user and assign them to companies
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="user@example.com"
              />
            </div>
            <div>
              <Label htmlFor="password">Password (optional)</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Leave empty to generate temporary password"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
            <div>
              <Label>Companies (select at least one)</Label>
              <div className="mt-2 space-y-2 border rounded-md p-4 max-h-60 overflow-y-auto">
                {companies?.length === 0 ? (
                  <p className="text-sm text-gray-500">No companies available</p>
                ) : (
                  companies?.map((company: any) => (
                    <div key={company.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={company.id}
                        checked={formData.company_ids.includes(company.id)}
                        onCheckedChange={() => toggleCompanySelection(company.id)}
                      />
                      <Label htmlFor={company.id} className="flex-1 cursor-pointer">
                        {company.name}
                      </Label>
                      {formData.company_ids.includes(company.id) && (
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id={`admin-${company.id}`}
                            checked={
                              formData.company_roles.find((r) => r.company_id === company.id)
                                ?.is_admin || false
                            }
                            onCheckedChange={() => toggleCompanyAdmin(company.id)}
                          />
                          <Label htmlFor={`admin-${company.id}`} className="text-sm cursor-pointer">
                            Admin
                          </Label>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateUser} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>Update user information and company assignments</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="edit-is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="edit-is_active">Active</Label>
            </div>
            <div>
              <Label>Companies</Label>
              <div className="mt-2 space-y-2 border rounded-md p-4 max-h-60 overflow-y-auto">
                {companies?.map((company: any) => (
                  <div key={company.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={`edit-${company.id}`}
                      checked={formData.company_ids.includes(company.id)}
                      onCheckedChange={() => toggleCompanySelection(company.id)}
                    />
                    <Label htmlFor={`edit-${company.id}`} className="flex-1 cursor-pointer">
                      {company.name}
                    </Label>
                    {formData.company_ids.includes(company.id) && (
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`edit-admin-${company.id}`}
                          checked={
                            formData.company_roles.find((r) => r.company_id === company.id)
                              ?.is_admin || false
                          }
                          onCheckedChange={() => toggleCompanyAdmin(company.id)}
                        />
                        <Label htmlFor={`edit-admin-${company.id}`} className="text-sm cursor-pointer">
                          Admin
                        </Label>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateUser} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Updating...' : 'Update User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteUserId} onOpenChange={() => setDeleteUserId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the user and all
              associated data. Consider deactivating instead.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} className="bg-red-600 hover:bg-red-700">
              Delete Permanently
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default UsersListPage;
