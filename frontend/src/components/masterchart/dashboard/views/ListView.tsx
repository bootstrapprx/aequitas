// frontend/src/components/masterchart/dashboard/views/ListView.tsx
import React, { useMemo, useState } from 'react';
import { MasterAccount } from '@/types/masterchart';
import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    getSortedRowModel,
    getPaginationRowModel,
    SortingState,
    useReactTable,
} from '@tanstack/react-table';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';

interface ListViewProps {
    accounts: MasterAccount[];
    onSelectAccount: (account: MasterAccount) => void;
}

const ListView: React.FC<ListViewProps> = ({ accounts, onSelectAccount }) => {
    const [sorting, setSorting] = useState<SortingState>([]);
    const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 20 });

    const columns = useMemo<ColumnDef<MasterAccount>[]>(
        () => [
            {
                accessorKey: 'code',
                header: ({ column }) => (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                        className="hover:bg-transparent"
                    >
                        Code
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                ),
                cell: ({ row }) => (
                    <span className="font-mono font-medium">{row.getValue('code')}</span>
                ),
            },
            {
                accessorKey: 'description',
                header: ({ column }) => (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                        className="hover:bg-transparent"
                    >
                        Name
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                ),
            },
            {
                accessorKey: 'type',
                header: 'Type',
                cell: ({ row }) => (
                    <Badge variant={row.getValue('type') === 'H' ? 'default' : 'secondary'}>
                        {row.getValue('type') === 'H' ? 'Header' : 'Detail'}
                    </Badge>
                ),
            },
            {
                accessorKey: 'category',
                header: ({ column }) => (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                        className="hover:bg-transparent"
                    >
                        Category
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                ),
            },
            {
                accessorKey: 'level',
                header: ({ column }) => (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                        className="hover:bg-transparent"
                    >
                        Level
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                ),
                cell: ({ row }) => <div className="text-center">{row.getValue('level')}</div>,
            },
            {
                id: 'actions',
                cell: ({ row }) => (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onSelectAccount(row.original)}
                    >
                        Details
                    </Button>
                ),
            },
        ],
        [onSelectAccount]
    );

    const table = useReactTable({
        data: accounts,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        onSortingChange: setSorting,
        onPaginationChange: setPagination,
        state: {
            sorting,
            pagination,
        },
    });

    return (
        <div className="space-y-4">
            <div className="rounded-xl border bg-card">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => (
                                    <TableHead key={header.id}>
                                        {header.isPlaceholder
                                            ? null
                                            : flexRender(
                                                header.column.columnDef.header,
                                                header.getContext()
                                            )}
                                    </TableHead>
                                ))}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow key={row.id} className="hover:bg-accent/50">
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={columns.length} className="h-24 text-center">
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                    Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
                    {Math.min(
                        (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                        accounts.length
                    )}{' '}
                    of {accounts.length} accounts
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        Next
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ListView;
