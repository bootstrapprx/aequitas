// frontend/src/components/masterchart/dashboard/views/CardsView.tsx
import React from 'react';
import { MasterAccount } from '@/types/masterchart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Folder, FileText, Info } from 'lucide-react';
import { motion } from 'framer-motion';

interface CardsViewProps {
    accounts: MasterAccount[];
    onSelectAccount: (account: MasterAccount) => void;
}

const AccountCard: React.FC<{
    account: MasterAccount;
    index: number;
    onSelect: () => void;
}> = ({ account, index, onSelect }) => {
    const isHeader = account.type === 'H';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.02 }}
        >
            <Card className="rounded-2xl shadow-lg shadow-black/10 dark:shadow-black/30 hover:-translate-y-1 transition-transform duration-200 h-full">
                <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                            {isHeader ? (
                                <div className="p-2 rounded-lg bg-primary/10">
                                    <Folder className="h-5 w-5 text-primary" />
                                </div>
                            ) : (
                                <div className="p-2 rounded-lg bg-muted">
                                    <FileText className="h-5 w-5 text-muted-foreground" />
                                </div>
                            )}
                            <div>
                                <CardTitle className="text-lg font-bold font-mono">{account.code}</CardTitle>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    Level {account.level} • {account.category}
                                </p>
                            </div>
                        </div>
                        <Badge variant={isHeader ? 'default' : 'secondary'}>
                            {isHeader ? 'Header' : 'Detail'}
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-3">
                    <p className="text-sm line-clamp-2">{account.description}</p>

                    {account.parent_code && (
                        <div className="text-xs text-muted-foreground">
                            Parent: <span className="font-mono">{account.parent_code}</span>
                        </div>
                    )}

                    <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={onSelect}
                    >
                        <Info className="h-4 w-4 mr-2" />
                        View Details
                    </Button>
                </CardContent>
            </Card>
        </motion.div>
    );
};

const CardsView: React.FC<CardsViewProps> = ({ accounts, onSelectAccount }) => {
    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {accounts.map((account, index) => (
                <AccountCard
                    key={account.id}
                    account={account}
                    index={index}
                    onSelect={() => onSelectAccount(account)}
                />
            ))}
        </div>
    );
};

export default CardsView;
