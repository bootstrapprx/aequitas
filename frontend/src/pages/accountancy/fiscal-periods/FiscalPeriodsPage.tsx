import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Plus, Lock, Unlock, AlertCircle, Hourglass } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  PageHeader,
  AtheneumCard,
  AtheneumCardHeader,
  AtheneumCardContent,
  WaxSealBadge,
} from '@/components/athenaeum';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  useFiscalPeriods,
  useCreateFiscalPeriod,
  useCloseFiscalPeriod,
  useCreateMonthlyPeriods,
} from '@/hooks/useAccounting';
import { useAuth } from '@/contexts/AuthContext';
import { useCompany } from '@/contexts/CompanyContext';
import type { FiscalPeriod } from '@/types/accounting';

type PeriodType = 'month' | 'quarter' | 'year';
type PeriodStatus = 'open' | 'closed' | 'locked';

const FiscalPeriodsPage = () => {
  const { user } = useAuth();
  const { selectedCompanyId, selectedCompany } = useCompany();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [bulkCreateDialogOpen, setBulkCreateDialogOpen] = useState(false);
  const [filterYear, setFilterYear] = useState<string>('all');

  // Form states
  const [periodNumber, setPeriodNumber] = useState('');
  const [periodType, setPeriodType] = useState<PeriodType>('month');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [bulkYear, setBulkYear] = useState(new Date().getFullYear());

  // Fetch fiscal periods
  const { data: fiscalPeriods = [], isLoading } = useFiscalPeriods(selectedCompanyId || undefined, {
    year: filterYear !== 'all' ? parseInt(filterYear) : undefined,
  });

  // Mutations
  const createMutation = useCreateFiscalPeriod();
  const closeMutation = useCloseFiscalPeriod();
  const bulkCreateMutation = useCreateMonthlyPeriods();

  // Get unique years from periods
  const availableYears = Array.from(
    new Set(fiscalPeriods.map((p: FiscalPeriod) => new Date(p.start_date).getFullYear()))
  ).sort((a, b) => b - a);

  const handleCreate = async () => {
    if (!selectedCompanyId || !periodNumber || !startDate || !endDate) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await createMutation.mutateAsync({
        company_id: selectedCompanyId,
        period_number: periodNumber,
        period_type: periodType,
        start_date: startDate,
        end_date: endDate,
        status: 'open',
      });
      toast.success('Fiscal period created successfully');
      setCreateDialogOpen(false);
      resetForm();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create fiscal period');
    }
  };

  const handleBulkCreate = async () => {
    if (!selectedCompanyId) return;

    try {
      await bulkCreateMutation.mutateAsync({
        companyId: selectedCompanyId,
        year: bulkYear,
      });
      toast.success(`Created 12 monthly periods for ${bulkYear}`);
      setBulkCreateDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create monthly periods');
    }
  };

  const handleClose = async (period: FiscalPeriod) => {
    if (!user?.id) return;

    try {
      await closeMutation.mutateAsync({
        periodId: period.id!,
        userId: user.id,
      });
      toast.success(`Period ${period.period_number} closed successfully`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to close fiscal period');
    }
  };

  const resetForm = () => {
    setPeriodNumber('');
    setPeriodType('month');
    setStartDate('');
    setEndDate('');
  };

  const getStatusBadge = (status: PeriodStatus) => {
    switch (status) {
      case 'open':
        return <WaxSealBadge type="unlocked" size="sm" />;
      case 'closed':
        return <WaxSealBadge type="pending" size="sm" />;
      case 'locked':
        return <WaxSealBadge type="locked" size="sm" />;
      default:
        return <WaxSealBadge type="pending" size="sm" />;
    }
  };

  const getTypeDisplay = (type: PeriodType) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };
  const isActiveCompany = selectedCompany?.onboarding_status === 'ACTIVE' || selectedCompany?.is_active;

  // Empty state when no company is selected
  if (!selectedCompanyId) {
    return (
      <div className="p-10 space-y-8">
        <PageHeader
          title="Chronicle of Time"
          subtitle="Guard the sacred boundaries of accounting cycles"
          icon={Hourglass}
        />
        <AtheneumCard>
          <AtheneumCardContent>
            <div className="flex flex-col items-center justify-center space-y-4 text-center py-16">
              <Hourglass className="h-16 w-16 text-muted-foreground opacity-50" />
              <div>
                <h3 className="font-semibold text-lg mb-2">No Company Selected</h3>
                <p className="text-muted-foreground">
                  Please select a company from the dropdown above to manage fiscal periods.
                </p>
              </div>
            </div>
          </AtheneumCardContent>
        </AtheneumCard>
      </div>
    );
  }

  return (
    <div className="p-10 space-y-8">
      {/* Header - Using Athenaeum PageHeader */}
      <PageHeader
        title="Chronicle of Time"
        subtitle="Guard the sacred boundaries of accounting cycles"
        icon={Hourglass}
        actions={
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setBulkCreateDialogOpen(true)}
              className="shadow-gold"
            >
              <Calendar className="mr-2 h-4 w-4" />
              Create Monthly Periods
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} className="shadow-gold">
              <Plus className="mr-2 h-4 w-4" />
              New Period
            </Button>
          </div>
        }
      />

      {/* Info Alert */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>About Fiscal Periods</AlertTitle>
          <AlertDescription>
            Fiscal periods define the time ranges for accounting transactions. Journal entries must
            belong to an open period. Closing a period prevents new entries from being posted to it.
          </AlertDescription>
        </Alert>
        {isActiveCompany && (
          <p className="text-sm text-muted-foreground mt-2 pl-6">
            Closed periods cannot be reopened.
          </p>
        )}
      </motion.div>

      {/* Filters - Using Athenaeum Card */}
      <AtheneumCard hover>
        <AtheneumCardHeader icon={<Calendar className="w-5 h-5" />}>
          Filters
        </AtheneumCardHeader>
        <AtheneumCardContent>
          <div className="flex items-center gap-4">
            <div className="w-48">
              <Label htmlFor="filter-year">Year</Label>
              <Select value={filterYear} onValueChange={setFilterYear}>
                <SelectTrigger id="filter-year">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Years</SelectItem>
                  {availableYears.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Periods Table - Using Athenaeum Card */}
      <AtheneumCard glow>
        <AtheneumCardHeader icon={<Hourglass className="w-5 h-5" />} embossed>
          Fiscal Periods
          <span className="text-sm font-normal text-muted-foreground ml-3">
            {fiscalPeriods.length} {fiscalPeriods.length === 1 ? 'period' : 'periods'}
          </span>
        </AtheneumCardHeader>
        <AtheneumCardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Hourglass className="h-12 w-12 mx-auto mb-4 opacity-50 animate-pulse-glow" />
              <p>Loading fiscal periods...</p>
            </div>
          ) : fiscalPeriods.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No fiscal periods found</p>
              <p className="text-sm">Create your first period to start recording journal entries</p>
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Period Number</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead>End Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fiscalPeriods.map((period: FiscalPeriod) => (
                    <TableRow key={period.id}>
                      <TableCell className="font-medium">{period.period_number}</TableCell>
                      <TableCell>{getTypeDisplay(period.period_type)}</TableCell>
                      <TableCell>{new Date(period.start_date).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(period.end_date).toLocaleDateString()}</TableCell>
                      <TableCell>{getStatusBadge(period.status)}</TableCell>
                      <TableCell className="text-right">
                        {period.status === 'open' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleClose(period)}
                            disabled={closeMutation.isPending}
                          >
                            <Lock className="mr-1 h-3 w-3" />
                            Close
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </AtheneumCardContent>
      </AtheneumCard>

      {/* Create Period Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Fiscal Period</DialogTitle>
            <DialogDescription>
              Define a new accounting period for recording journal entries
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="period-number">Period Number *</Label>
              <Input
                id="period-number"
                placeholder="e.g., 2024-01, Q1-2024"
                value={periodNumber}
                onChange={(e) => setPeriodNumber(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="period-type">Period Type</Label>
              <Select value={periodType} onValueChange={(value: PeriodType) => setPeriodType(value)}>
                <SelectTrigger id="period-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="quarter">Quarter</SelectItem>
                  <SelectItem value="year">Year</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-date">Start Date *</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-date">End Date *</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Period'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Bulk Create Monthly Periods Dialog */}
      <Dialog open={bulkCreateDialogOpen} onOpenChange={setBulkCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Monthly Periods</DialogTitle>
            <DialogDescription>
              Automatically create all 12 monthly periods for a year
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="bulk-year">Year</Label>
              <Input
                id="bulk-year"
                type="number"
                min="2000"
                max="2100"
                value={bulkYear}
                onChange={(e) => setBulkYear(parseInt(e.target.value))}
              />
            </div>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This will create 12 monthly periods ({bulkYear}-01 through {bulkYear}-12) with
                standard calendar dates. All periods will be created with "open" status.
              </AlertDescription>
            </Alert>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setBulkCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleBulkCreate} disabled={bulkCreateMutation.isPending}>
              {bulkCreateMutation.isPending ? 'Creating...' : 'Create 12 Periods'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FiscalPeriodsPage;
