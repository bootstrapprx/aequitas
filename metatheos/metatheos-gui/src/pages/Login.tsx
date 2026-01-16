import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Lock } from 'lucide-react';

export default function Login() {
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        // TODO: Implement actual auth logic (invoke Rust backend)
        console.log("Attempting login...");

        setTimeout(() => {
            // Mock success for now
            setIsLoading(false);
            navigate('/dashboard');
        }, 1000);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/50">
            <Card className="w-full max-w-md shadow-lg">
                <CardHeader className="space-y-1">
                    <div className="flex justify-center mb-4">
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                            <Lock className="h-6 w-6 text-primary" />
                        </div>
                    </div>
                    <CardTitle className="text-2xl font-bold text-center">Metatheos Admin</CardTitle>
                    <CardDescription className="text-center">
                        Enter your secure access credentials
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-2">
                            <Input
                                type="password"
                                placeholder="Access Token / Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isLoading}
                                className="text-center tracking-widest"
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={isLoading || !password}
                        >
                            {isLoading ? "Authenticating..." : "Access System"}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center">
                    <p className="text-xs text-muted-foreground text-center max-w-[18rem]">
                        Restricted System. Unauthorized access is monitored and logged.
                        <br />
                        Metatheos v2.0
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
