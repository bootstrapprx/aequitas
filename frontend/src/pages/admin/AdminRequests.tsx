import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

interface ElevationRequest {
    id: string;
    user_id: string;
    requested_role: string;
    reason: string;
    status: string;
    created_at: string;
}

const AdminRequests = () => {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [rejectId, setRejectId] = useState<string | null>(null);
    const [rejectReason, setRejectReason] = useState("");

    const { data: requests, isLoading } = useQuery({
        queryKey: ["elevationRequests"],
        queryFn: () => api.get<ElevationRequest[]>("/elevation/pending"),
    });

    const reviewMutation = useMutation({
        mutationFn: (data: { id: string; status: "APPROVED" | "REJECTED"; rejection_reason?: string }) =>
            api.post(`/elevation/${data.id}/review`, { status: data.status, rejection_reason: data.rejection_reason }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["elevationRequests"] });
            toast({ title: "Request Reviewed", description: "The request has been processed." });
            setRejectId(null);
            setRejectReason("");
        },
        onError: (error: any) => {
            toast({ title: "Error", description: error.response?.data?.detail || "Failed to review request.", variant: "destructive" });
        },
    });

    const handleApprove = (id: string) => {
        reviewMutation.mutate({ id, status: "APPROVED" });
    };

    const handleReject = () => {
        if (rejectId) {
            reviewMutation.mutate({ id: rejectId, status: "REJECTED", rejection_reason: rejectReason });
        }
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Elevation Requests</h1>
                    <p className="text-muted-foreground mt-1">Review and approve user role elevation requests</p>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Pending Requests</CardTitle>
                    <CardDescription>Users requesting higher privileges.</CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-4">Loading...</div>
                    ) : requests && requests.length > 0 ? (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>User ID</TableHead>
                                    <TableHead>Requested Role</TableHead>
                                    <TableHead>Reason</TableHead>
                                    <TableHead>Date</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {requests.map((req) => (
                                    <TableRow key={req.id}>
                                        <TableCell className="font-mono text-xs">{req.user_id}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{req.requested_role}</Badge>
                                        </TableCell>
                                        <TableCell className="max-w-md truncate" title={req.reason}>{req.reason}</TableCell>
                                        <TableCell>{format(new Date(req.created_at), "MMM d, yyyy")}</TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Button size="sm" variant="default" onClick={() => handleApprove(req.id)} disabled={reviewMutation.isPending}>
                                                <Check className="h-4 w-4 mr-1" /> Approve
                                            </Button>
                                            <Button size="sm" variant="destructive" onClick={() => setRejectId(req.id)} disabled={reviewMutation.isPending}>
                                                <X className="h-4 w-4 mr-1" /> Reject
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">No pending requests found.</div>
                    )}
                </CardContent>
            </Card>

            <Dialog open={!!rejectId} onOpenChange={(open) => !open && setRejectId(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Reject Request</DialogTitle>
                        <DialogDescription>Please provide a reason for rejection.</DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <Textarea
                            placeholder="Rejection reason..."
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                        />
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setRejectId(null)}>Cancel</Button>
                        <Button variant="destructive" onClick={handleReject} disabled={reviewMutation.isPending}>
                            Confirm Rejection
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default AdminRequests;
