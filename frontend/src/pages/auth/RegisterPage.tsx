import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle } from 'lucide-react';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Registration Disabled</CardTitle>
          <CardDescription>User accounts must be created by administrators</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Public Registration is Disabled</AlertTitle>
            <AlertDescription>
              For security reasons, new user accounts can only be created by:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>System Administrators (SuperUsers)</li>
                <li>Company Administrators</li>
              </ul>
            </AlertDescription>
          </Alert>

          <div className="space-y-2 text-sm text-muted-foreground">
            <p>
              To get access to Aequitas, please contact your company administrator
              or system administrator to create an account for you.
            </p>
            <p>
              If you're setting up Aequitas for the first time, please use the
              default superuser account to create your company and user accounts.
            </p>
          </div>

          <div className="pt-4">
            <Button asChild className="w-full">
              <Link to="/login">
                Go to Login
              </Link>
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Log in here
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RegisterPage;

