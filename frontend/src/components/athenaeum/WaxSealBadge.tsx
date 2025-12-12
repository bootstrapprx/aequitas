/**
 * WaxSealBadge - Classical wax seal badge component
 *
 * Displays status or approval states with a wax seal aesthetic
 * Includes animation when state changes
 */

import { motion } from 'framer-motion';
import { Check, X, AlertCircle, Lock, Unlock } from 'lucide-react';
import { cn } from '@/lib/utils';

type SealType = 'approved' | 'rejected' | 'pending' | 'locked' | 'unlocked';

interface WaxSealBadgeProps {
  type: SealType;
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
}

const sealConfig = {
  approved: {
    color: 'hsl(120 60% 40%)',
    icon: Check,
    label: 'Approved',
  },
  rejected: {
    color: 'hsl(0 65% 50%)',
    icon: X,
    label: 'Rejected',
  },
  pending: {
    color: 'hsl(38 72% 52%)',
    icon: AlertCircle,
    label: 'Pending',
  },
  locked: {
    color: 'hsl(0 75% 35%)',
    icon: Lock,
    label: 'Locked',
  },
  unlocked: {
    color: 'hsl(120 60% 40%)',
    icon: Unlock,
    label: 'Unlocked',
  },
};

const sizeConfig = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
};

const iconSizeConfig = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export const WaxSealBadge = ({
  type,
  size = 'md',
  animate = true,
}: WaxSealBadgeProps) => {
  const config = sealConfig[type];
  const Icon = config.icon;

  const Wrapper = animate ? motion.div : 'div';

  return (
    <Wrapper
      {...(animate && {
        initial: { scale: 0, rotate: -180 },
        animate: { scale: 1, rotate: 0 },
        transition: {
          type: 'spring',
          stiffness: 260,
          damping: 20,
        },
        className: 'animate-wax-seal',
      })}
      className={cn(
        'wax-seal flex items-center justify-center',
        sizeConfig[size]
      )}
      style={{
        background: `radial-gradient(circle at 30% 30%, ${config.color}, ${config.color}dd)`,
      }}
      title={config.label}
    >
      <Icon
        className={cn(
          'text-white drop-shadow-lg',
          iconSizeConfig[size]
        )}
        strokeWidth={3}
      />
    </Wrapper>
  );
};
