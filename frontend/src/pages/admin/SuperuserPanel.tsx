import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Users, Settings, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import {
  useGetAllUsers,
  usePromoteUser,
  useDemoteUser,
  useGetSettings,
  useUpdateSettings,
} from '@/integrations/queries/useAdmin';
import type { User } from '@/types/user';

const SuperuserPanel: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [showSettings, setShowSettings] = useState(false);

  // Check if current user is superuser
  const isSuperuser = currentUser?.is_superuser || false;

  // Fetch data
  const { data: users, isLoading: usersLoading } = useGetAllUsers();
  const { data: settings, isLoading: settingsLoading } = useGetSettings();

  // Mutations
  const promoteMutation = usePromoteUser();
  const demoteMutation = useDemoteUser();
  const updateSettingsMutation = useUpdateSettings();

  const handlePromote = (userId: string) => {
    if (window.confirm('Are you sure you want to promote this user to superuser?')) {
      promoteMutation.mutate(userId);
    }
  };

  const handleDemote = (userId: string) => {
    if (userId === currentUser?.id) {
      alert('You cannot demote yourself!');
      return;
    }
    if (window.confirm('Are you sure you want to demote this user from superuser?')) {
      demoteMutation.mutate(userId);
    }
  };

  const handleToggleMaintenanceMode = () => {
    if (settings) {
      updateSettingsMutation.mutate({
        maintenance_mode: !settings.maintenance_mode,
      });
    }
  };

  const handleTogglePublicSignup = () => {
    if (settings) {
      updateSettingsMutation.mutate({
        allow_public_signup: !settings.allow_public_signup,
      });
    }
  };

  if (!isSuperuser) {
    return (
      <div className="p-10">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-6 w-6 text-red-600" />
              <span>Access Denied</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              You need superuser privileges to access this panel.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center space-x-4 mb-2">
          <Shield className="h-8 w-8 text-purple-600 dark:text-purple-400" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Superuser Panel
          </h1>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Manage user permissions and system-wide settings
        </p>
      </motion.div>

      {/* User Management Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>User Management</span>
            </CardTitle>
            <CardDescription>
              Promote or demote users to/from superuser status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usersLoading ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users && users.length > 0 ? (
                      users.map((user: User) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">
                            {user.email}
                            {user.id === currentUser?.id && (
                              <Badge variant="outline" className="ml-2">
                                You
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {user.is_superuser ? (
                              <Badge className="bg-purple-600">Superuser</Badge>
                            ) : (
                              <Badge variant="secondary">Regular User</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(user.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-right">
                            {user.is_superuser ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDemote(user.id)}
                                disabled={
                                  demoteMutation.isPending ||
                                  user.id === currentUser?.id
                                }
                              >
                                {demoteMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  'Demote'
                                )}
                              </Button>
                            ) : (
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => handlePromote(user.id)}
                                disabled={promoteMutation.isPending}
                              >
                                {promoteMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  'Promote'
                                )}
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted-foreground">
                          No users found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* System Settings Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
      >
        <Card>
          <CardHeader className="cursor-pointer" onClick={() => setShowSettings(!showSettings)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <CardTitle>System Settings</CardTitle>
              </div>
              {showSettings ? (
                <ChevronUp className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              )}
            </div>
            <CardDescription>
              Configure global application settings
            </CardDescription>
          </CardHeader>
          {showSettings && (
            <CardContent className="space-y-6">
              {settingsLoading ? (
                <div className="flex justify-center items-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : (
                <>
                  {/* Maintenance Mode */}
                  <div className="flex items-center justify-between space-x-4 p-4 rounded-lg border">
                    <div className="flex-1">
                      <Label htmlFor="maintenance-mode" className="text-base font-semibold">
                        Maintenance Mode
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        When enabled, the application will be unavailable to regular users
                      </p>
                    </div>
                    <Switch
                      id="maintenance-mode"
                      checked={settings?.maintenance_mode || false}
                      onCheckedChange={handleToggleMaintenanceMode}
                      disabled={updateSettingsMutation.isPending}
                    />
                  </div>

                  {/* Public Signup */}
                  <div className="flex items-center justify-between space-x-4 p-4 rounded-lg border">
                    <div className="flex-1">
                      <Label htmlFor="public-signup" className="text-base font-semibold">
                        Allow Public Signup
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        When enabled, anyone can register for a new account
                      </p>
                    </div>
                    <Switch
                      id="public-signup"
                      checked={settings?.allow_public_signup || false}
                      onCheckedChange={handleTogglePublicSignup}
                      disabled={updateSettingsMutation.isPending}
                    />
                  </div>

                  {/* Settings Info */}
                  {settings && (
                    <div className="pt-4 border-t text-xs text-muted-foreground">
                      Last updated: {new Date(settings.updated_at).toLocaleString()}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          )}
        </Card>
      </motion.div>
    </div>
  );
};

export default SuperuserPanel;
