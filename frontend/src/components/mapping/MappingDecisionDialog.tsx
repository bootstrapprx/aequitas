import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

type DecisionMode = 'accept' | 'override' | 'reject';

type Props = {
  open: boolean;
  mode: DecisionMode;
  defaultReason?: string;
  onClose: () => void;
  onSubmit: (params: { reason: string; masterAccountId?: string }) => void;
};

export const MappingDecisionDialog = ({ open, mode, defaultReason = '', onClose, onSubmit }: Props) => {
  const [reason, setReason] = useState(defaultReason);
  const [masterAccountId, setMasterAccountId] = useState('');

  const titleMap: Record<DecisionMode, string> = {
    accept: 'Accept mapping',
    override: 'Override mapping',
    reject: 'Reject mapping',
  };

  const handleSubmit = () => {
    onSubmit({ reason, masterAccountId: masterAccountId || undefined });
    setReason('');
    setMasterAccountId('');
  };

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{titleMap[mode]}</DialogTitle>
        </DialogHeader>
        {mode === 'override' && (
          <div className="space-y-2">
            <Label htmlFor="master-account">Master Account ID</Label>
            <Input
              id="master-account"
              placeholder="Enter master account ID"
              value={masterAccountId}
              onChange={(e) => setMasterAccountId(e.target.value)}
            />
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="reason">Reason</Label>
          <Textarea
            id="reason"
            placeholder="Provide context for this decision"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Submit</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default MappingDecisionDialog;
