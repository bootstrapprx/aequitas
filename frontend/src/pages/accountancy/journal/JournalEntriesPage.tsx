import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const JournalEntriesPage = () => {
  return (
    <div className="p-10 space-y-8">
      <motion.div
        initial={ opacity: 0, y: -20 }
        animate={ opacity: 1, y: 0 }
        transition={ duration: 0.5 }
      >
        <div className="flex items-center space-x-4 mb-2">
          <BookOpen className="h-8 w-8 text-green-600 dark:text-green-400" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Ledger Accounts
          </h1>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          View and manage ledger accounts and transaction history
        </p>
      </motion.div>

      <motion.div
        initial={ opacity: 0, y: 20 }
        animate={ opacity: 1, y: 0 }
        transition={ delay: 0.2, duration: 0.5 }
      >
        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
            <CardDescription>
              This feature is currently under development
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              We're working hard to bring you this functionality. In the meantime, you can:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li>Explore other modules in the sidebar</li>
              <li>Check out the ChartForge module for chart of accounts management</li>
              <li>Review the documentation for more information</li>
            </ul>
            <div className="flex gap-4 pt-4">
              <Button variant="outline">View Documentation</Button>
              <Button variant="outline">Contact Support</Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={ opacity: 0, y: 20 }
        animate={ opacity: 1, y: 0 }
        transition={ delay: 0.4, duration: 0.5 }
      >
        <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <CardHeader>
            <CardTitle className="text-blue-900 dark:text-blue-100">
              Want to be notified when this feature launches?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
              We'll send you an email as soon as Ledger Accounts is available.
            </p>
            <Button className="bg-blue-600 hover:bg-blue-700">
              Notify Me
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default JournalEntriesPage;
