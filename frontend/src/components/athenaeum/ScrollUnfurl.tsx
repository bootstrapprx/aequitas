/**
 * ScrollUnfurl - Ancient scroll unfurling animation
 *
 * Displays content with a scroll unfurling effect
 * Perfect for reports, financial statements, and important documents
 */

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';
import { Scroll } from 'lucide-react';

interface ScrollUnfurlProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  delay?: number;
}

export const ScrollUnfurl = ({
  children,
  className,
  title,
  subtitle,
  delay = 0,
}: ScrollUnfurlProps) => {
  return (
    <motion.div
      initial={{ scaleY: 0, opacity: 0 }}
      animate={{ scaleY: 1, opacity: 1 }}
      transition={{
        duration: 0.8,
        delay,
        ease: [0.34, 1.56, 0.64, 1],
      }}
      style={{ transformOrigin: 'top' }}
      className={cn(
        'relative overflow-hidden rounded-lg',
        'parchment shadow-card',
        className
      )}
    >
      {/* Scroll Rod Top */}
      <div className="h-3 bg-gradient-to-b from-amber-900 to-amber-800 border-b-2 border-amber-950 shadow-inner" />

      {/* Content */}
      <div className="p-8">
        {(title || subtitle) && (
          <div className="mb-6 text-center">
            {title && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: delay + 0.3, duration: 0.5 }}
                className="flex items-center justify-center gap-3 mb-2"
              >
                <Scroll className="w-6 h-6 text-amber-800" />
                <h2 className="text-3xl font-heading font-bold text-amber-900 embossed-gold">
                  {title}
                </h2>
                <Scroll className="w-6 h-6 text-amber-800" />
              </motion.div>
            )}
            {subtitle && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: delay + 0.5, duration: 0.5 }}
                className="text-sm text-amber-800/70 font-medium"
              >
                {subtitle}
              </motion.p>
            )}
            <div className="manuscript-line mt-4" />
          </div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.6, duration: 0.8 }}
          className="animate-ink-fade"
        >
          {children}
        </motion.div>
      </div>

      {/* Scroll Rod Bottom */}
      <div className="h-3 bg-gradient-to-t from-amber-900 to-amber-800 border-t-2 border-amber-950 shadow-inner" />

      {/* Scrollwork Decoration */}
      <div className="absolute top-0 left-0 right-0 h-16 scrollwork pointer-events-none opacity-30" />
      <div className="absolute bottom-0 left-0 right-0 h-16 scrollwork pointer-events-none opacity-30 transform rotate-180" />
    </motion.div>
  );
};
