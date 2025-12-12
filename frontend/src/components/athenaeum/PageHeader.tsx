/**
 * PageHeader - Athenaeum-styled page header
 *
 * A classical page header with marble textures, ornate borders,
 * and golden accents for the Digital Athenaeum of Finance
 */

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';
import { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  actions?: ReactNode;
  className?: string;
}

export const PageHeader = ({
  title,
  subtitle,
  icon: Icon,
  actions,
  className,
}: PageHeaderProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn('mb-8', className)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-2">
            {Icon && (
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                  type: 'spring',
                  stiffness: 200,
                  damping: 15,
                  delay: 0.2,
                }}
              >
                <Icon className="w-10 h-10 text-primary animate-pulse-glow" />
              </motion.div>
            )}
            <h1 className="text-4xl md:text-5xl font-heading font-bold text-foreground embossed-gold">
              {title}
            </h1>
          </div>
          {subtitle && (
            <motion.p
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="text-lg text-muted-foreground ml-14"
            >
              {subtitle}
            </motion.p>
          )}
        </div>

        {actions && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            {actions}
          </motion.div>
        )}
      </div>

      {/* Decorative manuscript line */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay: 0.5, duration: 0.8 }}
        style={{ transformOrigin: 'left' }}
        className="manuscript-line mt-6"
      />
    </motion.div>
  );
};
