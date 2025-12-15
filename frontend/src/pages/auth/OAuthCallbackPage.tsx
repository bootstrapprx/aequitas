import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Loader2, AlertCircle } from 'lucide-react';

const OAuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [providerEmail, setProviderEmail] = useState<string | null>(null);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');

      // Handle OAuth errors (user cancelled, etc.)
      if (errorParam) {
        setError('OAuth authentication was cancelled or failed');
        setIsProcessing(false);
        return;
      }

      if (!code || !state) {
        setError('Invalid OAuth callback - missing parameters');
        setIsProcessing(false);
        return;
      }

      try {
        // Call backend callback endpoint
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/oauth/google/callback`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code, state }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'OAuth callback failed');
        }

        const data = await response.json();

        if (data.status === 'success') {
          // Successful login - store token and redirect
          localStorage.setItem('token', data.access_token);

          toast({
            title: 'Access Granted',
            description: 'Welcome to the Athenaeum.',
            className: 'bg-background border-gold text-gold font-heading',
          });

          // Check if user needs setup
          if (data.requires_setup) {
            navigate('/auth/setup');
          } else {
            navigate('/dashboard');
          }
        } else if (data.status === 'setup_required') {
          // New OAuth user - needs to complete setup
          localStorage.setItem('token', data.access_token);

          toast({
            title: 'Account Created',
            description: 'Please complete your account setup.',
            className: 'bg-background border-gold text-gold font-heading',
          });

          navigate('/auth/setup');
        } else if (data.status === 'link_required') {
          // Email collision - show linking UI
          setLinkToken(data.link_token);
          setProviderEmail(data.provider_email);
          setIsProcessing(false);
        } else {
          throw new Error(`Unknown OAuth status: ${data.status}`);
        }
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'Failed to complete OAuth authentication');
        setIsProcessing(false);
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate, toast]);

  const handleConfirmLink = async () => {
    if (!linkToken) return;

    setIsProcessing(true);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/oauth/link/confirm`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            link_token: linkToken,
            confirm: true,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to link account');
      }

      const data = await response.json();

      // Store token
      localStorage.setItem('token', data.access_token);

      toast({
        title: 'Accounts Linked',
        description: 'Your Google account has been linked successfully.',
        className: 'bg-background border-gold text-gold font-heading',
      });

      navigate('/dashboard');
    } catch (err: any) {
      console.error('Account linking error:', err);
      toast({
        title: 'Linking Failed',
        description: err.message || 'Failed to link accounts',
        variant: 'destructive',
        className: 'font-heading',
      });
      setIsProcessing(false);
    }
  };

  const handleCancelLink = () => {
    navigate('/login');
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
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-emerald flex items-center justify-center shadow-glow mb-2">
            {isProcessing ? (
              <Loader2 className="h-8 w-8 text-white animate-spin" />
            ) : error ? (
              <AlertCircle className="h-8 w-8 text-destructive" />
            ) : (
              <span className="text-4xl">🔗</span>
            )}
          </div>
          <CardTitle className="text-2xl font-heading font-bold text-gradient-gold tracking-wide text-engraved">
            {isProcessing
              ? 'Processing OAuth...'
              : error
              ? 'Authentication Error'
              : 'Link Accounts'}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-8">
          {isProcessing && (
            <div className="text-center space-y-4">
              <p className="text-muted-foreground font-body">
                Verifying your identity with Google...
              </p>
              <div className="flex justify-center">
                <Loader2 className="h-8 w-8 text-gold animate-spin" />
              </div>
            </div>
          )}

          {error && (
            <div className="space-y-4">
              <p className="text-destructive font-body text-center">{error}</p>
              <Button
                onClick={() => navigate('/login')}
                className="w-full bg-gradient-emerald hover:brightness-110 text-white font-heading font-bold shadow-glow"
              >
                Return to Login
              </Button>
            </div>
          )}

          {linkToken && providerEmail && (
            <div className="space-y-6">
              <div className="bg-muted/30 rounded-lg p-4 border border-sidebar-border">
                <p className="text-sm font-body text-muted-foreground mb-2">
                  An account already exists with the email:
                </p>
                <p className="font-heading text-gold font-semibold">{providerEmail}</p>
              </div>

              <p className="text-sm font-body text-muted-foreground text-center">
                Would you like to link your Google account to your existing Aequitas account?
                This will allow you to sign in with either method.
              </p>

              <div className="space-y-3">
                <Button
                  onClick={handleConfirmLink}
                  disabled={isProcessing}
                  className="w-full bg-gradient-emerald hover:brightness-110 text-white font-heading font-bold shadow-glow"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Linking...
                    </>
                  ) : (
                    'Link Accounts'
                  )}
                </Button>

                <Button
                  onClick={handleCancelLink}
                  variant="outline"
                  disabled={isProcessing}
                  className="w-full border-sidebar-border hover:border-gold/50 font-heading"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Decorative Footer */}
      <div className="absolute bottom-8 text-center w-full z-20 opacity-30 text-xs font-heading tracking-[0.3em] pointer-events-none">
        MMXXIV • VERITAS ET AEQUITAS
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
