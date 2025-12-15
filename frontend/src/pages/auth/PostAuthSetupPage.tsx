import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Building2 } from 'lucide-react';
import { api } from '@/lib/api';

/**
 * PostAuthSetup - Onboarding flow for OAuth users with no companies
 *
 * Flow:
 * 1. User authenticated via OAuth
 * 2. Check if user has companies
 * 3. If no companies, show this setup page
 * 4. Collect company name
 * 5. Create company and link user
 * 6. Redirect to dashboard
 */
const PostAuthSetupPage = () => {
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!companyName.trim()) {
      toast({
        title: 'Company Name Required',
        description: 'Please enter your company name to continue.',
        variant: 'destructive',
        className: 'font-heading',
      });
      return;
    }

    setIsLoading(true);

    try {
      // Create company
      const response = await api.post('/companies', {
        name: companyName.trim(),
      });

      toast({
        title: 'Chamber Established',
        description: `${companyName} has been registered in the Athenaeum.`,
        className: 'bg-background border-gold text-gold font-heading',
      });

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Company creation error:', error);
      toast({
        title: 'Setup Failed',
        description: error.message || 'Failed to create company. Please try again.',
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
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-heading font-bold text-gradient-gold tracking-wide text-engraved">
            Establish Your Chamber
          </CardTitle>
          <CardDescription className="font-heading italic text-muted-foreground text-base">
            Register your organization in the Digital Athenaeum
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2 group">
              <Label htmlFor="companyName" className="font-heading text-gold flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-gold/50 group-focus-within:bg-gold transition-colors" />
                Organization Name
              </Label>
              <Input
                id="companyName"
                type="text"
                placeholder="Acme Corporation"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                disabled={isLoading}
                className="bg-input/30 border-input/50 focus:border-gold/50 focus:ring-gold/20 font-body transition-all duration-300 h-11"
                autoFocus
              />
              <p className="text-xs text-muted-foreground font-body mt-2">
                This will be your primary organization. You can create more later.
              </p>
            </div>

            <Button
              type="submit"
              className="w-full h-12 bg-gradient-emerald hover:brightness-110 text-white font-heading font-bold tracking-wider text-lg shadow-glow transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Establishing...
                </>
              ) : (
                'Complete Setup'
              )}
            </Button>

            <div className="bg-muted/30 rounded-lg p-4 border border-sidebar-border">
              <p className="text-xs font-body text-muted-foreground text-center leading-relaxed">
                By completing setup, you'll gain access to the full Aequitas platform including
                ChartForge, journal entries, financial reports, and more.
              </p>
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

export default PostAuthSetupPage;
