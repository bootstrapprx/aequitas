/**
 * Step 0: Welcome Screen
 *
 * Purpose: Set expectations and reduce fear
 *
 * Content:
 * - Short explanation of wizard
 * - What will happen
 * - What won't happen
 * - Start button
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Scroll, Shield, Check, X } from 'lucide-react';

import { AtheneumCard, AtheneumCardHeader, AtheneumCardContent } from '@/components/athenaeum';
import { Button } from '@/components/ui/button';

interface Step0WelcomeProps {
  onNext: () => void;
  status: any;
}

const Step0Welcome: React.FC<Step0WelcomeProps> = ({ onNext, status }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Main Welcome */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="inline-block mb-4"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-full flex items-center justify-center mx-auto shadow-gold">
            <Scroll className="h-10 w-10 text-white" />
          </div>
        </motion.div>
        <h1 className="text-3xl font-bold text-foreground mb-2 embossed-gold scale-100">
          Welcome to Aequitas
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          We'll guide you through setting up your company's accounting foundation.
          This ensures accuracy, compliance, and future-proof reporting.
        </p>
      </div>

      {/* What Will Happen */}
      <AtheneumCard hover className="border-emerald-200">
        <AtheneumCardHeader icon={<Check className="h-5 w-5 text-emerald-600" />} embossed>
          What You'll Do
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <ul className="space-y-3">
            {[
              'Choose an accounting template that matches your jurisdiction and business type',
              'Review and customize your chart of accounts to fit your needs',
              'Define fiscal periods to organize your financial year',
              'Activate accounting to start recording transactions'
            ].map((item, index) => (
              <motion.li
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="flex items-start space-x-3"
              >
                <Check className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span className="text-foreground/80 dark:text-foreground/90">{item}</span>
              </motion.li>
            ))}
          </ul>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* What Won't Happen */}
      <AtheneumCard hover className="border-amber-200">
        <AtheneumCardHeader icon={<Shield className="h-5 w-5 text-amber-600" />} embossed>
          What You Won't Need to Worry About
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <ul className="space-y-3">
            {[
              'No complex accounting jargon or confusing terminology',
              'No transactions will be recorded during setup',
              'Nothing is irreversible without a clear warning',
              'Your progress is saved automatically—you can exit anytime'
            ].map((item, index) => (
              <motion.li
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="flex items-start space-x-3"
              >
                <X className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span className="text-foreground/80 dark:text-foreground/90">{item}</span>
              </motion.li>
            ))}
          </ul>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Time Estimate */}
      <AtheneumCard className="bg-secondary/50 border-none">
        <AtheneumCardContent>
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground mb-1">Estimated Time</p>
            <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">10–15 minutes</p>
            <p className="text-xs text-muted-foreground mt-1">You can pause and resume at any time</p>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Start Button */}
      <div className="flex justify-center pt-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.9 }}
        >
          <Button
            onClick={onNext}
            size="lg"
            className="px-12 py-6 text-lg shadow-gold hover:shadow-2xl transition-all"
          >
            Start Setup
          </Button>
        </motion.div>
      </div>

      {/* Footer Note */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1 }}
        className="text-center text-xs text-gray-500 pt-6 border-t border-gray-200"
      >
        <p>Need help? Contact support at any time during the setup process.</p>
      </motion.div>
    </motion.div>
  );
};

export default Step0Welcome;
