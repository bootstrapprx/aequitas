// frontend/src/components/masterchart/dashboard/AccountDetailsPanel.tsx
import React from 'react';
import { MasterAccount } from '@/types/masterchart';
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AccountDetailsPanelProps {
    account: MasterAccount | null;
    isOpen: boolean;
    onClose: () => void;
    onAddAccount?: (account: MasterAccount) => void;
    isAdded?: boolean;
    isAdding?: boolean;
    companyName?: string | null;
}

const AccountDetailsPanel: React.FC<AccountDetailsPanelProps> = ({
    account,
    isOpen,
    onClose,
    onAddAccount,
    isAdded = false,
    isAdding = false,
    companyName = null,
}) => {
    if (!account) return null;

    const canAdd = !!onAddAccount && !isAdded && !isAdding && !!companyName;

    return (
        <Sheet open={isOpen} onOpenChange={onClose}>
            <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
                <SheetHeader>
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <SheetTitle className="font-mono text-2xl">{account.code}</SheetTitle>
                            <SheetDescription>{account.description}</SheetDescription>
                        </div>
                        {onAddAccount && (
                            <div className="flex flex-col items-end gap-2">
                                <Button
                                    size="sm"
                                    onClick={() => onAddAccount(account)}
                                    disabled={!canAdd}
                                >
                                    {isAdded ? 'Already in Chart' : isAdding ? 'Adding...' : 'Add to Chart'}
                                </Button>
                                <span className="text-xs text-muted-foreground">
                                    {companyName ? `Adds to ${companyName}` : 'Select a company to add this account.'}
                                </span>
                            </div>
                        )}
                    </div>
                </SheetHeader>

                <Tabs defaultValue="overview" className="mt-6">
                    <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="structure">Structure</TabsTrigger>
                        <TabsTrigger value="history">History</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                        <Card>
                            <CardContent className="pt-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Type</p>
                                        <Badge variant={account.type === 'H' ? 'default' : 'secondary'} className="mt-1">
                                            {account.type === 'H' ? 'Header' : 'Detail'}
                                        </Badge>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Level</p>
                                        <p className="font-semibold mt-1">{account.level}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Category</p>
                                        <p className="font-semibold mt-1">{account.category}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Parent Code</p>
                                        <p className="font-mono font-semibold mt-1">
                                            {account.parent_code || '—'}
                                        </p>
                                    </div>
                                </div>

                                {account.notes && (
                                    <div>
                                        <p className="text-sm text-muted-foreground">Notes</p>
                                        <p className="text-sm mt-2">{account.notes}</p>
                                    </div>
                                )}

                                {account.normal_balance && (
                                    <div>
                                        <p className="text-sm text-muted-foreground">Normal Balance</p>
                                        <p className="font-semibold mt-1">{account.normal_balance}</p>
                                    </div>
                                )}

                                {account.fs_mapping && (
                                    <div>
                                        <p className="text-sm text-muted-foreground">Statement Mapping</p>
                                        <p className="font-semibold mt-1">{account.fs_mapping}</p>
                                    </div>
                                )}

                                {account.start_date && (
                                    <div>
                                        <p className="text-sm text-muted-foreground">Start Date</p>
                                        <p className="font-semibold mt-1">
                                            {new Date(account.start_date).toLocaleDateString()}
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="structure" className="space-y-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Hierarchy Position</p>
                                        <p className="text-sm mt-2">
                                            This account is at level {account.level} in the hierarchy.
                                            {account.parent_code && (
                                                <> This account is a child of <span className="font-mono font-semibold">{account.parent_code}</span>.</>
                                            )}
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="history" className="space-y-4">
                        <Card>
                            <CardContent className="pt-6">
                                <p className="text-sm text-muted-foreground">
                                    Account history and audit trail would be displayed here.
                                </p>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </SheetContent>
        </Sheet>
    );
};

export default AccountDetailsPanel;
