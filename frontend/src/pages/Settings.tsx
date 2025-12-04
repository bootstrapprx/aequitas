import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings as SettingsIcon, User, Bell, Shield, Database, Lock } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import Sidebar from "@/components/dashboard/Sidebar";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";

const SettingsPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [requestRole, setRequestRole] = useState("ACCOUNTANT");
  const [requestReason, setRequestReason] = useState("");
  const [isRequestOpen, setIsRequestOpen] = useState(false);
  const { toast } = useToast();

  const requestMutation = useMutation({
    mutationFn: (data: { requested_role: string; reason: string }) =>
      api.post("/elevation/request", data),
    onSuccess: () => {
      toast({ title: "Request Submitted", description: "Your elevation request has been sent for approval." });
      setIsRequestOpen(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.response?.data?.detail || "Failed to submit request.", variant: "destructive" });
    }
  });

  const handleSubmitRequest = () => {
    requestMutation.mutate({ requested_role: requestRole, reason: requestReason });
  };

  const settingsSections = [
    {
      icon: User,
      title: "Profile Settings",
      description: "Manage your account information and preferences"
    },
    {
      icon: Bell,
      title: "Notifications",
      description: "Configure email and in-app notifications"
    },
    {
      icon: Shield,
      title: "Security",
      description: "Password, 2FA, and security options"
    },
    {
      icon: Database,
      title: "Data Management",
      description: "Import, export, and backup settings"
    },
    {
      icon: Lock,
      title: "Role & Permissions",
      description: "Request role elevation (Accountant, Admin, SU)",
      action: () => setIsRequestOpen(true)
    }
  ];

  return (
    <div className="flex h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Application Settings</h1>
              <p className="text-muted-foreground mt-1">Manage your preferences and configuration</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Theme:</span>
              <ThemeToggle />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {settingsSections.map((section, index) => (
              <Card key={index} className="cursor-pointer hover:shadow-lg transition-shadow" onClick={section.action}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <section.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{section.title}</CardTitle>
                      <CardDescription className="text-sm">{section.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" className="w-full">
                    Configure
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Quick Settings</CardTitle>
              <CardDescription>Configure application settings and preferences here.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <SettingsIcon className="h-20 w-20 mb-4 opacity-50" />
                <p className="text-lg font-medium">Settings configuration coming soon</p>
                <p className="text-sm">Advanced settings will be available here</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={isRequestOpen} onOpenChange={setIsRequestOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Role Elevation</DialogTitle>
            <DialogDescription>
              Submit a request to upgrade your account privileges.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Requested Role</label>
              <Select value={requestRole} onValueChange={setRequestRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACCOUNTANT">Accountant</SelectItem>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                  <SelectItem value="SU">Super User (SU)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason</label>
              <Textarea
                placeholder="Why do you need this role?"
                value={requestReason}
                onChange={(e) => setRequestReason(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRequestOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmitRequest} disabled={requestMutation.isPending}>
              {requestMutation.isPending ? "Submitting..." : "Submit Request"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SettingsPage;