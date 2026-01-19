import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Building2, Mail, UserPlus, CheckCircle, XCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { useCompany } from '@/contexts/CompanyContext';

interface Invitation {
  id: string;
  email: string;
  target_type: 'company' | 'group';
  target_id: string;
  target_name: string;
  role: string;
  is_admin: boolean;
  inviter_email: string | null;
  expires_at: string;
  created_at: string;
}

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
 *
 * TODO (Phase 2):
 * - Check for pending invitations (GET /api/v1/users/invitations)
 * - If invitations exist, show "Accept Invitation" option instead of creating new company
 * - Resolve invite email matching OAuth email
 * - Support both "Create Company" and "Join via Invitation" flows
 */
const PostAuthSetupPage = () => {
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingInvitations, setIsFetchingInvitations] = useState(true);
  const [pendingInvitations, setPendingInvitations] = useState<Invitation[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { refreshCompanies, setSelectedCompanyId } = useCompany();

  useEffect(() => {
    checkInvitations();
  }, []);

  const checkInvitations = async () => {
    try {
      const data = await api.get<{ invitations: Invitation[] }>('/invitations/pending');

      setPendingInvitations(data.invitations || []);
      setIsFetchingInvitations(false);

      // If no invitations, show create form immediately
      if (!data.invitations || data.invitations.length === 0) {
        setShowCreateForm(true);
      }
    } catch (error: any) {
      console.error('Failed to fetch invitations:', error);
      // On error, show create form
      setShowCreateForm(true);
      setIsFetchingInvitations(false);
    }
  };

  const handleAcceptInvitation = async (invitationId: string) => {
    setIsLoading(true);

    try {
      await api.post(`/invitations/${invitationId}/accept`, {});

      toast({
        title: 'Invitation Accepted',
        description: 'You have been added to the company.',
        className: 'bg-background border-gold text-gold font-heading',
      });

      await refreshCompanies();

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Invitation acceptance error:', error);
      toast({
        title: 'Acceptance Failed',
        description: error.response?.data?.detail || 'Failed to accept invitation.',
        variant: 'destructive',
        className: 'font-heading',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeclineInvitation = async (invitationId: string) => {
    try {
      await api.post(`/invitations/${invitationId}/decline`, {});

      toast({
        title: 'Invitation Declined',
        description: 'The invitation has been declined.',
        className: 'font-heading',
      });

      // Remove from list
      setPendingInvitations((prev) => prev.filter((inv) => inv.id !== invitationId));

      // If no more invitations, show create form
      if (pendingInvitations.length === 1) {
        setShowCreateForm(true);
      }
    } catch (error: any) {
      console.error('Invitation decline error:', error);
      toast({
        title: 'Decline Failed',
        description: 'Failed to decline invitation.',
        variant: 'destructive',
        className: 'font-heading',
      });
    }
  };

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
      const response = await api.post<{ id: string; name: string }>('/companies', {
        name: companyName.trim(),
      });

      toast({
        title: 'Chamber Established',
        description: `${companyName} has been registered in the Athenaeum.`,
        className: 'bg-background border-gold text-gold font-heading',
      });

      await refreshCompanies();
      setSelectedCompanyId(response.id);

      // Redirect to onboarding wizard
      navigate(`/onboarding/${response.id}`);
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

  if (isFetchingInvitations) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 text-gold animate-spin mx-auto" />
          <p className="text-muted-foreground font-body">Checking for invitations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 marble-texture opacity-50" />
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-background to-transparent z-10" />
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-background to-transparent z-10" />

      {/* Main Card */}
      <Card className="w-full max-w-2xl relative z-20 border-0 bg-card/95 backdrop-blur-sm stone-border shadow-card animate-fade-up">
        <CardHeader className="space-y-4 text-center pb-8 border-b border-sidebar-border">
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-emerald flex items-center justify-center shadow-glow mb-2 animate-float">
            {pendingInvitations.length > 0 ? (
              <Mail className="h-8 w-8 text-white" />
            ) : (
              <Building2 className="h-8 w-8 text-white" />
            )}
          </div>
          <CardTitle className="text-3xl font-heading font-bold text-gradient-gold tracking-wide text-engraved">
            {pendingInvitations.length > 0 ? 'You Have Invitations' : 'Establish Your Chamber'}
          </CardTitle>
          <CardDescription className="font-heading italic text-muted-foreground text-base">
            {pendingInvitations.length > 0
              ? 'Accept an invitation or create your own organization'
              : 'Register your organization in the Digital Athenaeum'}
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-8">
          {pendingInvitations.length > 0 && !showCreateForm && (
            <div className="space-y-4">
              <h3 className="font-heading text-lg font-semibold text-gold mb-4">Pending Invitations</h3>

              {pendingInvitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="border border-sidebar-border rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-heading font-semibold text-foreground text-lg">
                        {invitation.target_name}
                      </h4>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-muted-foreground font-body">
                          <span className="text-gold">Role:</span> {invitation.is_admin ? 'Admin' : invitation.role}
                        </p>
                        {invitation.inviter_email && (
                          <p className="text-sm text-muted-foreground font-body">
                            <span className="text-gold">Invited by:</span> {invitation.inviter_email}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground font-body">
                          Expires: {new Date(invitation.expires_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button
                        onClick={() => handleAcceptInvitation(invitation.id)}
                        disabled={isLoading}
                        className="bg-gradient-emerald hover:brightness-110 text-white font-heading shadow-glow"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Accept
                      </Button>
                      <Button
                        onClick={() => handleDeclineInvitation(invitation.id)}
                        disabled={isLoading}
                        variant="outline"
                        className="border-sidebar-border font-heading"
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        Decline
                      </Button>
                    </div>
                  </div>
                </div>
              ))}

              <div className="pt-4 border-t border-sidebar-border mt-6">
                <Button
                  onClick={() => setShowCreateForm(true)}
                  variant="outline"
                  className="w-full border-sidebar-border hover:border-gold/50 font-heading"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Or Create Your Own Company
                </Button>
              </div>
            </div>
          )}

          {(showCreateForm || pendingInvitations.length === 0) && (
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

              {pendingInvitations.length > 0 && showCreateForm && (
                <div className="pt-4 border-t border-sidebar-border">
                  <Button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    variant="outline"
                    className="w-full border-sidebar-border font-heading"
                  >
                    Back to Invitations
                  </Button>
                </div>
              )}
            </form>
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

export default PostAuthSetupPage;
