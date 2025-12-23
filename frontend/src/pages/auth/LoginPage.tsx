import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';
import api from '@/integrations/api';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(true);
  const [recoveryMode, setRecoveryMode] = useState(false);
  const [recoveryEndpoint, setRecoveryEndpoint] = useState('/auth/recovery-login');
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const fetchAuthConfig = async () => {
      try {
        const response = await api.get('/auth/config');
        const data = response.data;
        setGoogleEnabled(data.google_oauth_enabled !== false);
        setRecoveryMode(Boolean(data.auth_recovery_mode));
        if (data.recovery_endpoint) {
          setRecoveryEndpoint(data.recovery_endpoint);
        }
      } catch (error) {
        console.warn('Auth config unavailable, defaulting to local login only', error);
        setGoogleEnabled(false);
        setRecoveryMode(false);
      }
    };

    fetchAuthConfig();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);

      // Check user context to determine routing (matches OAuth flow)
      const contextResponse = await api.get('/invitations/context');
      const { requires_setup, pending_invitations, has_company } = contextResponse.data;

      toast({
        title: 'Access Granted',
        description: 'Welcome to the Athenaeum.',
        className: 'bg-background border-gold text-gold font-heading',
      });

      // Route based on user context
      if (requires_setup) {
        // User has no companies - redirect to setup (will show invitations if any)
        if (pending_invitations > 0) {
          toast({
            title: 'Invitations Pending',
            description: `You have ${pending_invitations} invitation${pending_invitations > 1 ? 's' : ''} waiting.`,
            className: 'bg-background border-gold text-gold font-heading',
          });
        }
        navigate('/auth/setup');
      } else {
        // User has companies - check if onboarding is complete for preferred company
        try {
          // We need the user from the login response or context (which is async updating)
          // But contextResponse.data doesn't give us company ID.
          // Let's rely on AuthContext user if updated, or fetch /auth/me again?
          // Actually, we can assume the first company or preferred one.

          // Let's try to fetch user details to get preferred company
          const userRes = await api.get('/auth/me');
          const user = userRes.data;
          const companyId = user.preferred_company_id || (user.company_ids && user.company_ids[0]);

          if (companyId) {
            // Check onboarding status
            try {
              const statusRes = await api.get(`/onboarding/status/${companyId}`);
              if (statusRes.data.onboarding_status !== 'ACTIVE') {
                toast({
                  title: 'Resuming Onboarding',
                  description: 'Continuing form where you left off...',
                  className: 'bg-background border-gold text-gold font-heading',
                });
                navigate(`/onboarding/${companyId}`);
                return;
              }
            } catch (ignore) {
              // If status check fails, fall back to dashboard and let OnboardingGuard handle it
            }
          }
        } catch (e) {
          console.error("Failed to check onboarding status", e);
        }

        // Proceed to dashboard if active or check failed
        navigate('/dashboard');
      }
    } catch (error: any) {
      toast({
        title: 'Access Denied',
        description: error.message || 'The gates remain closed. check your credentials.',
        variant: 'destructive',
        className: 'font-heading',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/, '');

  const redirectToOAuthProvider = async (provider: 'google' | 'microsoft' | 'apple') => {
    if (provider === 'google' && !googleEnabled) {
      toast({
        title: 'Google login disabled',
        description: 'Use the email/password form or recovery login.',
        variant: 'destructive',
        className: 'font-heading',
      });
      return;
    }

    setIsLoading(true);
    try {
      // Fetch the authorization URL from the backend
      const response = await api.get(`/auth/oauth/${provider}/start`);
      const { authorization_url } = response.data;

      if (authorization_url) {
        // Redirect to the provider's consent screen
        window.location.href = authorization_url;
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (error: any) {
      console.error('OAuth start failed:', error);
      toast({
        title: 'Authentication Failed',
        description: error.response?.data?.detail || 'Failed to initiate login. Please try again.',
        variant: 'destructive',
        className: 'font-heading',
      });
      setIsLoading(false);
    }
  };

  const handleRecoveryLogin = async () => {
    if (!email || !password) {
      toast({
        title: 'Enter credentials',
        description: 'Set AUTH_RECOVERY credentials and enter them above.',
        variant: 'destructive',
        className: 'font-heading',
      });
      return;
    }

    setIsLoading(true);
    try {
      await api.post(recoveryEndpoint, { email, password, recovery: true });
      toast({
        title: 'Recovery session granted',
        description: 'Fallback login successful. Continuing to setup…',
        className: 'bg-background border-gold text-gold font-heading',
      });

      await login(email, password);

      const contextResponse = await api.get('/invitations/context');
      const { requires_setup } = contextResponse.data;
      navigate(requires_setup ? '/auth/setup' : '/dashboard');
    } catch (error: any) {
      toast({
        title: 'Recovery failed',
        description: error.message || 'Check AUTH_RECOVERY credentials.',
        variant: 'destructive',
        className: 'font-heading',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 marble-texture opacity-50" />
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-background to-transparent z-10" />
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-background to-transparent z-10" />

      {/* Main Card */}
      <Card className="w-full max-w-md relative z-20 border-0 bg-card/95 backdrop-blur-sm stone-border shadow-card animate-fade-up">
        <CardHeader className="space-y-4 text-center pb-8 border-b border-sidebar-border">
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-emerald flex items-center justify-center shadow-glow mb-2 animate-float">
            <span className="text-4xl">⚖️</span>
          </div>
          <CardTitle className="text-4xl font-heading font-bold text-gradient-gold tracking-wide text-engraved">
            Aequitas
          </CardTitle>
          <CardDescription className="font-heading italic text-muted-foreground text-lg">
            "The Digital Athenaeum of Finance"
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2 group">
              <Label htmlFor="email" className="font-heading text-gold flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-gold/50 group-focus-within:bg-gold transition-colors" />
                Identifier
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="scribe@aequitas.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                className="bg-input/30 border-input/50 focus:border-gold/50 focus:ring-gold/20 font-body transition-all duration-300 h-11"
              />
            </div>
            <div className="space-y-2 group">
              <Label htmlFor="password" className="font-heading text-gold flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-gold/50 group-focus-within:bg-gold transition-colors" />
                Secret Key
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                className="bg-input/30 border-input/50 focus:border-gold/50 focus:ring-gold/20 font-body transition-all duration-300 h-11 tracking-widest"
              />
            </div>
            <Button
              type="submit"
              className="w-full h-12 bg-gradient-emerald hover:brightness-110 text-white font-heading font-bold tracking-wider text-lg shadow-glow transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Unsealing...
                </>
              ) : (
                'Enter the Gateway'
              )}
            </Button>

            {/* OAuth Divider */}
            <div className="relative py-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-sidebar-border"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground font-heading tracking-wider">Or continue with</span>
              </div>
            </div>

            {/* Google OAuth Button */}
            {googleEnabled && (
              <Button
                type="button"
                variant="outline"
                className="w-full h-12 border-sidebar-border hover:border-gold/50 hover:bg-card/50 font-heading font-medium tracking-wide transition-all duration-300 flex items-center justify-center gap-3"
                onClick={() => redirectToOAuthProvider('google')}
                disabled={isLoading}
              >
                <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </Button>
            )}

            {/* Microsoft OAuth Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full h-12 border-sidebar-border hover:border-gold/50 hover:bg-card/50 font-heading font-medium tracking-wide transition-all duration-300 flex items-center justify-center gap-3"
              onClick={() => redirectToOAuthProvider('microsoft')}
              disabled={isLoading}
            >
              <svg className="h-5 w-5 shrink-0" viewBox="0 0 23 23">
                <path fill="#f35325" d="M0 0h11v11H0z" />
                <path fill="#81bc06" d="M12 0h11v11H12z" />
                <path fill="#05a6f0" d="M0 12h11v11H0z" />
                <path fill="#ffba08" d="M12 12h11v11H12z" />
              </svg>
              Continue with Microsoft
            </Button>

            {/* Apple Sign-In Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full h-12 border-sidebar-border hover:border-gold/50 hover:bg-card/50 font-heading font-medium tracking-wide transition-all duration-300 flex items-center justify-center gap-3"
              onClick={() => redirectToOAuthProvider('apple')}
              disabled={isLoading}
            >
              <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
              </svg>
              Continue with Apple
            </Button>

            {recoveryMode && (
              <div className="space-y-3 border border-sidebar-border rounded-lg p-4 text-sm text-muted-foreground font-body">
                <p className="font-heading text-gold text-base">Emergency Recovery</p>
                <p>
                  Set <code>AUTH_RECOVERY_MODE=true</code>, <code>RECOVERY_ADMIN_EMAIL</code>, and{' '}
                  <code>RECOVERY_ADMIN_PASSWORD</code>, then enter those credentials above. When ready, use the
                  recovery login button.
                </p>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full border-gold/60 text-gold hover:bg-card/70"
                  onClick={handleRecoveryLogin}
                  disabled={isLoading}
                >
                  Use Recovery Login
                </Button>
              </div>
            )}

            <div className="text-center text-sm text-muted-foreground pt-4 font-body">
              New to the order?{' '}
              <Link to="/register" className="text-gold hover:text-gold-light hover:underline font-medium transition-colors">
                Initiate Rite
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Decorative Footer */}
      <div className="absolute bottom-8 text-center w-full z-20 opacity-30 text-xs font-heading tracking-[0.3em] pointer-events-none">
        MMXXIV • VERITAS ET AEQUITAS
      </div>
    </div>
  );
};

export default LoginPage;
