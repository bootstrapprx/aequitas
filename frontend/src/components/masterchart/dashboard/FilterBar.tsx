// frontend/src/components/masterchart/dashboard/FilterBar.tsx
import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Search, X } from 'lucide-react';
import { FilterState } from '@/types/masterchart';

interface FilterBarProps {
    filters: FilterState;
    onFiltersChange: (filters: FilterState) => void;
    categories: string[];
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onFiltersChange, categories }) => {
    const handleReset = () => {
        onFiltersChange({
            search: '',
            category: 'all',
            type: 'all',
            normalBalance: 'all',
            tags: [],
        });
    };

    return (
        <div className="flex flex-wrap items-center gap-4 rounded-xl border px-4 py-3 bg-card">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder="Search accounts..."
                    value={filters.search}
                    onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
                    className="pl-9"
                />
            </div>

            {/* Category Filter */}
            <Select
                value={filters.category}
                onValueChange={(value) => onFiltersChange({ ...filters, category: value })}
            >
                <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {categories.map((cat) => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                </SelectContent>
            </Select>

            {/* Type Filter */}
            <Select
                value={filters.type}
                onValueChange={(value) => onFiltersChange({ ...filters, type: value as FilterState['type'] })}
            >
                <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="H">Header</SelectItem>
                    <SelectItem value="D">Detail</SelectItem>
                </SelectContent>
            </Select>

            {/* Normal Balance Filter */}
            <Select
                value={filters.normalBalance}
                onValueChange={(value) => onFiltersChange({ ...filters, normalBalance: value as FilterState['normalBalance'] })}
            >
                <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Balance" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Balances</SelectItem>
                    <SelectItem value="Debit">Debit</SelectItem>
                    <SelectItem value="Credit">Credit</SelectItem>
                </SelectContent>
            </Select>

            {/* Reset Button */}
            <Button variant="outline" size="sm" onClick={handleReset}>
                <X className="h-4 w-4 mr-2" />
                Reset
            </Button>
        </div>
    );
};

export default FilterBar;
