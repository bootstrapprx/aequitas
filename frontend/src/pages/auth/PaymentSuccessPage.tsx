import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { CheckCircle2, Loader2, AlertCircle, ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';

const PaymentSuccessPage = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { toast } = useToast();
    const { refreshAuth } = useAuth();

    const [status, setStatus] = useState<'confirming' | 'success' | 'error'>('confirming');
    const [error, setError] = useState<string | null>(null);

    const token = searchParams.get('token');
    const isMock = searchParams.get('mock') === 'true';

    useEffect(() => {
        const confirmRegistration = async () => {
            if (!token) {
                setStatus('error');
                setError('Missing registration token');
                return;
            }

            try {
                // Confirm the registration
                const response = await api.post('/auth/register/confirm', { token });

                if (response.data.access_token) {
                    // Store the token
                    localStorage.setItem('token', response.data.access_token);

                    // Refresh auth context
                    await refreshAuth();

                    setStatus('success');

                    toast({
                        title: 'Welcome to Aequitas!',
                        description: 'Your account has been created successfully.',
                    });

                    // Redirect to dashboard after a short delay
                    setTimeout(() => {
                        navigate('/dashboard');
                    }, 2000);
                }
            } catch (err: any) {
                setStatus('error');
                const message = err.response?.data?.detail || 'Failed to confirm registration';
                setError(message);
            }
        };

        confirmRegistration();
    }, [token, navigate, toast, refreshAuth]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    {status === 'confirming' && (
                        <>
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            </div>
                            <CardTitle className="text-2xl">Confirming Payment</CardTitle>
                            <CardDescription>
                                Please wait while we set up your account...
                            </CardDescription>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
                                <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
                            </div>
                            <CardTitle className="text-2xl">Payment Successful!</CardTitle>
                            <CardDescription>
                                Your account has been created. Redirecting to dashboard...
                            </CardDescription>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                                <AlertCircle className="h-8 w-8 text-destructive" />
                            </div>
                            <CardTitle className="text-2xl">Something Went Wrong</CardTitle>
                            <CardDescription>
                                We couldn't complete your registration.
                            </CardDescription>
                        </>
                    )}
                </CardHeader>

                <CardContent className="space-y-4">
                    {status === 'success' && (
                        <div className="space-y-2">
                            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Redirecting to dashboard...
                            </div>
                            <Button className="w-full" onClick={() => navigate('/dashboard')}>
                                Go to Dashboard
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </div>
                    )}

                    {status === 'error' && (
                        <>
                            <Alert variant="destructive">
                                <AlertCircle className="h-4 w-4" />
                                <AlertTitle>Error</AlertTitle>
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                            <div className="flex flex-col gap-2">
                                <Button asChild variant="outline">
                                    <Link to="/register">Try Again</Link>
                                </Button>
                                <Button asChild variant="ghost">
                                    <Link to="/login">Go to Login</Link>
                                </Button>
                            </div>
                        </>
                    )}

                    {isMock && status === 'confirming' && (
                        <Alert>
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                                Development mode: Simulating payment confirmation...
                            </AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default PaymentSuccessPage;
