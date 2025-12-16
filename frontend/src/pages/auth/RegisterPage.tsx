import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle, Loader2, CreditCard, UserPlus, Building2 } from 'lucide-react';
import { api } from '@/lib/api';

interface AuthConfig {
  allow_public_signup: boolean;
  stripe_enabled: boolean;
  stripe_configured: boolean;
  stripe_mock_mode: boolean;
  mock_payments_allowed: boolean;
}

// Default safe config when backend is unavailable
const DEFAULT_AUTH_CONFIG: AuthConfig = {
  allow_public_signup: false,
  stripe_enabled: false,
  stripe_configured: false,
  stripe_mock_mode: false,
  mock_payments_allowed: false,
};

const parseAuthConfig = (data: any): AuthConfig => ({
  allow_public_signup: data?.allow_public_signup ?? false,
  stripe_enabled: data?.stripe_enabled ?? data?.stripe_configured ?? false,
  stripe_configured: data?.stripe_configured ?? data?.stripe_enabled ?? false,
  stripe_mock_mode: data?.stripe_mock_mode ?? data?.mock_payments_allowed ?? false,
  mock_payments_allowed: data?.mock_payments_allowed ?? data?.stripe_mock_mode ?? false,
});

const USER_FIRST_REGISTER_ENDPOINT = '/auth/register/user-first';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { toast } = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [authConfig, setAuthConfig] = useState<AuthConfig>(DEFAULT_AUTH_CONFIG);
  const [configLoading, setConfigLoading] = useState(true);

  useEffect(() => {
    const fetchConfig = async () => {
      setConfigLoading(true);
      try {
        const response = await api.get<any>('/auth/config');
        setAuthConfig(parseAuthConfig(response));
      } catch (err) {
        console.warn('Failed to fetch auth config', err);
        setAuthConfig(DEFAULT_AUTH_CONFIG);
      } finally {
        setConfigLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const validateForm = () => {
    if (!email || !password || !confirmPassword) {
      setError('Email and password are required');
      return false;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return false;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm() || !authConfig.allow_public_signup) {
      return;
    }

    setIsLoading(true);
    try {
      const payload: Record<string, string> = {
        email,
        password,
      };

      if (fullName.trim()) {
        payload.full_name = fullName.trim();
      }

      await api.post(USER_FIRST_REGISTER_ENDPOINT, payload);

      toast({
        title: 'Account created',
        description: "Welcome to Aequitas. Let's finish your setup.",
        className: 'bg-background border-gold text-gold font-heading',
      });

      // Authenticate the new user immediately and continue setup
      await login(email, password);
      navigate('/auth/setup');
    } catch (err: any) {
      const details = err?.details || {};
      const message =
        details?.detail ||
        details?.message ||
        err?.message ||
        'Registration failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (configLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const registrationDisabled = !authConfig.allow_public_signup;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Create your account</CardTitle>
          <CardDescription>
            Enter your details to get started. You'll set up your company after signing in.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertTitle>What happens next?</AlertTitle>
            <AlertDescription>
              This creates your personal Aequitas login. We will guide you through company setup on the next step.
            </AlertDescription>
          </Alert>

          {registrationDisabled && (
            <Alert variant="destructive">
              <AlertTitle>Registration is currently closed</AlertTitle>
              <AlertDescription>
                Public sign ups are disabled. Contact your administrator for an invitation.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading || registrationDisabled}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="full-name">Full name (optional)</Label>
              <Input
                id="full-name"
                type="text"
                placeholder="Ada Lovelace"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={isLoading || registrationDisabled}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading || registrationDisabled}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading || registrationDisabled}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading || registrationDisabled}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Continue'
              )}
            </Button>
          </form>

          <div className="text-center text-sm text-muted-foreground pt-2">
            You'll choose or create a company on the next step.
          </div>

          <div className="text-center text-sm text-muted-foreground pt-4 border-t">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Log in
            </Link>
          </div>

          <div className="text-center text-xs text-muted-foreground">
            Need the legacy company-based flow?{' '}
            <Link to="/register/company" className="text-primary hover:underline font-medium">
              Access it here
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const LegacyCompanyRegisterPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { login } = useAuth();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [plan, setPlan] = useState<'starter' | 'pro'>('starter');

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);
  const [authConfig, setAuthConfig] = useState<AuthConfig>(DEFAULT_AUTH_CONFIG);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('paid');

  // Check if registration was canceled
  const wasCanceled = searchParams.get('canceled') === 'true';

  // Fetch auth config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      setConfigLoading(true);
      try {
        const response = await api.get<any>('/auth/config');
        if (response && typeof response === 'object') {
          const data = parseAuthConfig(response);
          setAuthConfig(data);
          if (data.allow_public_signup) {
            setActiveTab('free');
          }
        } else {
          console.warn('Auth config response invalid, using defaults');
          setAuthConfig(DEFAULT_AUTH_CONFIG);
        }
      } catch (err) {
        console.error('Failed to fetch auth config:', err);
        setAuthConfig(DEFAULT_AUTH_CONFIG);
      } finally {
        setConfigLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const validateForm = (): boolean => {
    if (!email || !password || !companyName) {
      setError('Please fill in all required fields');
      return false;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return false;
    }
    if (companyName.length < 2) {
      setError('Company name must be at least 2 characters');
      return false;
    }
    return true;
  };

  const handleFreeRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const response = await api.post<any>('/auth/register', {
        email,
        password,
        company_name: companyName,
        register_type: 'free',
        plan: 'starter'
      });

      if (response && response.access_token) {
        toast({
          title: 'Registration successful!',
          description: 'Welcome to Aequitas. Redirecting to dashboard...',
        });

        await login(email, password);
        navigate('/dashboard');
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePaidRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const response = await api.post<any>('/auth/register', {
        email,
        password,
        company_name: companyName,
        register_type: 'paid',
        plan
      });

      if (response && response.checkout_url) {
        toast({
          title: 'Redirecting to payment...',
          description: 'You will be redirected to complete your payment.',
        });

        window.location.href = response.checkout_url;
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (configLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription>
            Get started with Aequitas - your complete accounting solution
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {wasCanceled && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Payment Canceled</AlertTitle>
              <AlertDescription>
                Your payment was canceled. You can try again or choose a different plan.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              {authConfig.allow_public_signup && (
                <TabsTrigger value="free" className="flex items-center gap-2">
                  <UserPlus className="h-4 w-4" />
                  Free Account
                </TabsTrigger>
              )}
              <TabsTrigger
                value="paid"
                className={`flex items-center gap-2 ${!authConfig.allow_public_signup ? 'col-span-2' : ''}`}
              >
                <CreditCard className="h-4 w-4" />
                Pay & Register
              </TabsTrigger>
            </TabsList>

            {authConfig.allow_public_signup && (
              <TabsContent value="free">
                <form onSubmit={handleFreeRegister} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="email-free">Email</Label>
                    <Input
                      id="email-free"
                      type="email"
                      placeholder="you@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="company-free">Company Name</Label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="company-free"
                        type="text"
                        placeholder="Acme Inc."
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password-free">Password</Label>
                    <Input
                      id="password-free"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm-password-free">Confirm Password</Label>
                    <Input
                      id="confirm-password-free"
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>

                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating Account...
                      </>
                    ) : (
                      'Create Free Account'
                    )}
                  </Button>
                </form>
              </TabsContent>
            )}

            <TabsContent value="paid">
              <form onSubmit={handlePaidRegister} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="email-paid">Email</Label>
                  <Input
                    id="email-paid"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company-paid">Company Name</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="company-paid"
                      type="text"
                      placeholder="Acme Inc."
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="plan">Select Plan</Label>
                  <Select value={plan} onValueChange={(v) => setPlan(v as 'starter' | 'pro')}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="starter">
                        <div className="flex flex-col">
                          <span className="font-medium">Starter - $49.99</span>
                          <span className="text-sm text-muted-foreground">Perfect for small businesses</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="pro">
                        <div className="flex flex-col">
                          <span className="font-medium">Pro - $99.99</span>
                          <span className="text-sm text-muted-foreground">For growing companies</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password-paid">Password</Label>
                  <Input
                    id="password-paid"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password-paid">Confirm Password</Label>
                  <Input
                    id="confirm-password-paid"
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>

                {authConfig.stripe_mock_mode && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Development mode: Payment will be simulated.
                    </AlertDescription>
                  </Alert>
                )}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <CreditCard className="mr-2 h-4 w-4" />
                      Pay & Register
                    </>
                  )}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="text-center text-sm text-muted-foreground pt-4 border-t">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Log in here
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export { LegacyCompanyRegisterPage };
export default RegisterPage;
