import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);
      toast({
        title: 'Access Granted',
        description: 'Welcome to the Athenaeum.',
        className: 'bg-background border-gold text-gold font-heading',
      });
      navigate('/dashboard');
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

