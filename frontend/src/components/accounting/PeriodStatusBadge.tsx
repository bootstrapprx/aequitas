import { Badge } from '@/components/ui/badge';
import type { PeriodStatus } from '@/types/accounting';
import { Lock, LockOpen, CircleDot } from 'lucide-react';

interface PeriodStatusBadgeProps {
  status: PeriodStatus;
  showIcon?: boolean;
  className?: string;
}

export function PeriodStatusBadge({ status, showIcon = true, className }: PeriodStatusBadgeProps) {
  const config: Record<
    PeriodStatus,
    { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }
  > = {
    open: {
      label: 'Open',
      variant: 'default',
      icon: <CircleDot className="h-3 w-3" />,
    },
    closed: {
      label: 'Closed',
      variant: 'secondary',
      icon: <LockOpen className="h-3 w-3" />,
    },
    locked: {
      label: 'Locked',
      variant: 'destructive',
      icon: <Lock className="h-3 w-3" />,
    },
  };

  const { label, variant, icon } = config[status];

  return (
    <Badge variant={variant} className={className}>
      {showIcon && <span className="mr-1">{icon}</span>}
      {label}
    </Badge>
  );
}
