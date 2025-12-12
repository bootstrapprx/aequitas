/**
 * AtheneumCard - Classical marble-themed card component
 *
 * A premium card component with marble textures and stone borders
 * for the Digital Athenaeum of Finance aesthetic
 */

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface AtheneumCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  ornate?: boolean;
  parchment?: boolean;
  animate?: boolean;
}

export const AtheneumCard = ({
  children,
  className,
  hover = false,
  glow = false,
  ornate = false,
  parchment = false,
  animate = true,
}: AtheneumCardProps) => {
  const Card = animate ? motion.div : 'div';

  return (
    <Card
      {...(animate && {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.5 },
      })}
      className={cn(
        'relative rounded-lg overflow-hidden',
        parchment ? 'parchment' : 'bg-card border border-border',
        'shadow-card',
        hover && 'transition-all duration-300 hover:shadow-glow hover:scale-[1.02]',
        glow && 'shadow-glow',
        ornate && 'ornate-border',
        !parchment && 'marble-texture',
        className
      )}
    >
      {!parchment && (
        <div className="absolute inset-0 pointer-events-none opacity-[0.03] column-pattern mix-blend-multiply" />
      )}
      {children}
    </Card>
  );
};

interface AtheneumCardHeaderProps {
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
  embossed?: boolean;
}

export const AtheneumCardHeader = ({
  children,
  className,
  icon,
  embossed = false,
}: AtheneumCardHeaderProps) => {
  return (
    <div className={cn('p-6 pb-4', className)}>
      <div className="flex items-center gap-3">
        {icon && (
          <div className="text-primary animate-pulse-glow">
            {icon}
          </div>
        )}
        <h3 className={cn(
          'text-2xl font-heading font-bold',
          embossed && 'embossed-gold'
        )}>
          {children}
        </h3>
      </div>
      <div className="manuscript-line" />
    </div>
  );
};

interface AtheneumCardContentProps {
  children: ReactNode;
  className?: string;
}

export const AtheneumCardContent = ({
  children,
  className,
}: AtheneumCardContentProps) => {
  return (
    <div className={cn('p-6 pt-2', className)}>
      {children}
    </div>
  );
};
