/**
 * QuillIcon - Animated quill icon for writing operations
 *
 * Displays an animated quill that plays when content is being written
 * Perfect for journal entries, ledger updates, and data entry
 */

import { motion } from 'framer-motion';
import { Feather } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuillIconProps {
  isWriting?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeConfig = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export const QuillIcon = ({
  isWriting = false,
  size = 'md',
  className,
}: QuillIconProps) => {
  return (
    <motion.div
      className={cn('inline-block', className)}
      animate={
        isWriting
          ? {
              x: [0, 2, -2, 2, 0],
              y: [0, -1, 1, -1, 0],
              rotate: [0, 2, -2, 2, 0],
            }
          : {}
      }
      transition={{
        duration: 0.5,
        repeat: isWriting ? Infinity : 0,
        repeatType: 'loop',
      }}
    >
      <Feather
        className={cn(
          sizeConfig[size],
          isWriting
            ? 'text-primary animate-pulse-glow'
            : 'text-muted-foreground'
        )}
      />
    </motion.div>
  );
};

interface QuillWritingEffectProps {
  text: string;
  delay?: number;
  className?: string;
}

/**
 * QuillWritingEffect - Text that appears with a writing animation
 */
export const QuillWritingEffect = ({
  text,
  delay = 0,
  className,
}: QuillWritingEffectProps) => {
  return (
    <motion.span
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.8,
        delay,
        ease: 'easeOut',
      }}
      className={cn('animate-quill-write', className)}
    >
      {text}
    </motion.span>
  );
};
