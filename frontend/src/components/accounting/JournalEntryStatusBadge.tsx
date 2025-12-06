import { Badge } from '@/components/ui/badge';
import type { EntryStatus } from '@/types/accounting';

interface JournalEntryStatusBadgeProps {
  status: EntryStatus;
  className?: string;
}

export function JournalEntryStatusBadge({ status, className }: JournalEntryStatusBadgeProps) {
  const variants: Record<EntryStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    draft: {
      label: 'Draft',
      variant: 'secondary',
    },
    posted: {
      label: 'Posted',
      variant: 'default',
    },
    void: {
      label: 'Void',
      variant: 'destructive',
    },
  };

  const { label, variant } = variants[status];

  return (
    <Badge variant={variant} className={className}>
      {label}
    </Badge>
  );
}
